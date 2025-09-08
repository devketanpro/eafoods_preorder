import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from datetime import time, timedelta
from django.contrib.auth import get_user_model

from ..models import CustomUser, Product, StockBalance, DeliverySlot, PreOrder

@pytest.fixture
def api_client():
    return APIClient()

User = get_user_model()

@pytest.fixture
def create_users(db):
    admin = User.objects.create_user(username="admin", password="admin123", role="admin")
    customer = User.objects.create_user(username="cust", password="cust123", role="customer")
    ops = User.objects.create_user(username="ops", password="ops123", role="ops_manager")
    return {"admin": admin, "customer": customer, "ops": ops}

@pytest.fixture
def create_products(db):
    p1 = Product.objects.create(name="Apple", description="Fresh Apple")
    p2 = Product.objects.create(name="Banana", description="Yellow Banana")
    StockBalance.objects.create(product=p1, quantity=10)
    StockBalance.objects.create(product=p2, quantity=5)
    return [p1, p2]

@pytest.fixture
def create_delivery_slots(db):
    morning = DeliverySlot.objects.create(name="MORNING")
    afternoon = DeliverySlot.objects.create(name="AFTERNOON")
    evening = DeliverySlot.objects.create(name="EVENING")
    return [morning, afternoon, evening]

# -----------------------
# Auth / Signup / Login
# -----------------------
@pytest.mark.django_db
def test_signup_customer(api_client):
    url = reverse("signup")
    data = {"username": "newuser", "password": "newpass123"}
    response = api_client.post(url, data)
    assert response.status_code == 201
    assert "access" in response.data and "refresh" in response.data
    
@pytest.mark.django_db
def test_login_customer(api_client, create_users):
    url = reverse("login")
    # Use the same credentials you set in fixture with create_user()
    data = {"username": "cust", "password": "cust123"}
    response = api_client.post(url, data)

    # Debugging helper (optional)
    # print(response.status_code, response.data)

    assert response.status_code == status.HTTP_200_OK
    assert "access" in response.data  # JWT token should be returned

# -----------------------
# Ops Manager Stock Update
# -----------------------
@pytest.mark.django_db
def test_update_stock_allowed_time(api_client, create_users, create_products, monkeypatch):
    ops_user = create_users["ops"]
    api_client.force_authenticate(user=ops_user)

    # Mock time to 8:30 AM
    monkeypatch.setattr("django.utils.timezone.localtime", lambda: timezone.datetime.combine(timezone.now().date(), time(8,30)))

    url = reverse("stock-update", args=[create_products[0].id])
    response = api_client.patch(url, {"quantity": 20})
    assert response.status_code == 200
    create_products[0].refresh_from_db()
    assert create_products[0].stock.quantity == 20

@pytest.mark.django_db
def test_update_stock_outside_allowed_time(api_client, create_users, create_products, monkeypatch):
    from django.utils import timezone
    from datetime import time

    ops_user = create_users["ops"]
    api_client.force_authenticate(user=ops_user)

    # Mock time to 2 PM (not allowed slot)
    monkeypatch.setattr(
        "django.utils.timezone.localtime",
        lambda: timezone.datetime.combine(timezone.now().date(), time(14, 0))
    )

    url = reverse("stock-update", args=[create_products[0].id])
    response = api_client.patch(url, {"quantity": 20})

    assert response.status_code == status.HTTP_400_BAD_REQUEST

    # Handle both list and dict responses
    if isinstance(response.data, list):
        assert any("Stock can only be updated" in msg for msg in response.data)
    else:
        errors = response.data.get("non_field_errors", []) or [response.data.get("detail", "")]
        assert any("Stock can only be updated" in msg for msg in errors)

# -----------------------
# PreOrder Creation
# -----------------------
@pytest.mark.django_db
def test_create_preorder_success(api_client, create_users, create_products, create_delivery_slots, monkeypatch):
    cust = create_users["customer"]
    api_client.force_authenticate(user=cust)

    # Mock time to 5 PM (before cut-off)
    monkeypatch.setattr("django.utils.timezone.localtime", lambda: timezone.datetime.combine(timezone.now().date(), time(17,0)))

    url = reverse("preorder-create")
    data = {
        "product_name": create_products[0].name,
        "quantity": 2,
        "slot": "MORNING",
        "delivery_address": "123 Street"
    }
    response = api_client.post(url, data)
    assert response.status_code == 201
    preorder = PreOrder.objects.get(id=response.data["id"])
    assert preorder.quantity == 2
    assert preorder.delivery_date == (timezone.localtime().date() + timedelta(days=1))

@pytest.mark.django_db
def test_create_preorder_after_cutoff(api_client, create_users, create_products, create_delivery_slots, monkeypatch):
    cust = create_users["customer"]
    api_client.force_authenticate(user=cust)

    # Mock time to 6:30 PM (after cut-off)
    monkeypatch.setattr("django.utils.timezone.localtime", lambda: timezone.datetime.combine(timezone.now().date(), time(18,30)))

    url = reverse("preorder-create")
    data = {
        "product_name": create_products[0].name,
        "quantity": 1,
        "slot": "MORNING",
        "delivery_address": "456 Street"
    }
    response = api_client.post(url, data)
    assert response.status_code == 201
    preorder = PreOrder.objects.get(id=response.data["id"])
    assert preorder.delivery_date == (timezone.localtime().date() + timedelta(days=2))

@pytest.mark.django_db
def test_create_preorder_insufficient_stock(api_client, create_users, create_products, create_delivery_slots):
    cust = create_users["customer"]
    api_client.force_authenticate(user=cust)

    url = reverse("preorder-create")
    data = {
        "product_name": create_products[1].name,
        "quantity": 100,  # exceed stock
        "slot": "AFTERNOON",
        "delivery_address": "789 Street"
    }
    response = api_client.post(url, data)
    assert response.status_code == 400
    assert "Insufficient stock" in response.data["error"]

# -----------------------
# Cancel Order
# -----------------------
@pytest.mark.django_db
def test_cancel_order(api_client, create_users, create_products, create_delivery_slots):
    cust = create_users["customer"]
    api_client.force_authenticate(user=cust)

    preorder = PreOrder.objects.create(
        user=cust,
        product=create_products[0],
        slot=create_delivery_slots[0],
        quantity=1,
        delivery_date=timezone.now().date(),
        delivery_address="123 Street"
    )

    url = reverse("cancel-order", args=[preorder.id])
    response = api_client.post(url)
    assert response.status_code == 200
    preorder.refresh_from_db()
    assert preorder.is_cancelled
    create_products[0].refresh_from_db()
    assert create_products[0].stock.quantity == 11  # stock restored

@pytest.mark.django_db
def test_cancel_order_twice(api_client, create_users, create_products, create_delivery_slots):
    cust = create_users["customer"]
    api_client.force_authenticate(user=cust)

    preorder = PreOrder.objects.create(
        user=cust,
        product=create_products[0],
        slot=create_delivery_slots[0],
        quantity=1,
        delivery_date=timezone.now().date(),
        delivery_address="123 Street",
        is_cancelled=True
    )

    url = reverse("cancel-order", args=[preorder.id])
    response = api_client.post(url)
    assert response.status_code == 400
    assert "already cancelled" in response.data["error"]
