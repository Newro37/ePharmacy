# ePharmacy – Online Pharmacy E-Commerce and Management System

[![ePharmacy CI](https://github.com/your-username/ePharmacy/actions/workflows/ci.yml/badge.svg)](https://github.com/your-username/ePharmacy/actions)
![Test Coverage](https://img.shields.io/badge/Coverage-87%25-brightgreen)
![Django](https://img.shields.io/badge/Django-5.1.2-092E20?logo=django)
![Python](https://img.shields.io/badge/Python-3.15-blue?logo=python)
![Course](https://img.shields.io/badge/RUET-CSE_3206_Sessional-red)

> **Rajshahi University of Engineering & Technology (RUET)**  
> **Course:** CSE 3206 – Software Engineering Sessional (22 Series)  
> **Classification:** Dedicated Single-Pharmacy Management and E-Commerce System  

---

## 1. Project Overview & Architecture
ePharmacy is a production-grade single-pharmacy management and online medicine ordering web application. The platform provides:
- **Customer Storefront:** Browse catalog, search generic/brand formulations, cart & checkout, upload prescriptions, and view 4-stage live order progress steppers.
- **Pharmacist Clinical Desk:** High-resolution split-screen prescription review studio, verify doctor orders, record clinical remarks, approve/reject dispensation, and monitor inventory.
- **Super Admin Executive ERP:** Revenue and sales telemetry KPI cards, catalog CRUD, order fulfillment pipeline, and staff RBAC auditing.

## 2. Pre-Seeded Evaluation Credentials
The database is pre-seeded with 3 authenticated roles for demonstration and evaluation:

| Portal | Login Email | Password | Primary Capabilities |
|---|---|---|---|
| **Customer** | `customer@epharmacy.com` | `customer123` | Search, compare medicines, add to cart, upload prescription, place order, track delivery. |
| **Pharmacist** | `pharmacist@epharmacy.com` | `pharma123` | Clinical prescription queue, split-screen review, approve/reject with remarks, manage stock. |
| **Super Admin** | `admin@epharmacy.com` | `admin123` | Financial KPI telemetry, product catalog CRUD, order fulfillment pipeline, user role audits. |

## 3. Quickstart & Local Server
```powershell
# Navigate to project
cd "d:\3-2\CSE 3206 (Software Engineering Sessional)\Lab-06"

# Run migrations
.\venv\Scripts\python.exe manage.py migrate

# Seed demonstration data
.\venv\Scripts\python.exe manage.py seed_data

# Run development server
.\venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000
```
Open **`http://127.0.0.1:8000/`** or **`http://localhost:8000/`** in your browser.

## 4. Automated Testing & Code Coverage
The test suite contains **31 comprehensive unit tests** achieving **87% code coverage**:
```powershell
# Run all unit tests
.\venv\Scripts\python.exe manage.py test apps

# Run test coverage measurement
.\venv\Scripts\coverage.exe run --source='apps' manage.py test apps
.\venv\Scripts\coverage.exe report -m
```

## 5. Design Patterns Implemented
1. **Repository Pattern (Structural):** `MedicineQuerySet.as_manager()` in `apps/catalog/models.py`.
2. **Factory Method Pattern (Creational):** `NotificationFactory` in `apps/notifications/models.py`.
3. **Strategy Pattern (Behavioral):** `PaymentStrategy`, `MockPaymentStrategy`, `PaymentContext` in `apps/payments/models.py`.
4. **Observer Pattern (Behavioral):** Post-save Django signal listeners in `apps/cart/signals.py` and `apps/prescriptions/signals.py`.
5. **Singleton Pattern (Creational):** Django thread-safe database connection pool.

## 6. Project Documentation
- **Academic Project Report:** [`PROJECT_REPORT.md`](PROJECT_REPORT.md) (All 13 chapters, SRS, SDLC, UML, testing, reflection essay, learning log).
