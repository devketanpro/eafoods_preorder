from datetime import datetime, time, timedelta

from django.utils import timezone

from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError, PermissionDenied, NotAuthenticated

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

from drf_spectacular.utils import extend_schema, OpenApiParameter

from .permissions import IsOpsManager, IsCustomer
from .models import Product, StockBalance, PreOrder, DeliverySlot
from .serializers import (
    ProductSerializer,
    StockBalanceSerializer,
    PreOrderSerializer,
    DeliverySlotSerializer,
    SignupSerializer,
)


class SignupView(generics.CreateAPIView):
    """
    Public signup endpoint.
    Customers register here.
    """
    serializer_class = SignupSerializer
    permission_classes = [AllowAny]


class LoginView(TokenObtainPairView):
    """Login returns access + refresh tokens."""
    permission_classes = [AllowAny]


class LogoutView(APIView):
    """Logout blacklists refresh token."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Logout successful"})
        except Exception:
            return Response({"error": "Invalid refresh token"}, status=400)
        
 

class OpsManagerCreateView(generics.CreateAPIView):
    """
    API endpoint to create an Ops Manager; accessible only to authenticated admin users.
    Returns 401 for unauthenticated users and 403 for non-admins.
    """

    serializer_class = SignupSerializer
    permission_classes = [IsAdminUser]

    def permission_denied(self, request, message=None, code=None):
        if not request.user.is_authenticated:
            raise NotAuthenticated("You must be logged in as an admin to create an Ops Manager.")
        raise PermissionDenied("Only admin users can create an Ops Manager.")

    def perform_create(self, serializer):
        serializer.save(role="ops_manager")



class ProductListView(generics.ListAPIView):
    """
    Public endpoint: List all products.
    Permissions:
    - AllowAny (anyone can view products, no login required).
    """

    permission_classes = [AllowAny]
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class DeliverySlotListView(generics.ListAPIView):
    """
    Public endpoint: List all available delivery slots.
    Permissions:
    - AllowAny (anyone can view slots, no login required).
    """
    permission_classes = [AllowAny]
    queryset = DeliverySlot.objects.all()
    serializer_class = DeliverySlotSerializer


class StockUpdateView(generics.UpdateAPIView):
    """
    Ops Manager endpoint to update product stock.

    - Permissions: Only accessible by users with role 'ops_manager'.
    - Updates StockBalance quantity for products.
    - Intended for morning (8-9AM) and evening (6-7PM) updates.
    - Changes immediately affect pre-order availability.
    """

    permission_classes = [IsOpsManager]
    queryset = StockBalance.objects.all()
    serializer_class = StockBalanceSerializer

    def perform_update(self, serializer):
        now = timezone.localtime()
        if not (time(8,0) <= now.time() <= time(12,0) or time(18,0) <= now.time() <= time(19,0)):
            raise ValidationError(
            "Stock can only be updated during allowed slots: "
            "Morning (8AM–12PM) or Evening (6PM–7PM)."
            )
        serializer.save()


class PreOrderCreateView(generics.CreateAPIView):
    """
    Create a new pre-order for customers.

    - Requires authentication (IsCustomer).
    - Checks stock availability and applies 6PM cutoff rule 
      (orders after 6PM delivered in +2 days).
    - Product can be selected by `product_name`.
      * If exact match, order it.
      * If similar products exist, return suggestions.
      * If none, return proper message.
    """

    permission_classes = [IsCustomer]
    queryset = PreOrder.objects.all()
    serializer_class = PreOrderSerializer

    def create(self, request, *args, **kwargs):
        now = timezone.localtime()
        if not request.user.is_authenticated:
            return Response({"error": "Authentication required"}, status=401)
        user = request.user

        # --- Product ---
        product_name = request.data.get("product_name", "").strip()
        if not product_name:
            return Response({"error": "Provide product_name"}, status=400)

        product = Product.objects.filter(name__iexact=product_name).first()
        if not product:
            suggestions = Product.objects.filter(name__icontains=product_name)
            if not suggestions.exists():
                return Response(
                    {"error": f"No products found for '{product_name}'", "suggestions": []},
                    status=404
                )
            return Response(
                {
                    "error": f"No exact match for '{product_name}'",
                    "suggestions": list(suggestions.values("id", "name"))
                },
                status=300
            )

        # --- Quantity ---
        try:
            qty = int(request.data.get("quantity", 0))
            if qty <= 0:
                return Response({"error": "Quantity must be greater than zero."}, status=400)
        except (ValueError, TypeError):
            return Response({"error": "Quantity must be a valid number."}, status=400)

        # --- Slot ---
        slot_input = request.data.get("slot", "").strip().upper()
        try:
            slot = DeliverySlot.objects.get(name=slot_input)
        except DeliverySlot.DoesNotExist:
            valid_slots = [choice[0] for choice in DeliverySlot.SLOT_CHOICES]
            return Response(
                {"error": f"Invalid slot. Choose one of: {', '.join(valid_slots)}"},
                status=400
            )

        # --- Delivery Address ---
        address = request.data.get("delivery_address", "").strip()

        if not address:
            return Response({"error": "Delivery address cannot be empty."}, status=400)

        # Must contain at least one letter
        if not any(c.isalpha() for c in address):
            return Response({"error": "Delivery address must contain at least one letter."}, status=400)

        # Optional: allow letters, numbers, spaces, commas, periods, hyphens
        if not all(c.isalnum() or c.isspace() or c in ",.-" for c in address):
            return Response(
                {"error": "Delivery address can only contain letters, numbers, spaces, and ,.-"},
                status=400
            )

        # --- Stock Check ---
        try:
            stock = StockBalance.objects.get(product=product)
        except StockBalance.DoesNotExist:
            return Response({"error": "Stock not found"}, status=404)

        if stock.quantity < qty:
            return Response(
                {"error": f"Insufficient stock for {product.name}. Available: {stock.quantity}"},
                status=400
            )

        # --- Cutoff Logic ---
        cutoff = time(18, 0)
        delivery_date = now.date() + timedelta(days=1)
        if now.time() >= cutoff:
            delivery_date += timedelta(days=1)

        # --- Create PreOrder ---
        preorder = PreOrder.objects.create(
            user=user,
            product=product,
            slot=slot,  # pass the actual object, not the string
            quantity=qty,
            delivery_date=delivery_date,
            delivery_address=address
        )

        # Deduct stock
        stock.quantity -= qty
        stock.save()

        return Response(
            PreOrderSerializer(preorder, context={"request": request}).data,
            status=201
        )


class CancelOrderView(APIView):
    """
    Customer-only endpoint: Cancel an existing pre-order.
    Enforces:
    - Only the user who placed the order can cancel it.
    - Restores stock balance after cancellation.
    Permissions:
    - IsCustomer (only authenticated customers can cancel their orders).
    """

    permission_classes = [IsCustomer]

    def post(self, request, pk):
        try:
            preorder = PreOrder.objects.get(pk=pk, user=request.user)  
        except PreOrder.DoesNotExist:
            return Response(
                {"error": "Order not found or not authorized"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if preorder.is_cancelled:
            return Response(
                {"error": "Order already cancelled"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        preorder.is_cancelled = True
        preorder.save()

        stock = StockBalance.objects.get(product=preorder.product)
        stock.quantity += preorder.quantity
        stock.save()

        return Response({"message": "Order cancelled"}, status=status.HTTP_200_OK)


@extend_schema(
        parameters=[
            OpenApiParameter(
                name="slot",
                description="Delivery slot (MORNING, AFTERNOON, EVENING)",
                required=True,
                type=str,
            )
        ]
    )
class OrderListBySlotView(generics.ListAPIView):
    """
    Restricted endpoint: List all orders grouped by delivery slot for fulfillment.
    Permissions:
    - IsOpsManager (only authenticated Ops Managers can view orders by slot).
    """

    permission_classes = [IsOpsManager]
    serializer_class = PreOrderSerializer

    def get_queryset(self):
        # Return all orders as fallback; filtering is done in list()
        return PreOrder.objects.all()

    def list(self, request, *args, **kwargs):
        slot_input = request.query_params.get("slot")
        if not slot_input:
            return Response(
                {"error": "Slot parameter is required."},
                status=400
            )

        slot_input = slot_input.strip().upper()
        try:
            slot = DeliverySlot.objects.get(name=slot_input)
        except DeliverySlot.DoesNotExist:
            valid_slots = [choice[0] for choice in DeliverySlot.SLOT_CHOICES]
            return Response(
                {"error": f"Invalid slot. Choose one of: {', '.join(valid_slots)}"},
                status=400
            )

        queryset = PreOrder.objects.filter(slot=slot, is_cancelled=False)
        if not queryset.exists():
            return Response(
                {"message": f"No orders found for {slot.name} slot."},
                status=200
            )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class TopProductsReportView(APIView):
    """
    Restricted reporting endpoint: Show top products ordered within a date range.
    Permissions:
    - IsOpsManager (only authenticated Ops Managers can access sales reports).
    """

    permission_classes = [IsOpsManager]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="start",
                description="Start date (YYYY-MM-DD)",
                required=True,
                type=str,
            ),
            OpenApiParameter(
                name="end",
                description="End date (YYYY-MM-DD)",
                required=True,
                type=str,
            ),
        ]
    )
    def get(self, request):
        start = request.query_params.get("start")
        end = request.query_params.get("end")

        try:
            start_date = datetime.strptime(start, "%Y-%m-%d").date()
            end_date = datetime.strptime(end, "%Y-%m-%d").date()
        except (TypeError, ValueError):
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD"}, status=400
            )

        #  Auto-swap if start is after end
        if start_date > end_date:
            start_date, end_date = end_date, start_date

            qs = (
            PreOrder.objects.filter(
                delivery_date__range=[start_date, end_date],
                is_cancelled=False,
            )
            .select_related("product", "user")
            .values(
                "id",
                "user__username",
                "product__name",
                "quantity",
                "created_at",
                "delivery_date",
            )
            .order_by("-quantity")
        )

        return Response(qs, status=status.HTTP_200_OK)
