# Payment Service – Razorpay Integration

This service handles secure payment processing for the freelancing platform using Razorpay. It is built as a microservice and is responsible for creating payment intents, verifying payments, handling webhooks, and updating payment status reliably.

## Responsibilities

The Payment Service is responsible for:

- Creating Razorpay payment orders (payment intents)
- Storing payment records in the database
- Verifying payment authenticity using Razorpay signatures
- Handling Razorpay webhooks for guaranteed payment confirmation
- Acting as the single source of truth for payment status
- Notifying other services (Job / Application) after payment success

## Tech Stack

- **Backend:** Django, Django REST Framework
- **Payment Gateway:** Razorpay
- **Database:** MySQL / PostgreSQL
- **Security:** HMAC Signature Verification
- **Architecture:** Microservice

## Payment Flow

```
Client accepts proposal
        ↓
Frontend calls Payment Service (create-order)
        ↓
Payment Service creates Razorpay Order
        ↓
Frontend opens Razorpay Checkout UI
        ↓
User completes payment
        ↓
Frontend sends payment proof (verify API)
        ↓
Payment Service verifies signature
        ↓
Payment marked as PAID
        ↓
Razorpay Webhook confirms payment (final truth)
        ↓
Other services notified
```

## Environment Variables

Create a `.env` file in the project root and configure the following:

```env
RAZORPAY_KEY_ID=rzp_test_xxxxx
RAZORPAY_KEY_SECRET=xxxxxxxxxxxx
```

**⚠️ Important:** Never expose `RAZORPAY_KEY_SECRET` to the frontend. This secret must only be used on the backend.

## Installation & Setup

### 1. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run Migrations

```bash
python manage.py migrate
```

### 4. Start Development Server

```bash
python manage.py runserver
```

## Database Model

### Payment

```python
class Payment(models.Model):
    job_id = models.IntegerField()
    application_id = models.IntegerField()
    client_id = models.IntegerField()
    freelancer_id = models.IntegerField()

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default="INR")

    razorpay_order_id = models.CharField(max_length=100)
    razorpay_payment_id = models.CharField(max_length=100, null=True, blank=True)
    razorpay_signature = models.CharField(max_length=255, null=True, blank=True)

    status = models.CharField(
        max_length=20,
        choices=[
            ("created", "Created"),
            ("paid", "Paid"),
            ("failed", "Failed"),
            ("refunded", "Refunded"),
        ],
        default="created"
    )

    created_at = models.DateTimeField(auto_now_add=True)
```

## API Endpoints

### 1. Create Payment Order

Creates a Razorpay payment order and stores the payment record with status `created`.

**Endpoint:**

```http
POST /api/payments/create-order/
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json
```

**Request Body:**

```json
{
  "job_id": 1,
  "application_id": 10,
  "client_id": 5,
  "freelancer_id": 9,
  "amount": 5000
}
```

**Response:**

```json
{
  "order_id": "order_xyz",
  "amount": 500000,
  "currency": "INR",
  "status": "created"
}
```

**Response Fields:**
- `order_id` - Razorpay order ID
- `amount` - Amount in smallest currency unit (paise for INR)
- `currency` - Payment currency (default: INR)
- `status` - Payment status

### 2. Verify Payment

Verifies the payment signature and confirms payment from the frontend after user completes Razorpay checkout. This provides fast frontend feedback.

**Endpoint:**

```http
POST /api/payments/verify/
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json
```

**Request Body:**

```json
{
  "razorpay_order_id": "order_xyz",
  "razorpay_payment_id": "pay_abc",
  "razorpay_signature": "signature_here"
}
```

**Response:**

```json
{
  "status": "success",
  "message": "Payment verified",
  "payment_id": 1
}
```

**Note:** Frontend verification provides immediate feedback, but webhook verification is the final source of truth.

### 3. Razorpay Webhook

Handles payment confirmation events directly from Razorpay. This is the final source of truth for payment status.

**Endpoint:**

```http
POST /api/payments/webhook/
Content-Type: application/json
```

**Webhook Events Handled:**
- `payment.captured` - Payment successfully captured
- `payment.failed` - Payment failed
- `payment.authorized` - Payment authorized

**Security:**
- Verifies webhook signature using HMAC-SHA256
- Prevents fake payment events
- Idempotent updates prevent duplicate processing

## Postman Examples

### Create Order

**URL:** `POST http://localhost:8000/api/payments/create-order/`

**Headers:**
```
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json
```

**Body:**
```json
{
  "job_id": 1,
  "application_id": 10,
  "client_id": 5,
  "freelancer_id": 9,
  "amount": 5000
}
```

### Verify Payment

**URL:** `POST http://localhost:8000/api/payments/verify/`

**Headers:**
```
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json
```

**Body:**
```json
{
  "razorpay_order_id": "order_DBJOWzybf0sJbb",
  "razorpay_payment_id": "pay_DBJOWzybf0sJbb",
  "razorpay_signature": "9ef4dffbfd84f1318f6739a3ce19f9d85851857ae648f114332d8401e0949a3d"
}
```

## Security Design

The Payment Service implements multiple layers of security:

- **HMAC-SHA256 Verification:** Razorpay signatures are verified using HMAC-SHA256 to ensure authenticity
- **Backend-Only Secrets:** `RAZORPAY_KEY_SECRET` is never exposed to frontend
- **Immutable Payment Status:** Frontend cannot directly update payment status
- **Webhook Verification:** Razorpay webhooks are verified to prevent fake payment events
- **Idempotent Operations:** Duplicate webhook events are safely handled without duplicate processing
- **JWT Authentication:** All payment endpoints require valid JWT token

## Integration with Other Services

After successful payment confirmation via webhook, the Payment Service notifies:

- **Job Service:** To update job status and lock the freelancer
- **Application Service:** To mark the application as paid
- **Notification Service:** To send payment confirmation emails

## Testing

### Test with Razorpay Sandbox

1. Use Razorpay test credentials:
   ```
   Key ID: rzp_test_xxxxx
   Key Secret: xxxxxxxxxxxx
   ```

2. Use test payment cards:
   ```
   Card: 4111 1111 1111 1111
   Expiry: 12/25
   CVV: 123
   ```

### Unit Tests

```bash
python manage.py test payments
```

## Deployment Checklist

- [ ] Set `DEBUG=False`
- [ ] Use production Razorpay credentials
- [ ] Configure webhook URL in Razorpay dashboard
- [ ] Enable HTTPS/SSL for webhook endpoint
- [ ] Set secure `SECRET_KEY` in settings
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Use PostgreSQL instead of SQLite
- [ ] Enable CORS for frontend domain
- [ ] Set up monitoring and logging

## Webhook Configuration

To receive webhooks from Razorpay:

1. Go to Razorpay Dashboard → Settings → Webhooks
2. Add webhook URL: `https://yourdomain.com/api/payments/webhook/`
3. Select events: `payment.authorized`, `payment.failed`, `payment.captured`
4. Copy webhook secret and add to `.env`:
   ```env
   RAZORPAY_WEBHOOK_SECRET=xxxxx
   ```

## Error Handling

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| Invalid signature | Signature verification failed | Check Razorpay credentials |
| Order not found | Order ID doesn't exist | Verify order was created successfully |
| Duplicate payment | Webhook processed twice | System handles idempotently |
| Webhook timeout | Network issue with Razorpay | Implement retry mechanism |

## License

This project is licensed under the MIT License.

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Support

For issues and questions:

- Check Razorpay documentation: https://razorpay.com/docs/
- Open an issue on GitHub
- Contact the development team
