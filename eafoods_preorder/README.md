# EA Foods Preorder System


A Django REST Framework (DRF) project for managing preorders, stock updates, and reporting of products. This project is fully Dockerized and uses **SQLite** as the database.

---

## Table of Contents

* [Features](#features)
* [Tech Stack](#tech-stack)
* [Project Structure](#project-structure)
* [Setup Instructions](#setup-instructions)
* [Docker Usage](#docker-usage)
* [API Documentation](#api-documentation)
* [Testing](#testing)
* [Notes](#notes)

---

## Features

* User signup, login, logout with JWT authentication
* Admin can create Ops Manager users
* Stock management with time-based restrictions
* Preorder creation and cancellation for customers
* List orders by delivery slot
* Top-selling products report
* REST API endpoints documented via Swagger and Redoc

---

## Tech Stack

* Python 3.10
* Django 5.x
* Django REST Framework
* SQLite (default database)
* Docker & Docker Compose
* drf-spectacular for API schema & documentation

---

## Project Structure

```
eafoods_preorder/
├── eafoods_preorder/      # Django project settings
├── preorder/              # App containing core features
├── manage.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── README.md
└── db.sqlite3
```

---

## Setup Instructions (Local without Docker)

1. Clone the repository:

```bash
git clone https://github.com/devketanpro/eafoods_preorder.git
cd eafoods_preorder
```

2. Create a Python virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Set environment variables:

```bash
export DJANGO_SETTINGS_MODULE=eafoods_preorder.settings
```

5. Apply database migrations:

```bash
python manage.py makemigrations
python manage.py migrate
```

6. Create a superuser:

```bash
python manage.py createsuperuser
```

7. Run the server:

```bash
python manage.py runserver
```

---

## Docker Usage

This project is fully Dockerized. The Docker Compose setup ensures all migrations are applied automatically and the server runs inside the container.

**Steps to run:**

1. Build the Docker container:

```bash
sudo docker compose build
```

2. Start the container:

```bash
sudo docker compose up
```

3. The Django server will be available at:

```
http://localhost:8000
```

**Notes:**

* SQLite database is used, so your data is persisted inside the container filesystem.
* The container runs `makemigrations`, `migrate`, and `runserver` automatically.

---

## API Documentation

The API is documented using **drf-spectacular**:

* **Swagger UI:** [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/)
* **Redoc:** [http://localhost:8000/api/redoc/](http://localhost:8000/api/redoc/)
* **Schema JSON:** [http://localhost:8000/api/schema/](http://localhost:8000/api/schema/)

---

## Testing

Unit and integration tests are written using **pytest**:

```bash
pytest preorder/tests/
```

---

## Notes

* Ensure Docker daemon is running before using `docker compose`.
* Add `0.0.0.0` to `ALLOWED_HOSTS` in `eafoods_preorder/settings.py` for Docker deployment:

```python
ALLOWED_HOSTS = ["0.0.0.0", "localhost"]
```

* If ports are already in use, update the `docker-compose.yml` port mapping.

---

## Author

**Ketan Bamniya**
Email: [devketanpro11@gmail.com](mailto:devketanpro11@gmail.com)
GitHub: [devketanpro](https://github.com/devketanpro)
