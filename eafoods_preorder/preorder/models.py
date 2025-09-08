from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings


class CustomUser(AbstractUser):
    """
    Custom user extending Django's AbstractUser.
    Uses a role field instead of multiple booleans
    to make the model scalable if more roles are added.
    """

    ROLE_CHOICES = [
        ("customer", "Customer"),
        ("ops_manager", "Ops Manager"),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="customer",
        help_text="Defines the role of the user in the system.",
    )

    # Fix reverse accessor clashes with default auth.User
    groups = models.ManyToManyField(
        "auth.Group",
        related_name="customuser_groups",  # unique related_name
        blank=True,
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        related_name="customuser_permissions",  # unique related_name
        blank=True,
    )

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def is_ops_manager(self) -> bool:
        """Helper method: check if user is an Ops Manager."""
        return self.role == "ops_manager"

    def is_customer(self) -> bool:
        """Helper method: check if user is a Customer."""
        return self.role == "customer"


class Product(models.Model):
    """
    Represents a product available for pre-order.
    """

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class StockBalance(models.Model):
    """
    Maintains stock levels of products updated by Ops managers.
    """

    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="stock")
    quantity = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product.name}: {self.quantity}"


class DeliverySlot(models.Model):
    """
    Delivery slots available for pre-orders.
    """

    SLOT_CHOICES = [
        ("MORNING", "8AM - 11AM"),
        ("AFTERNOON", "12PM - 3PM"),
        ("EVENING", "4PM - 7PM"),
    ]

    name = models.CharField(max_length=20, choices=SLOT_CHOICES, unique=True)

    def __str__(self):
        return self.get_name_display()


class PreOrder(models.Model):
    """
    Represents a customer pre-order.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name="preorders",
        help_text="User who placed the pre-order"
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    slot = models.ForeignKey(DeliverySlot, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    delivery_date = models.DateField()
    delivery_address = models.TextField()
    is_cancelled = models.BooleanField(default=False)

    def __str__(self):
        return f"Order {self.id} by {self.user.username} - {self.product.name} x {self.quantity}"
