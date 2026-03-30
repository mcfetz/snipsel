# Release Notes - March 30, 2026

## 🎉 Major Release: OIDC Authentication & Admin User Management

This release introduces enterprise-grade authentication and user management capabilities to Snipsel.

---

## ✨ New Features

### 🔐 OIDC / Single Sign-On (SSO) Support

Snipsel now supports authentication via any OIDC-compliant identity provider:

- **Google Workspace**
- **Microsoft Azure AD**
- **Keycloak**
- **Authentik**
- **Synology SSO**
- And any other OIDC provider

**New Environment Variables:**

| Variable | Default | Description |
|----------|---------|-------------|
| `SNIPSEL_OIDC_ENABLED` | `0` | Enable OIDC authentication |
| `SNIPSEL_OIDC_DISCOVERY_URL` | - | OIDC discovery URL |
| `SNIPSEL_OIDC_CLIENT_ID` | - | OIDC client ID |
| `SNIPSEL_OIDC_CLIENT_SECRET` | - | OIDC client secret |
| `SNIPSEL_OIDC_SCOPE` | `openid email profile` | OIDC scopes |
| `SNIPSEL_OIDC_PROVIDER_NAME` | `OIDC` | Display name for login button |
| `SNIPSEL_OIDC_DISABLE_PASSWORD_LOGIN` | `0` | Disable password login (force OIDC/Passkey) |

**Features:**
- Automatic user provisioning on first OIDC login
- Existing users can link their OIDC account
- First user via OIDC automatically becomes admin
- Option to disable password login entirely when OIDC is enabled

---

### 👤 Admin User Management

Administrators can now manage users through a dedicated admin panel:

**Features:**
- List all users with role and status information
- Create new users (with auto-generated passwords)
- Toggle admin role for users
- Activate/deactivate user accounts
- Delete users (with self-protection)

**Access:** Settings → Administration → User Management (admin-only)

**Note:** The first user created (via registration or OIDC) is automatically assigned admin privileges.

---

## 🔧 Technical Changes

### Backend
- **New Dependencies:** Authlib 1.3.2, requests 2.32.3
- **New Database Table:** `user_oidc_links` for OIDC identity mapping
- **New Column:** `users.is_admin` boolean flag
- **New Routes:**
  - `GET/POST /api/admin/users` - User management API
  - `DELETE/PATCH /api/admin/users/<id>` - Modify users
  - `GET /api/auth/oidc/config` - OIDC configuration
  - `GET /api/auth/oidc/login` - Initiate OIDC flow
  - `GET /api/auth/oidc/callback` - OIDC callback
- **New Decorator:** `@require_admin` for admin-only routes

### Frontend
- **New Component:** `UserManagement.svelte` - Admin user management UI
- **New View Type:** `user_management` added to view router
- **Updated:** `Login.svelte` with OIDC button and password-disable support
- **Updated:** `Settings.svelte` with admin panel link (admin-only)

### Database Migrations
- `f1a2b3c4d5e6_add_user_oidc_links_table.py` - OIDC support
- `a1b2c3d4e5f7_add_is_admin_to_users.py` - Admin support

---

## 🐛 Bug Fixes

### Passkey Authentication
- Fixed missing passkey login routes (405 error)
- Fixed `rp.id` detection to use request host as fallback
- Fixed frontend to pass username for passkey login

### OIDC Login
- Fixed missing OIDC routes in production builds
- Fixed first-user admin assignment for OIDC users

---

## 📝 Configuration Example

```bash
# Basic setup
docker run -d \
  --name snipsel \
  -p 5000:5000 \
  -v ./data:/app/data \
  -v ./uploads:/app/uploads \
  -e SNIPSEL_SECRET_KEY="your-secret" \
  -e SNIPSEL_DOMAIN="snipsel.example.com" \
  -e SNIPSEL_FRONTEND_URL="https://snipsel.example.com" \
  \
  # OIDC Configuration \
  -e SNIPSEL_OIDC_ENABLED=1 \
  -e SNIPSEL_OIDC_DISCOVERY_URL="https://sso.example.com/.well-known/openid-configuration" \
  -e SNIPSEL_OIDC_CLIENT_ID="your-client-id" \
  -e SNIPSEL_OIDC_CLIENT_SECRET="your-client-secret" \
  -e SNIPSEL_OIDC_PROVIDER_NAME="Company SSO" \
  -e SNIPSEL_OIDC_DISABLE_PASSWORD_LOGIN=1 \
  \
  # Security \
  -e SNIPSEL_REGISTRATION_ENABLED=0 \
  ghcr.io/mcfetz/snipsel:latest
```

---

## 🔄 Migration Guide

### For Existing Installations

1. **Pull latest image and run migrations:**
   ```bash
   docker pull ghcr.io/mcfetz/snipsel:latest
   docker stop snipsel
   docker run --rm -v ./data:/app/data ghcr.io/mcfetz/snipsel:latest flask --app snipsel_api.app db upgrade
   docker start snipsel
   ```

2. **Promote existing user to admin (if needed):**
   ```bash
   docker exec snipsel sqlite3 /app/data/snipsel.db "UPDATE users SET is_admin = 1 WHERE username = 'your-username';"
   ```

3. **Configure OIDC (optional):**
   Set the OIDC environment variables as shown above.

---

## 📚 Documentation Updates

- Updated README.md with OIDC configuration options
- Added admin user management to feature list
- Documented new environment variables
- Added security considerations for OIDC

---

## 🙏 Credits

Developed with assistance from [Sisyphus](https://github.com/code-yeongyu/oh-my-openagent) AI agent.

---

**Full Changelog:** Compare commits `26a7459..bc36656` on main branch
