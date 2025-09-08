"""
Serializers for the Preorder app.

This module handles validation and transformation of model instances
into JSON representations for the API. It also enforces critical
business rules such as:
- Stock-driven orders (cannot exceed available stock).
- Daily cut-off time (orders placed after 6:00 PM are scheduled +2 days).
- Cancelling an order restores stock.

All validations follow the EA Foods Pre-Order assignment requirements.
"""

from datetime import datetime, time, timedelta
from django.utils import timezone
from rest_framework import serializers
from .models import Product, StockBalance, PreOrder, DeliverySlot
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
User = get_user_model()

class SignupSerializer(serializers.ModelSerializer):
    """
    Handles user signup.
    Default role = customer (unless explicitly set by admin).
    """
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "password", "role"]

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("User already exists, please login.")
        return value

    def create(self, validated_data):
        role = validated_data.get("role", "customer")
        user = User(username=validated_data["username"], role=role)
        user.set_password(validated_data["password"])
        user.save()
        return user

    def to_representation(self, instance):
        """Return JWT tokens after signup."""
        refresh = RefreshToken.for_user(instance)
        return {
            "message": "Signup successful",
            "username": instance.username,
            "role": instance.role,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }


class ProductSerializer(serializers.ModelSerializer):
    """
    Serializer for Product model.
    Provides ID, name, and description.
    """

    class Meta:
        model = Product
        fields = ["id", "name", "description"]


class StockBalanceSerializer(serializers.ModelSerializer):
    """
    Serializer for StockBalance model.
    Includes nested product details for readability.
    """

    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        write_only=True,
        source="product",
        help_text="ID of the product this stock belongs to",
    )

    class Meta:
        model = StockBalance
        fields = ["id", "product", "product_id", "quantity", "updated_at"]


class DeliverySlotSerializer(serializers.ModelSerializer):
    """
    Serializer for DeliverySlot model.
    Ensures slot choices are enforced.
    """

    class Meta:
        model = DeliverySlot
        fields = ["id", "name"]


class PreOrderSerializer(serializers.ModelSerializer):
    """
    Serializer for PreOrder model.
    Handles validation of:
    - Stock availability
    - Cut-off time (6:00 PM daily)
    - Quantity positivity
    """

    product_name = serializers.CharField(write_only=True)  # just take input name
    product = serializers.CharField(source='product.name', read_only=True)

    slot = serializers.ChoiceField(choices=DeliverySlot.SLOT_CHOICES, write_only=True)
    slot_name = serializers.CharField(source='slot.name', read_only=True)

    user_name = serializers.CharField(source='user.username', read_only=True)
    delivery_date = serializers.DateField(read_only=True)

    delivery_address = serializers.CharField(write_only=True, required=True)
    delivery_address_output = serializers.CharField(source='delivery_address', read_only=True)

    class Meta:
        model = PreOrder
        fields = [
            "product_name", 
            "quantity",
            "slot",          
            "delivery_address",
            "id",       
            "slot_name",    
            "delivery_date",
            "user_name",
            "product",
            "delivery_address_output",
        ]


    def validate_quantity(self, value):
        """Ensure quantity is a positive number."""
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value

    def validate(self, data):
        """
        Custom validation for pre-orders:
        - Ensure stock is available.
        - Enforce cut-off rule.
        """
        product = data.get("product")
        quantity = data.get("quantity")

        # --- Stock Validation ---
        try:
            stock = product.stock
        except StockBalance.DoesNotExist:
            raise serializers.ValidationError(f"No stock record found for {product.name}.")

        if stock.quantity < quantity:
            raise serializers.ValidationError(
                f"Insufficient stock for {product.name}. Available: {stock.quantity}"
            )

        # --- Cut-off Validation ---
        now = timezone.localtime()
        cutoff = time(18, 0)  # 6:00 PM
        delivery_date = data.get("delivery_date")

        if delivery_date is None:
            # If delivery_date not provided, assign based on cut-off
            if now.time() >= cutoff:
                data["delivery_date"] = (now + timedelta(days=2)).date()
            else:
                data["delivery_date"] = (now + timedelta(days=1)).date()
        else:
            # Enforce cut-off even if delivery_date is given
            if now.time() >= cutoff and delivery_date == (now + timedelta(days=1)).date():
                raise serializers.ValidationError(
                    "Orders placed after 6PM cannot be scheduled for next day. Choose +2 days."
                )

        return data

    def create(self, validated_data):
        """
        On creation:
        - Deduct stock
        - Save order
        """
        product = validated_data["product"]
        quantity = validated_data["quantity"]
        validated_data['user'] = self.context['request'].user


        stock = product.stock
        stock.quantity -= quantity
        stock.save()

        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        On cancellation:
        - Restore stock
        """
        is_cancelled = validated_data.get("is_cancelled", instance.is_cancelled)

        if is_cancelled and not instance.is_cancelled:
            # restore stock only when changing from active → cancelled
            stock = instance.product.stock
            stock.quantity += instance.quantity
            stock.save()

        return super().update(instance, validated_data)
