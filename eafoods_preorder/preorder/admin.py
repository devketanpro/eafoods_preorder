"""
Admin configuration for the Preorder app.
"""

from django.contrib import admin
from .models import Product, StockBalance, DeliverySlot, PreOrder


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Admin view for managing Products.

    Features:
    - Display product ID, name, and description in list view.
    - Searchable by product name.
    """

    list_display = ("id", "name", "description")
    search_fields = ("name",)


@admin.register(StockBalance)
class StockBalanceAdmin(admin.ModelAdmin):
    """
    Admin view for managing StockBalance.

    Features:
    - Shows stock levels per product.
    - Filterable by last updated time.
    - Editable quantity field directly from detail view.

    Used by Ops managers to update stock twice daily (8AM, 6PM).
    """

    list_display = ("id", "product", "quantity", "updated_at")
    list_filter = ("updated_at",)


@admin.register(DeliverySlot)
class DeliverySlotAdmin(admin.ModelAdmin):
    """
    Admin view for managing Delivery Slots.

    Features:
    - Shows available slots (Morning, Afternoon, Evening).
    - Filter by slot type.
    """

    list_display = ("id", "name")
    list_filter = ("name",)


@admin.register(PreOrder)
class PreOrderAdmin(admin.ModelAdmin):
    """
    Admin view for managing PreOrders.

    Features:
    - Shows order details (product, slot, quantity, delivery date, status).
    - Filter by slot, delivery date, cancelled status.
    - Searchable by product name.
    - Helps Ops managers view and fulfill pre-orders grouped by slots.

    Notes:
    - Cancelling an order should restore stock (handled in business logic).
    """

    list_display = (
        "id",
        "product",
        "slot",
        "quantity",
        "delivery_date",
        "is_cancelled",
        "created_at",
        "user",
        "delivery_address",
    )
    list_filter = ("slot", "delivery_date", "is_cancelled", "created_at")
    search_fields = ("product__name",)
