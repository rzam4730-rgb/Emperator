# Emperator Authentication

## Architecture

Emperator uses phone/password authentication with bcrypt password hashing, short-lived JWT access tokens, and rotating opaque refresh tokens stored only as SHA-256 hashes in SQLite.

Flow:

1. `POST /api/auth/register` creates a user, restaurant, owner membership, starter menu, access token and refresh token.
2. `POST /api/auth/login` verifies the bcrypt password and issues a new access/refresh token pair.
3. API requests send `Authorization: Bearer <access_token>`.
4. The backend validates the JWT and resolves `user_id`, `restaurant_id` and role.
5. RBAC checks the required permission before protected endpoints run.
6. When the access token expires, the frontend calls `POST /api/auth/refresh`. The old refresh token is revoked and a new refresh token is issued.
7. `POST /api/auth/logout` revokes the supplied refresh token.

## Credentials and tokens

- Passwords are never stored in plaintext. They are stored as bcrypt hashes.
- Access tokens are JWTs signed with `EMPERATOR_JWT_SECRET` and expire after 15 minutes by default.
- Refresh tokens are random opaque values. Only their SHA-256 hashes are stored in the database.
- Refresh tokens rotate on every refresh; the previous token is revoked.
- The frontend keeps the access token in memory and persists only the refresh token in browser storage so the access token is not persisted across application restarts.

## Multi-tenant isolation

Every authenticated user belongs to one or more restaurants through `user_restaurants`. Business records use `restaurant_id`, and protected queries always scope products, customers and orders to the authenticated restaurant.

## Roles

`owner`, `manager`, `cashier`, `kitchen`, and `accountant` are seeded. Permissions are stored separately in `permissions` and `role_permissions`.

## Production requirements

Set a strong random `EMPERATOR_JWT_SECRET` through the environment. Do not commit a real secret. Serve the API over HTTPS and restrict CORS to the actual Emperator origins before production deployment.
