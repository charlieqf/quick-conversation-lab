# LocalStorage Migration Plan

## Overview
This document outlines the plan to migrate the remaining client-side `localStorage` data to the Backend API. This ensures data persistence across devices, enables user accounts, and improves application consistency.

## Verified Findings
The following `localStorage` keys were identified and verified in the codebase:

1.  **`quick_user_profile`**: Stores user name and avatar prompt. Used in `App.tsx` and `HistoryModule`.
2.  **`quick_settings`**: Stores model selection (`selectedModel`, `selectedScenarioModel`) and voice selection (`selectedVoice`). Used in `Settings`, `Report`, and `ActiveSession`.
3.  **`quick_scenarios`**: Stores local scenario drafts in `ScenarioEditor` (disconnected from the main DB-backed list).
4.  **`quick_eval_prompt`**: Stores the user's custom prompt for AI evaluation.
5.  **`VITE_API_BASE_URL`**: Used for developer API overrides.

## Migration Strategy

### 1. User Profile (`quick_user_profile`)
**Goal**: Persist user identity and preference to the `users` table.

*   **Backend**: 
    *   Ensure `User` model has `username` (name), `avatar_url` (or prompt info).
    *   Create endpoints: `GET /api/user/profile` and `PUT /api/user/profile`.
*   **Frontend**: 
    *   `App.tsx`: On load, fetch profile from API.
    *   `HistoryModule` (Profile Modal): Save updates to API instead of `localStorage`.
    *   Remove `localStorage` fallback once implemented.

### 2. User Settings (`quick_settings` & `quick_eval_prompt`)
**Goal**: Persist global application settings (models, voices) and custom prompts to the `users` table's JSON column.

*   **Backend**: 
    *   Use the existing `settings` JSON column in `User` model.
    *   Extend `GET /api/user/profile` to include settings OR create `GET/PUT /api/user/settings`.
    *   Schema:
        ```json
        {
          "selectedModel": "gemini-2.5-flash",
          "selectedVoice": "Kore",
          "selectedScenarioModel": "gemini-2.5-flash",
          "evalPrompt": "..." 
        }
        ```
*   **Frontend**: 
    *   `SettingsModule`: Load initial state from API. Save changes to API.
    *   `ActiveSession`: Fetch settings from API (via prop or context) instead of reading `localStorage` directly (or load user profile into global context).
    *   `ReportModule`: Load custom `evalPrompt` from user settings API.

### 3. Scenario Drafts (`quick_scenarios`)
**Goal**: Unify the "Draft" and "Saved" states. `ScenarioEditor` currently writes to LS, while `Selection` reads from DB.

*   **Strategy**: Treat "Drafts" as "Unpublished" or simply save directly to the DB.
*   **Backend**: 
    *   The `scenarios` table already exists.
    *   Optional: Add `status` column ('draft', 'published') if distinction is needed. For now, direct save is acceptable.
*   **Frontend**: 
    *   `ScenarioEditor`: 
        *   **Load**: Fetch `GET /api/data/scenarios/{id}`.
        *   **Save**: `PUT /api/data/scenarios/{id}` (or POST for new).
        *   **Auto-save**: Implement debounce auto-save to backend or keep manual "Save" button. 
        *   **Remove**: All `localStorage` logic in `ScenarioEditor`.

### 4. Developer Overrides (`VITE_API_BASE_URL`)
**Goal**: Retain for development flexibility.

*   **Strategy**: **Do Not Migrate**. 
*   **Reason**: This is a developer-only tool for pointing the frontend to different backends (localhost vs cloud) without rebuilding. It does not belong in the production database.

## Execution Order
1.  **Scenario Editor**: High priority to fix the "Disconnected Data" bug (Editor saves to local, List reads from DB).
2.  **User Profile & Settings**: Implement `User` endpoints and update `App.tsx` / `SettingsModule`.
3.  **Cleanup**: Remove unused `localStorage` code.
