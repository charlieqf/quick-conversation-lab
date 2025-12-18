# Multi-User Support Requirements

## 1. Overview
The system currently supports a single user. This feature introduces multi-user support, distinguishing between **Administrator** and **Standard User** roles, with basic authentication.

## 2. User Roles

### 2.1 Administrator (Admin)
- **Identity**: The existing default user.
- **Permissions**:
    - **Full System Access**: access to all features.
    - **System Configuration**: Can view and modify the "Settings" page.
    - **Content Management**: Can Create, Edit, Save, and Delete Scenarios, Roles, and Scripts.
    - **AI Generation**: Can use AI tools for generation.

### 2.2 Standard User
- **Identity**: Created by the Administrator via backend scripts.
- **Permissions**:
    - **Read-Only Access**: Can view Scenarios and Roles.
    - **Restricted UI**:
        - **Settings**: The "Settings" page/tab is **hidden**.
        - **Editors**: In Scenario/Role editors, buttons for Create, Save, Generate, and Delete are **disabled (greyed-out)**.
    - **Allowed Actions**:
        - Can run conversation Sessions.
        - Can view Session Reports.

## 3. Functional Requirements

### 3.1 Authentication
- **Login Page**:
    - New route `/login`.
    - Simple form: Username, Password, Login button.
- **Mechanism**:
    - Username + Password authentication.
    - Passwords must be hashed (bcrypt).
    - Session management via JWT (stateless) or secure cookie.

### 3.2 User Management (CLI Only)
No UI for user management in this phase. The following backend scripts are required:
1.  `create_user.py`: Create new users with optional Admin flag.
2.  `delete_user.py`: Remove a user.
3.  `change_password.py`: Reset/Change a user's password.
4.  `list_users.py`: View all users and their roles.

### 3.3 Backend Changes
- **Data Model**: Update `User` table with `password_hash`, `role` (default='user'), `is_active`.
- **API Security**:
    - Protect modification endpoints (`POST`, `PUT`, `DELETE`).
    - Verify `role='admin'` for privileged actions.
    - Public/User endpoints: `GET` scenarios (read-only), `POST` sessions (run permitted).

### 3.4 Frontend Changes
- **Routing**: Guard all routes (except `/login`). Redirect unauthenticated users to Login.
- **UI adaptation**:
    - Check user role on load.
    - If `role != 'admin'`, hide Settings link.
    - If `role != 'admin'`, disable specific action buttons in Editors.
