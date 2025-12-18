# Implementation Plan: Role-Based Log Filtering (v2)

> **Dev Team Review Feedback**: Enforce filtering at both server-side (WebSocket) and UI. UI filtering alone is not secure as non-admin users can read all logs via devtools.

## Overview

Filter realtime session logs based on user role:

| Role | Visible Logs |
|------|--------------|
| **Admin** | All logs (connection, audio, VAD, timing, transcripts) |
| **Regular User** | Transcripts only (`Transcript [User/Model]: ...`) |

---

## Architecture

### Current Log Flow
```
Backend WebSocket (websocket.py)
       ↓ sends all messages
Frontend VoiceSocket.ts
       ↓ parses messages, calls log()
useSessionConnection.ts (log function)
       ↓
logs: LogEntry[] (React State)
       ↓
SessionDebugConsole.tsx (renders)
```

### Proposed Log Flow (Secure)
```
Backend WebSocket (websocket.py)
       ↓ FILTER: check user.role before sending
       ↓ admin: send all | user: send transcript only
Frontend VoiceSocket.ts
       ↓
useSessionConnection.ts
       ↓
SessionDebugConsole.tsx (belt-and-suspenders filter)
```

---

## Implementation

### Phase 1: Backend (Primary Security Layer)

#### 1.1 Define Log Categories
All WebSocket messages already have a `type` field. Map to categories:

| Message Type | Category | Visible to |
|--------------|----------|------------|
| `session.created` | system | admin |
| `audio.output` | system | admin |
| `transcription` | transcript | all |
| `turn.complete` | system | admin |
| `error` | system | admin |
| `warning` | system | admin |

#### 1.2 Modify `websocket.py` - Add send helper

```python
# After user authentication (line ~65)
is_admin = user.role == 'admin'

# Helper function to filter outgoing messages
async def send_filtered(msg_type: str, payload: dict, category: str = 'system'):
    """Send message only if user role permits."""
    if category == 'transcript' or is_admin:
        await websocket.send_json({
            "type": msg_type,
            "timestamp": int(time.time() * 1000),
            "payload": payload
        })
    # else: drop message silently for non-admin
```

#### 1.3 Full Inventory of `send_json` Calls

All outbound paths must use `send_filtered()` except for critical auth errors where user role is not yet determined:

| Line | Context | Type | Category | Action |
|------|---------|------|----------|--------|
| 55 | Auth failure (no user yet) | error | N/A | **Keep direct** - client needs error before disconnect |
| 81 | Model not found | error | system | Use `send_filtered()` |
| 107 | `on_audio` callback | audio.output | system | Use `send_filtered()` |
| 119 | `on_transcription` - turn complete | turn.complete | system | Use `send_filtered()` |
| 125 | `on_transcription` - actual transcript | transcription | **transcript** | Use `send_filtered()` ✅ |
| 139 | `handle_error_async` | error | system | Use `send_filtered()` |
| 192 | Model disabled error | error | system | Use `send_filtered()` |
| 278 | session.created | session.created | system | Use `send_filtered()` |
| 303 | warning (rate limit) | warning | system | Use `send_filtered()` |
| 335 | Model response parse error | warning | system | Use `send_filtered()` |
| 346 | session.ended | session.ended | system | Use `send_filtered()` |
| 361 | Disconnect cleanup | session.ended | system | Use `send_filtered()` |
| 375 | On close handler | session.ended | system | Use `send_filtered()`|

**Note**: Line 55 (auth failure) MUST remain direct send because:
1. User object doesn't exist yet at that point
2. Client needs the error to display login prompt

All other 12 calls should use `send_filtered()`.

---

### Phase 2: Frontend (Belt-and-Suspenders)

#### 2.1 `types.ts` - Add category field
```diff
+export type LogCategory = 'system' | 'transcript';

 export interface LogEntry {
   timestamp: string;
   message: string;
   type: 'info' | 'success' | 'error' | 'stream' | 'thought';
   detail?: string;
+  category?: LogCategory;
 }
```

#### 2.2 `useSessionConnection.ts` - Tag logs
```diff
-const log = useCallback((msg: string, type) => {
+const log = useCallback((msg: string, type, category: LogCategory = 'system') => {
   setLogs(prev => [...prev, { timestamp, message: msg, type, category }]);
 }, []);

 // For transcript callback:
-log(`Transcript [${role}]: ${text}`, 'info');
+log(`Transcript [${role}]: ${text}`, 'info', 'transcript');
```

#### 2.3 `SessionDebugConsole.tsx` - Backup filter
```diff
+import { useAuth } from '../../../contexts/AuthContext';

 export const SessionDebugConsole = ({ logs, onClear }) => {
+  const { user } = useAuth();
+  const isAdmin = user?.role === 'admin';
+  const visibleLogs = isAdmin ? logs : logs.filter(l => l.category === 'transcript');
   
-  // render logs
+  // render visibleLogs
```

---

## Files Affected

| Layer | File | Change |
|-------|------|--------|
| Backend | `websocket.py` | Add `send_filtered()`, update all sends |
| Frontend | `types.ts` | Add `LogCategory`, extend `LogEntry` |
| Frontend | `useSessionConnection.ts` | Update `log()` signature |
| Frontend | `SessionDebugConsole.tsx` | Add role-based filter |

---

## Security Considerations

1. **Primary filter is server-side** - non-admin users never receive system logs
2. **Frontend filter is backup** - defense in depth
3. **No sensitive data in transcript logs** - only speech content
4. **Token already validated** - user.role is trusted after JWT decode

---

## Implementation Steps

1. [ ] Backend: Add `is_admin` flag after auth
2. [ ] Backend: Create `send_filtered()` helper
3. [ ] Backend: Update all `send_json` calls with category
4. [ ] Frontend: Add `LogCategory` to `types.ts`
5. [ ] Frontend: Update `log()` function signature
6. [ ] Frontend: Tag transcript logs with category
7. [ ] Frontend: Add filter in `SessionDebugConsole`
8. [ ] Test: Verify admin sees all, user sees transcripts only
9. [ ] Deploy to GCP

**Estimated effort**: ~1 hour (backend 30min + frontend 30min)
