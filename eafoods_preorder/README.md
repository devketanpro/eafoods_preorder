# EA Foods Preorder System

This project is a Django-based backend for managing products, preorders, stock updates, and reports. It is designed with REST APIs using Django REST Framework (DRF) and is fully documented with Swagger UI.

---

## Features

* JWT-based authentication for customers, admins, and ops managers.
* Create, update, and cancel preorders.
* Update stock with time restrictions.
* List orders by delivery slots.
* Top-selling product reports.
* Fully documented API using DRF Spectacular (Swagger & Redoc).

---

## Project Structure

```text
eafoods_preorder/       # Django project folder
├── settings.py         # Project settings
├── urls.py             # Project URLs
preorder/               # Main app
├── models.py           # Database models
├── views.py            # API views
├── serializers.py      # Serializers
├── urls.py             # App URLs
├── management/commands/seed_products.py  # Seed initial products
├── tests/              # Test cases
```

---

## Setup Instructions (Local Development)

1. **Clone the repository**

```bash
git clone https://github.com/devketanpro/eafoods_preorder.git
cd eafoods_preorder
```

2. **Create and activate a virtual environment**

```bash
python -m venv venv
source venv/bin/activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Set environment variables**

```bash
export DJANGO_SETTINGS_MODULE=eafoods_preorder.settings
```

5. **Run migrations**

```bash
python manage.py makemigrations
python manage.py migrate
```

6. **Seed initial products**

```bash
python manage.py seed_products
```

7. **Create a superuser**

```bash
python manage.py createsuperuser
```

8. **Start the development server**

```bash
python manage.py runserver
```

Server will be available at `http://127.0.0.1:8000/`

---

## API Documentation

Swagger UI and Redoc are included:

* Swagger: `http://127.0.0.1:8000/api/docs/`
* Redoc: `http://127.0.0.1:8000/api/redoc/`
* API Schema JSON: `http://127.0.0.1:8000/api/schema/`

Use these endpoints to explore all API routes, request/response formats, and authentication requirements.

---

## Docker Usage

This project is fully Dockerized. The Docker Compose setup ensures all migrations are applied automatically and the server runs inside the container.

### Steps to run:

1. **Build the Docker container**

```bash
cd eafoods_preorder
sudo docker compose build
```

2. **Start the container**

```bash
sudo docker compose up -d
```

3. **Enter the running container**

```bash
sudo docker compose exec web bash
```

4. **Apply migrations inside the container**

```bash
python manage.py migrate
```

5. **Seed initial products inside the container**

```bash
python manage.py seed_products
```

6. **Create a superuser inside the container**

```bash
python manage.py createsuperuser
```

7. **Access the server**

```
http://localhost:8000
```

8. **Access Swagger UI for API documentation**

```
http://localhost:8000/api/docs/
```

---

## Running Tests

This project includes unit and integration tests.

```bash
pytest preorder/tests/
```

---


## Notes

* Make sure to use Python >=3.10.
* Docker ensures consistent environment for all developers.
* JWT authentication required for all protected endpoints.
* Seed products command must be run once after migrations to populate initial product data.
