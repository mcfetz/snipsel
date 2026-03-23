# Snipsel Backend API Documentation

Welcome to the Snipsel Backend API documentation. This document provides a comprehensive guide for developers to understand and interact with the Snipsel backend services.

## General Information

### Base URL
All API requests should be made to the base URL:
`http://<your-domain>/api`

### Authentication
Snipsel uses session-based authentication. Upon successful login, a session cookie is issued and must be included in subsequent requests.

- **Session Cookie**: `session`
- **CSRF Protection**: Ensure `SupportsCredentials: true` is set in your client requests.

### Response Format
All responses are returned in JSON format. Successful responses typically contain the requested data under a relevant top-level key.

**Error Response Example:**
```json
{
  "error": {
    "code": "invalid_credentials",
    "message": "Invalid username or password"
  }
}
```

---

## Authentication & User Profile

### Registration
Register a new user account.
- **URL**: `/auth/register`
- **Method**: `POST`
- **Body**: `{"username": "...", "password": "...", "email": "..."}`

### Login
Authenticate with username and password.
- **URL**: `/auth/login`
- **Method**: `POST`
- **Body**: `{"username": "...", "password": "..."}`
- **Success Response**: User object. If 2FA is enabled, returns `{"otp_required": true}`.

### OTP Verify
Complete login if 2FA is enabled.
- **URL**: `/auth/login/otp`
- **Method**: `POST`
- **Body**: `{"otp": "123456"}`

### Identity (Me) & Statistics
- **GET /auth/me**: Get current user info.
- **PATCH /auth/me**: Update user settings (email, password, default_collection_header_color, day_collection_template_id, carry_over_open_tasks).
- **GET /auth/me/stats**: Get counts of collections, snipsels, completed tasks, and attachments.

---

## Collections

Collections organize snipsels. They can be daily lists (`type: day`) or custom lists (`type: list`).

### List & Search
- **GET /collections**: List collections.
  - Query: `include_archived=1` (include archived), `search=...` (filter by title).
- **GET /collections/autocomplete**: Quick search.
  - Query: `q=...`

### Today's Collection
- **GET /collections/today**: Fetches or creates the daily collection.
  - Query: `day=YYYY-MM-DD` (optional).

### Managed Endpoints
- **POST /collections**: Create a collection.
- **GET /collections/<id>**: Get details.
- **PATCH /collections/<id>**: Update (title, icon, header_image_url, header_color, archived, is_template, is_passcode_protected, default_snipsel_type, show_completed_tasks).
- **DELETE /collections/<id>**: Delete (fails if it has backlinks from other active collections).

### Locking & Favorites
- **POST /auth/me/passcode**: Set/update personal passcode.
- **POST /auth/me/passcode/verify**: Unlock a protected collection. `{"passcode": "...", "collection_id": "..."}`.
- **POST /collections/<id>/favorite**: Add to favorites.
- **DELETE /collections/<id>/favorite**: Remove from favorites.

---

## Snipsels

