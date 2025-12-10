# Database Migration & Schema Design

## 1. Overview
Migrate Frontend LocalStorage data (Scenarios, Roles, UserProfile) to Backend Database (TiDB/MySQL) using a **Hybrid Schema (Relational + JSON)**.

## 2. Enhanced Table Design

### 2.0 Common Fields & Integrity
- All tables include `created_at` (Default Now) and `updated_at` (OnUpdate Now).
- All `user_id` columns are indexed Foreign Keys to `users.id`.
- **System Data**: `scenarios` and `roles` have `is_default` (BOOL). `is_default=True` means visible to all users (System Templates).

### 2.1 Table: `users`
| Field | Type | Attributes | Note |
| :--- | :--- | :--- | :--- |
| `id` | VARCHAR(36) | PK | |
| `username` | VARCHAR(100) | Unique, Index | Login ID / Name |
| `avatar_url` | VARCHAR(512) | | **Optimization**: Store URL path, not Base64 blob. |
| `settings` | JSON | | User-specific settings (API Keys, etc.) |

### 2.2 Table: `scenarios`
| Field | Type | Attributes | Note |
| :--- | :--- | :--- | :--- |
| `id` | VARCHAR(36) | PK | |
| `user_id` | VARCHAR(36) | FK, Index, Nullable | NULL = System System |
| `is_default` | BOOL | Default False | True = Template for everyone |
| `title` | VARCHAR(255) | Index | |
| `subtitle` | VARCHAR(255) | | |
| `description` | TEXT | | |
| `tags` | JSON | | *Future: Generated Column for Indexing* |
| `script_content` | MEDIUMTEXT | | **Limit**: 16MB max |
| `generation_prompt` | TEXT | | |
| `workflow` | TEXT | | |
| `knowledge_points` | TEXT | | |
| `scoring_criteria` | TEXT | | |
| `scoring_dimensions` | JSON | | |

### 2.3 Table: `roles`
| Field | Type | Attributes | Note |
| :--- | :--- | :--- | :--- |
| `id` | VARCHAR(36) | PK | |
| `user_id` | VARCHAR(36) | FK, Index, Nullable | |
| `is_default` | BOOL | Default False | |
| `name` | VARCHAR(100) | | |
| `name_cn` | VARCHAR(100) | Index | |
| `title` | VARCHAR(100) | | |
| `avatar_url` | VARCHAR(512) | | Replaces Base64 |
| `focus_areas` | JSON | | |
| `personality` | JSON | | |
| `system_prompt_addon` | TEXT | | |
| `generation_prompt` | TEXT | | |

### 2.4 Table: `session_records` (Enhanced)
| Field | Type | Attributes | Note |
| :--- | :--- | :--- | :--- |
| `id` | VARCHAR(36) | PK | |
| `user_id` | VARCHAR(36) | FK, Index | **New**: Multi-tenant support |
| `scenario_id` | VARCHAR(36) | Index | |
| `role_id` | VARCHAR(36) | Index | |
| `start_time` | DATETIME | Index | Sort key |
| `score` | INT | | |
| `duration_seconds` | INT | | |
| `messages` | JSON | | Full transcript |
| `ai_analysis` | JSON | | |
| `audio_url` | VARCHAR(512) | | Path to WAV file (Future) |

## 3. Migration & Sync Strategy

### 3.1 Migration Tooling
- **MVP Phase**: Use `SQLAlchemy.create_all()` for initial table creation.
- **Future**: Introduce `Alembic` for versioned migrations once schema stabilizes (Post-MVP).

### 3.2 Data Sync (LocalStorage -> DB)
1.  **Detection**: Frontend checks if DB has User Scenarios (`SELECT count where user_id=ME`).
2.  **Prompt**: If DB is empty but LocalStorage has data, show "Migrate Local Data" button.
3.  **Upload**: Frontend loops through LS data -> POST `/api/scenarios` (with `user_id`).
4.  **Cutover**: After successful upload, clear LS (or mark as archived) and switch mode to "API Only".

### 3.3 Seeding Defaults
- Endpoint: `/api/system/init_defaults`
- **Idempotency**: Logic checks `if exists(id=DEFAULT_ID)`. Only inserts if missing.
- **Ownership**: Sets `user_id=NULL`, `is_default=True`.

## 4. Performance & Security
- **Payload Limits**: API will enforce 10MB limit (FastAPI/Nginx config) to prevent Base64 bloat abuse.
- **Search**: Scenarios list filters by `(user_id = CURRENT_USER OR is_default = TRUE)`.

