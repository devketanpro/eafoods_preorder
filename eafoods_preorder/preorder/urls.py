from django.urls import path
from .views import (
    StockUpdateView,
    PreOrderCreateView,
    CancelOrderView,
    OrderListBySlotView,
    TopProductsReportView,
    SignupView,
    LoginView,
    LogoutView,
    OpsManagerCreateView,
    ProductListView,
)
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    # User signup endpoint
    path("signup/", SignupView.as_view(), name="signup"),

    # User login endpoint (returns JWT tokens)
    path("login/", LoginView.as_view(), name="login"),

    # Refresh JWT access token
    path("refresh/", TokenRefreshView.as_view(), name="token-refresh"),

    # User logout endpoint
    path("logout/", LogoutView.as_view(), name="logout"),

    # Create a new Ops Manager (admin only)
    path("create-ops-manager/", OpsManagerCreateView.as_view(), name="create-ops-manager"),

    # Update stock quantity for a specific product by ID
    path("stock/<int:pk>/", StockUpdateView.as_view(), name="stock-update"),

    # Create a new preorder for customers
    path("preorder/", PreOrderCreateView.as_view(), name="preorder-create"),

    # Cancel an existing preorder by ID
    path("cancel/<int:pk>/", CancelOrderView.as_view(), name="cancel-order"),

    # List orders grouped by delivery slot
    path("orders/", OrderListBySlotView.as_view(), name="orders-by-slot"),

    # Get top-selling products report
    path("report/top-products/", TopProductsReportView.as_view(), name="top-products"),

    # List all products
    path("products/", ProductListView.as_view(), name="product-list"),

    # Get details of a specific product by ID
    path("products/<int:pk>/", ProductListView.as_view(), name="product-detail"),
]

