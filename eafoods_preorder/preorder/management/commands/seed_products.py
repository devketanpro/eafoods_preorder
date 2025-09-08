"""
Custom Django management command to seed initial data.

This command populates:
- Products (with descriptions)
- Stock balances (default quantities)
- Delivery slots (Morning, Afternoon, Evening)

Usage:
    python manage.py seed_products

This is useful for:
- Initial setup of the application
- Demo/testing environments
- Ensuring Ops managers always have baseline data

Following assignment requirements:
- At least 5–10 products must exist in local DB/mocks.
- Stock balances should be updated twice daily (Ops will later update).
- Delivery slots must exist for customers to choose from.
"""

from django.core.management.base import BaseCommand
from preorder.models import Product, StockBalance, DeliverySlot


class Command(BaseCommand):
    help = "Seeds the database with sample products, stock balances, and delivery slots."

    def handle(self, *args, **options):
        # --- Seed Products ---
        products_data = [
            {"name": "Apple", "description": "Fresh red apples"},
            {"name": "Banana", "description": "Organic ripe bananas"},
            {"name": "Carrot", "description": "Crunchy orange carrots"},
            {"name": "Tomato", "description": "Juicy farm tomatoes"},
            {"name": "Milk", "description": "1L organic cow milk"},
            {"name": "Bread", "description": "Whole wheat bread loaf"},
            {"name": "Eggs", "description": "Pack of 12 free-range eggs"},
        ]

        for p in products_data:
            product, created = Product.objects.get_or_create(
                name=p["name"], defaults={"description": p["description"]}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f" Created product: {product.name}"))
            else:
                self.stdout.write(self.style.WARNING(f" Product already exists: {product.name}"))

            # Ensure stock exists for each product
            stock, stock_created = StockBalance.objects.get_or_create(
                product=product, defaults={"quantity": 50}  # default 50 items in stock
            )
            if stock_created:
                self.stdout.write(self.style.SUCCESS(f"   Added stock for {product.name}: {stock.quantity}"))
            else:
                self.stdout.write(self.style.WARNING(f"   Stock already exists for {product.name}"))

        # --- Seed Delivery Slots ---
        slots_data = [
            ("MORNING", "8AM - 11AM"),
            ("AFTERNOON", "12PM - 3PM"),
            ("EVENING", "4PM - 7PM"),
        ]

        for key, label in slots_data:
            slot, created = DeliverySlot.objects.get_or_create(name=key)
            if created:
                self.stdout.write(self.style.SUCCESS(f" Created slot: {label}"))
            else:
                self.stdout.write(self.style.WARNING(f" Slot already exists: {label}"))

        self.stdout.write(self.style.SUCCESS("Seeding completed successfully!"))
