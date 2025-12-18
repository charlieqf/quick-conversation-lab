# Implementation Plan - Multi-User Support

This plan details the full stack implementation of multi-user support, including specific libraries, file changes, and verification steps.

## User Review Required

> [!IMPORTANT]
> **Breaking Change**: The `User` table schema will change. The system will auto-migrate the existing user to 'admin' with a default password (e.g., 'admin') on first run, or require a script to set it.

## Technical Architecture

- **Auth Strategy**: OAuth2 with Password Flow (FastAPI `OAuth2PasswordBearer`).
- **Token**: JWT (JSON Web Tokens) containing `sub` (username) and `role`.
- **Hashing**: Bcrypt via `passlib`.

## Proposed Changes

### 1. Backend Implementation

#### Dependencies
- Add `python-jose`, `passlib[bcrypt]`, `python-multipart` to `requirements.txt`.

#### Models & Schema
- **[MODIFY] `backend/app/models.py`**:
    - Add columns to `User`:
        - `hashed_password` (String)
        - `role` (String, default='user')
        - `is_active` (Boolean, default=True)
- **[NEW] `backend/app/schemas.py`** (if not exists, or append):
    - `Token`, `TokenData`, `UserInDB`.

#### Authentication Module
- **[NEW] `backend/app/core/security.py`**:
    - `verify_password(plain, hashed)`
    - `get_password_hash(password)`
    - `create_access_token(data, expires)`
- **[NEW] Endpoint `backend/app/routers/auth.py`**:
    - `POST /token`: Validates user, returns JWT.

#### User Management Logic
- **[MODIFY] `backend/app/routers/users.py`**:
    - Add `get_current_user` dependency.
    - Update `get_profile` to use current authenticated user.
    - Add "bootstrapping" logic: If no users exist, create default Admin.

#### CLI Scripts (`backend/scripts/`)
- **[NEW] `create_user.py`**: Accepts args, hashes password, inserts to DB.
- **[NEW] `manage_users.py`**: List/Delete/Change Password functions.

### 2. Frontend Implementation

#### Auth Context
- **[NEW] `modules/Auth/AuthContext.tsx`**:
    - Stores `token` and `userProfile`.
    - Provides `login(username, password)` and `logout()` methods.
    - Axis interceptor to inject `Bearer <token>` header.

#### UI Components
- **[NEW] `modules/Auth/Login.tsx`**:
    - Centered card layout.
    - Error handling for "Invalid credentials".

#### Routing & Protection
- **[MODIFY] `src/App.tsx`**:
    - Wrap application with `AuthProvider`.
    - Create `PrivateRoute` component.
    - Redirect `/` to `/login` if no token.

#### Role-Based UI
- **[MODIFY] `modules/ScenarioEditor/index.tsx`**:
    - Subscribe to `AuthContext`.
    - `const isReadOnly = user.role !== 'admin';`
    - Update Buttons: `disabled={isReadOnly}`.
- **[MODIFY] `modules/RoleEditor/index.tsx`**:
    - Apply same `isReadOnly` logic.
- **[MODIFY] `modules/Settings/index.tsx`**:
    - Redirect non-admins if they somehow navigate here.

## 3. Verification Plan

### Automated
- **Auth Tests**: Add `tests/test_auth.py` to verify JWT generation and password hashing.

### Manual Walkthrough
1.  **Deployment**:
    - Run `pip install...`
    - Run DB migration (auto via App startup or script).
2.  **Admin Check**:
    - Login with `admin/admin`.
    - Create a Scenario (Success).
3.  **User Creation**:
    - Run `python backend/scripts/create_user.py --username testuser --password testpass`.
4.  **Standard User Check**:
    - Logout and Login as `testuser`.
    - Can view Scenario? (Yes)
    - Can see Save button? (No/Disabled)
    - Can see Settings? (No)