### Collection Interaction
- **GET /collections/<id>/snipsels**: List all snipsels in a collection.
- **POST /collections/<id>/snipsels**: Create new snipsel in this collection.
- **PATCH /collections/<id>/snipsels/reorder**: Reorder items. `{"items": [{"snipsel_id": "...", "position": 1, "indent": 0}, ...]}`
- **DELETE /collections/<id>/snipsels/<snipsel_id>`: Remove snipsel from collection.
- **DELETE /collections/<id>/snipsels/completed`: Batch delete all completed tasks in this collection.
- **POST /collections/<id>/snipsels/completed/reset`: Re-open all completed tasks in this collection.

### Snipsel Operations
- **GET /snipsels/<id>**: Get full snipsel details including backlinks, tags, and placements.
- **PATCH /snipsels/<id>**: Update snipsel content, type, task status, or reminders.
- **POST /snipsels/<id>/reactions**: Toggle emoji reaction. `{"emoji": "🚀"}`.
- **POST /collections/<id>/snipsels/<snipsel_id>/reference**: Create a reference to an existing snipsel. Body: `{"indent": 0}` (optional).
- **POST /collections/<id>/snipsels/<snipsel_id>/copy**: Create a full copy of a snipsel.

---

## Search & Exploration

### Full Text Search
- **GET /api/search**: Global search for snipsels and collections.
- **Query Params**:
  - `q`: Search query.
  - `tag`: Filter by tag name.
  - `mention`: Filter by @mention name.
  - `mentions_me`: `1` to find tasks assigned to you.
  - `scope`: `my`, `shared`, or `all`.
  - `type`: `text`, `task`, `media`.
  - `task_done`: `0` or `1`.
  - `day`: `YYYY-MM-DD` (filter by date).

### Tags & Mentions
- **GET /tags**: List available tags. Query: `scope`, `q`.
- **GET /mentions**: List available @mentions. Query: `scope`, `q`.
- **GET /search/mentions/incoming**: Find external daily snipsels that mention you. Query: `day`.

---

## Attachments

- **POST /snipsels/<id>/attachments**: Upload (multipart/form-data, key `file`).
- **GET /attachments/<id>**: Download original.
- **GET /attachments/<id>/thumbnail**: Download thumbnail.
- **DELETE /attachments/<id>**: Delete attachment.

---

## Importers (TwoS)

- **POST /importer/twos/login**: Authenticate with TwoS. `{"username": "...", "password": "..."}`.
- **POST /importer/twos/lists**: Fetch user lists. `{"token": "...", "userId": "..."}`.
- **POST /importer/twos/search**: Search TwoS. `{"token": "...", "userId": "...", "query": "..."}`.
- **POST /importer/twos/import**: Import lists. `{"token": "...", "userId": "...", "listIds": ["..."], "overwrite": false}`.

---

## Quick Add (API Key)

External integrations (iOS Shortcuts, browser extensions) can add snipsels via API key without full OAuth flow. Create an API key in **Settings → API Keys** first.

### Quick Add Snipsel
- **URL**: `/quick_add`
- **Method**: `POST`
- **Headers**:
  - `X-API-Key`: Your API key (e.g., `snipsel_abc123...`)
  - `Content-Type: application/json`
- **Body**:
  ```json
  {
    "content": "Meeting notes from standup",
    "type": "note",
    "title": "Standup",
    "tags": ["work", "meeting"]
  }
  ```
- **Parameters**:
  - `content` (string, optional): The snipsel content (markdown supported)
  - `type` (string, optional): `"note"` (default) or `"task"`
  - `title` (string, optional): Alternative to content if only title provided
  - `image_url` (string, optional): URL to an image to attach
  - `tags` (array of strings, optional): Tags to apply (e.g., `["work", "important"]`)
- **Response**:
  ```json
  {
    "snipsel": {
      "id": "uuid",
      "type": "text",
      "content": "Meeting notes from standup",
      "created_at": "2024-03-23T14:30:00"
    },
    "collection": {
      "id": "uuid",
      "title": "Monday, March 23"
    }
  }
  ```
- **Behavior**: Creates the snipsel in today's daily collection. Creates the collection if it doesn't exist.

### Curl Examples

```bash
# Simple note
 curl -X POST https://yourdomain.com/api/quick_add \
  -H "Content-Type: application/json" \
  -H "X-API-Key: snipsel_your_key_here" \
  -d '{"content": "Idea for project"}'

# Task with tags
 curl -X POST https://yourdomain.com/api/quick_add \
  -H "Content-Type: application/json" \
  -H "X-API-Key: snipsel_your_key_here" \
  -d '{
    "content": "Buy groceries",
    "type": "task",
    "tags": ["shopping", "home"]
  }'

# Upload file (multipart/form-data)
 curl -X POST https://yourdomain.com/api/quick_add \
  -H "X-API-Key: snipsel_your_key_here" \
  -F "content=Screenshot from meeting" \
  -F "type=note" \
  -F "file=@/path/to/screenshot.png" \
  -F "tags=work,meeting"

# Upload multiple files at once (all in one snipsel)
 curl -X POST https://yourdomain.com/api/quick_add \
  -H "X-API-Key: snipsel_your_key_here" \
  -F "content=Vacation photos" \
  -F "file=@photo1.jpg" \
  -F "file=@photo2.jpg" \
  -F "file=@photo3.jpg" \
  -F "tags=vacation"
```

**File Upload Notes:**
- Use `multipart/form-data` instead of JSON when uploading files
- The `file` field contains the uploaded file
- Images automatically get thumbnails generated
- Supported types: images (JPEG, PNG, GIF, WebP, **HEIC/HEIF**), videos (with FFmpeg), and any other file type
- Maximum file size is configured by `SNIPSEL_MAX_UPLOAD_BYTES` (default: 10MB)
- **HEIC Support**: Apple iPhone photos in HEIC format are fully supported with thumbnail generation

---

## Proxy

- **GET /proxy/deezer**: Resolve Deezer links/metadata. Query: `url` or `type`+`id`.
- **GET /proxy/youtube**: Fetch YouTube oEmbed metadata. Query: `url`.

---

## Common Objects

### Snipsel Object
```json
{
  "id": "uuid",
  "type": "text | task | media",
  "content_markdown": "...",
  "task_done": false,
  "reactions": [
    { "emoji": "👍", "count": 2, "active": true }
  ],
  "attachments": [
    { "id": "uuid", "filename": "...", "has_thumbnail": true }
  ]
}
```

### Collection Item (Placement)
```json
{
  "collection_id": "uuid",
  "snipsel_id": "uuid",
  "position": 5,
  "indent": 0,
  "snipsel": { ...SnipselObject... }
}
```
