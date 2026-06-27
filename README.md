# Payment Service

Payment Service integrates Labora with Razorpay for order creation, payment verification, webhook handling, payment persistence, and internal payment reporting.

## Responsibilities

- Create Razorpay payment orders.
- Store payment records for jobs/applications.
- Verify Razorpay checkout signatures.
- Process Razorpay `payment.captured` webhooks.
- Notify freelancers when a payment is marked paid.
- Expose internal payment lists, details, and statistics for Admin Service.

## Features

- Razorpay order creation in INR.
- Duplicate-safe verification and webhook payment updates.
- HMAC webhook signature verification with `RAZORPAY_KEY_SECRET`.
- Paid revenue aggregation for admin statistics.

## API Endpoints

Base path: `/api/`

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| `POST` | `payments/orders/` | DRF default JWT configured | Create a Razorpay order and local `Payment` record. |
| `POST` | `payments/verify/` | DRF default JWT configured | Verify Razorpay payment signature and mark payment as `paid`. |
| `POST` | `payments/webhooks/razorpay/` | Razorpay signature header | Process Razorpay webhook events. |

The public payment views do not apply explicit role permissions in the view functions.

## Internal Service Endpoints

Internal endpoints use `X-Service-Key: <SERVICE_API_KEY>`.

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `internal/payments/` | Return paginated payment summaries. |
| `GET` | `internal/payments/stats/` | Return payment counts and paid revenue total. |
| `GET` | `internal/payments/<payment_id>/` | Return one payment summary. |

## Authentication

The service configures Simple JWT with the shared RS256 public key. Internal views require `IsInternalService`. Webhooks are authenticated by Razorpay's `X-Razorpay-Signature`.

## Environment Variables

| Variable | Purpose |
| --- | --- |
| `DJANGO_SECRET_KEY` | Django secret key. |
| `DEBUG` | Enables debug mode when set to `True`. |
| `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` | MySQL database configuration. |
| `JWT_PUBLIC_KEY_PATH` | Public key used for JWT verification. |
| `SERVICE_API_KEY` | Shared key for internal endpoints. |
| `RAZORPAY_KEY_ID` | Razorpay API key id. |
| `RAZORPAY_KEY_SECRET` | Razorpay API secret and webhook-signature secret. |
| `NOTIFICATION_SERVICE_URL` | Used by shared notification client. |
| `*_SERVICE_URL` | Additional service URL settings loaded by settings. |

## Setup

```bash
cd PaymentService
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 8008
```

## Service Architecture

- Django project: `paymentservice`
- App: `payment`
- Razorpay client: `payment/razorpay_client.py`
- Internal permission: `payment.permissions.internal_service.IsInternalService`
- Outbound dependency: Notification Service through shared notification client

## Database Models

- `Payment`: stores job/application ids, client/freelancer ids, amount, currency, Razorpay order/payment/signature fields, status, and creation timestamp.

## Notification/Event Flow

Successful checkout verification or `payment.captured` webhook processing sends `payment_received` to the freelancer. Notification failures are logged but do not fail payment processing.
