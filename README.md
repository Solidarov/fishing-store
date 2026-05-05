# Fishing store

## Description
Will be shown soon...

## Main features
### User system:
- **Role-Based Access Control (RBAC):** Implemented via a Custom User model with three distinct roles: Admin, Seller, and Customer.
- **Automated Profile Lifecycle:** Utilizes Django Signals to automatically create and manage `CustomerProfile` or `SellerProfile` based on the user's current role.
- **Seller Moderation Workflow:** New seller accounts are set to "Inactive" by default, requiring administrative manual approval to ensure platform security.
- **Secure Public Registration:** Role selection via Radio Buttons with built-in protection against unauthorized Admin role assignment.
- **Smart Authentication Logic:** 
   - Auto-redirects for already authenticated users away from login/register pages.
   - Instant login for Customers upon signup and "Pending Activation" state for Sellers.
- **Unified Profile Interface:** A dynamic multi-form view that allows users to update both account credentials and role-specific metadata (addresses, store names) in one place.

## How to run localy
1. Prerequisties (Linux)
    - Python 3.14+ (pip, virtualenv)
    - Docker 29.4+
    - Git

2. Clone the repository
``` bash
git clone git@github.com:Solidarov/fishing-store.git
```

3. Create docker volume for Postgres container database
```bash
docker volume create db_data
```

4. Rewrite environment varibles in `.env` or use the mocking one that already provided

5. Run container
```bash
cd fishing-store && docker compose up --build
```

6. The app will be available in the browser under the `http:/localhost:8000/` address