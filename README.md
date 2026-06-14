# Client Profile Service

## Overview

The Client Profile Service is a microservice responsible for managing client-related data in the platform. It ensures that only authenticated and authorized users can access or modify client profiles.

This service works alongside the Auth Service, which handles user authentication and JWT token generation.

---

## Architecture

* **Auth Service**

  * Handles login and user authentication
  * Generates JWT tokens (signed with private key)

* **Client Profile Service**

  * Verifies JWT tokens using public key
  * Validates user role (must be `client`)
  * Processes profile-related requests

* **Nginx (API Gateway)**

  * Routes incoming requests to appropriate services
  * Simplifies service access through a single entry point

---

## Request Flow

1. User logs in via Auth Service
2. Auth Service returns JWT token
3. Client sends request with JWT:

   ```
   Authorization: Bearer <token>
   ```
4. Nginx routes request to Client Profile Service
5. Client Profile Service:

   * Verifies JWT signature
   * Checks token expiration
   * Extracts user data
   * Validates user role = `client`
6. Request is processed

---

## Security Design

### 1. JWT Verification

* Token must be verified using **public key**
* Reject invalid or tampered tokens

### 2. Role-Based Access Control

* Only users with role `client` can access endpoints
* Unauthorized roles → `403 Forbidden`

### 3. Token Validation

* Check expiration (`exp`)
* Check issuer (`iss`)
* Check audience (`aud`) (optional but recommended)

### 4. Zero Trust Policy

* Never trust frontend
* Always validate inside service

---

## Example Middleware (Django)

```python
from rest_framework.exceptions import AuthenticationFailed
import jwt

def verify_jwt(token):
    try:
        payload = jwt.decode(token, PUBLIC_KEY, algorithms=["RS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationFailed("Token expired")
    except jwt.InvalidTokenError:
        raise AuthenticationFailed("Invalid token")
```

---

## Role Validation Example

```python
def check_client_role(user):
    if user.get("role") != "client":
        raise PermissionDenied("Access denied")
```

---

## Nginx Configuration Example

```nginx
server {
    listen 80;

    location /auth/ {
        proxy_pass http://auth_service:8000/;
    }

    location /client/ {
        proxy_pass http://client_profile_service:8001/;
    }
}
```

---

## Best Practices

* Use **RS256 (Public/Private key)** instead of HS256
* Never expose private key
* Use HTTPS in production
* Log all authentication failures
* Keep services stateless

---

## Common Mistakes

❌ Trusting frontend token without verification
❌ Skipping role validation
❌ Using same secret across all services
❌ Putting business logic in Nginx

---

## Future Improvements

* Add API Gateway authentication layer
* Implement rate limiting
* Add refresh token mechanism
* Centralized logging and monitoring

---

## Conclusion

The Client Profile Service must independently verify authentication and authorization, ensuring secure and scalable communication in a microservices architecture.

---
