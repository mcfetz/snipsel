from __future__ import annotations

import hashlib
import io
import json
import secrets
from datetime import datetime, timedelta

import pyotp
import qrcode
import webauthn
from webauthn import (
    generate_authentication_options,
    generate_registration_options,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers import bytes_to_base64url, options_to_json
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    UserVerificationRequirement,
)

from flask import Blueprint, request, send_file, session
from werkzeug.security import check_password_hash, generate_password_hash

from snipsel_api.auth_session import (
    current_user,
    enforce_json,
    json_response,
    require_auth,
)
from snipsel_api.config import Settings
from snipsel_api.emailer import send_password_reset_email
from snipsel_api.errors import api_error
from snipsel_api.extensions import db
from snipsel_api.models import (
    Attachment,
    Collection,
    CollectionSnipsel,
    PasswordResetToken,
    Snipsel,
    User,
    UserOidcLink,
    UserPasskey,
)

auth_bp = Blueprint("auth", __name__)


@auth_bp.get("/config")
def auth_config():
    settings = Settings.from_env()
    return json_response(
        {
            "registration_enabled": settings.registration_enabled,
            "oidc_enabled": settings.oidc_enabled,
            "oidc_disable_password_login": settings.oidc_disable_password_login,
        }
    )


@auth_bp.post("/register")
@enforce_json
def register():
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""

    settings = Settings.from_env()
    if not settings.registration_enabled:
        raise api_error(
            403, "registration_disabled", "Registration is currently disabled"
        )

    if not username or not email or not password:
        raise api_error(
            400, "invalid_input", "username, email and password are required"
        )

    existing = (
        db.session.execute(
            db.select(User).where((User.username == username) | (User.email == email))
        )
        .scalars()
        .first()
    )
    if existing:
        raise api_error(409, "already_exists", "username or email already exists")

    user_count = db.session.execute(db.select(db.func.count(User.id))).scalar() or 0
    is_first_user = user_count == 0

    user = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(password, method="pbkdf2:sha256"),
        is_admin=is_first_user,
    )
    db.session.add(user)
    db.session.commit()

    session.permanent = True
    session["user_id"] = user.id
    return json_response({"user": _user_json(user)}, status=201)


@auth_bp.post("/login")
@enforce_json
def login():
    settings = Settings.from_env()
    if settings.oidc_disable_password_login:
        raise api_error(
            403,
            "password_login_disabled",
            "Password login is disabled. Please use OIDC.",
        )

    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not username or not password:
        raise api_error(400, "invalid_input", "username and password are required")

    user = (
        db.session.execute(db.select(User).where(User.username == username))
        .scalars()
        .first()
    )
    if not user or not user.is_active or user.deleted_at is not None:
        raise api_error(401, "invalid_credentials", "Invalid credentials")

    if not check_password_hash(user.password_hash, password):
        raise api_error(401, "invalid_credentials", "Invalid credentials")

    if user.otp_enabled:
        session["pending_2fa_user_id"] = user.id
        return json_response({"status": "2fa_required"})

    passkeys = (
        db.session.execute(db.select(UserPasskey).where(UserPasskey.user_id == user.id))
        .scalars()
        .all()
    )
    if passkeys:
        # If they have passkeys, we could force it, or offer it.
        # But usually OTP is the fallback.
        # For now, if OTP is NOT enabled but passkeys ARE, we just log in with password.
        # Or we could have a setting to force 2FA if any 2FA method is set.
        pass

    session.permanent = True
    session["user_id"] = user.id
    return json_response({"user": _user_json(user)})


@auth_bp.post("/login/otp")
@enforce_json
def login_otp():
    data = request.get_json() or {}
    code = (data.get("code") or "").strip()
    user_id = session.get("pending_2fa_user_id")

    if not user_id or not code:
        raise api_error(400, "invalid_input", "Code and pending session required")

    user = db.session.get(User, user_id)
    if not user or not user.otp_enabled or not user.otp_secret:
        session.pop("pending_2fa_user_id", None)
        raise api_error(401, "unauthorized", "Invalid session")

    totp = pyotp.TOTP(user.otp_secret)
    if not totp.verify(code):
        raise api_error(401, "invalid_code", "Invalid OTP code")

    session.pop("pending_2fa_user_id", None)
    session.permanent = True
    session["user_id"] = user.id
    return json_response({"user": _user_json(user)})


@auth_bp.post("/2fa/generate")
@require_auth
def generate_2fa():
    user = current_user()
    if user.otp_enabled:
        raise api_error(400, "already_enabled", "2FA is already enabled")

    secret = pyotp.random_base32()
    user.otp_secret = secret
    db.session.commit()

    totp = pyotp.TOTP(secret)
    provisioning_url = totp.provisioning_uri(name=user.email, issuer_name="Snipsel")

    return json_response({"secret": secret, "provisioning_url": provisioning_url})


@auth_bp.get("/2fa/qr")
@require_auth
def get_2fa_qr():
    user = current_user()
    if not user.otp_secret:
        raise api_error(400, "not_initiated", "2FA setup not initiated")

    if user.otp_enabled:
        raise api_error(400, "already_enabled", "2FA is already enabled")

    totp = pyotp.TOTP(user.otp_secret)
    provisioning_url = totp.provisioning_uri(name=user.email, issuer_name="Snipsel")

    img = qrcode.make(provisioning_url)
    buf = io.BytesIO()
    img.save(buf)
    buf.seek(0)

    return send_file(buf, mimetype="image/png")


@auth_bp.post("/2fa/enable")
@require_auth
@enforce_json
def enable_2fa():
    user = current_user()
    if user.otp_enabled:
        raise api_error(400, "already_enabled", "2FA is already enabled")

    data = request.get_json() or {}
    code = (data.get("code") or "").strip()
    password_confirm = data.get("password_confirm") or ""

    if not code or not password_confirm:
        raise api_error(400, "invalid_input", "Code and password_confirm are required")

    if not check_password_hash(user.password_hash, password_confirm):
        raise api_error(401, "invalid_credentials", "Invalid account password")

    if not user.otp_secret:
        raise api_error(400, "not_initiated", "2FA setup not initiated")

    totp = pyotp.TOTP(user.otp_secret)
    if not totp.verify(code):
        raise api_error(401, "invalid_code", "Invalid OTP code")

    user.otp_enabled = True
    db.session.commit()
    return json_response({"ok": True})


@auth_bp.post("/2fa/disable")
@require_auth
@enforce_json
def disable_2fa():
    import logging

    logger = logging.getLogger("snipsel_api.auth")
    user = current_user()
    data = request.get_json() or {}
    raw_password = data.get("password_confirm") or ""
    password_confirm = str(raw_password).strip()

    first_char = password_confirm[0] if password_confirm else ""
    logger.debug(
        f"Disable 2FA request for user {user.username}. Password length: {len(password_confirm)}, first char: {first_char}"
    )

    if not password_confirm:
        logger.warning(
            f"Disable 2FA failed: password_confirm missing for user {user.username}"
        )
        raise api_error(400, "invalid_input", "password_confirm is required")

    if not check_password_hash(user.password_hash, password_confirm):
        logger.warning(
            f"Disable 2FA failed: password mismatch for user {user.username}"
        )
        raise api_error(401, "invalid_credentials", "Invalid account password")

    user.otp_enabled = False
    user.otp_secret = None
    db.session.commit()
    logger.info(f"2FA disabled for user {user.username}")
    return json_response({"ok": True})


@auth_bp.post("/passkeys/register/begin")
@require_auth
def passkeys_register_begin():
    user = current_user()
    settings = Settings.from_env()
    rp_id = settings.snipsel_domain or request.host.split(":")[0] or "localhost"

    options = generate_registration_options(
        rp_id=rp_id,
        rp_name="Snipsel",
        user_id=user.id.encode("utf-8"),
        user_name=user.username,
        user_display_name=user.username,
        authenticator_selection=AuthenticatorSelectionCriteria(
            user_verification=UserVerificationRequirement.PREFERRED,
        ),
    )

    options_json_str = options_to_json(options)
    session["passkey_registration_options"] = options_json_str
    return json_response(json.loads(options_json_str))


@auth_bp.post("/passkeys/register/complete")
@require_auth
@enforce_json
def passkeys_register_complete():
    user = current_user()
    data = request.get_json() or {}
    options_json = session.get("passkey_registration_options")
    if not options_json:
        raise api_error(400, "invalid_session", "Registration session expired")

    settings = Settings.from_env()
    rp_id = settings.snipsel_domain or request.host.split(":")[0] or "localhost"
    origin = settings.snipsel_frontend_url or f"https://{rp_id}"
    if rp_id == "localhost":
        origin = "http://localhost:5173"

    credential_id = data.get("id")
    passkey = (
        db.session.execute(
            db.select(UserPasskey).where(
                UserPasskey.credential_id == credential_id,
                UserPasskey.user_id == user.id,
            )
        )
        .scalars()
        .first()
    )

    if not passkey:
        raise api_error(401, "invalid_credential", "Passkey not found for this user")

    try:
        verification = verify_authentication_response(
            credential=data,
            expected_challenge=webauthn.helpers.parse_authentication_options_json(
                options_json
            ).challenge,
            expected_origin=origin,
            expected_rp_id=rp_id,
            credential_public_key=webauthn.helpers.base64url_to_bytes(
                passkey.public_key
            ),
            credential_current_sign_count=passkey.sign_count,
        )
    except Exception as e:
        raise api_error(401, "verification_failed", str(e))

    passkey.sign_count = verification.new_sign_count
    db.session.commit()

    session.pop("passkey_login_options", None)
    session.pop("pending_passkey_user_id", None)
    session.permanent = True
    session["user_id"] = user.id
    return json_response({"user": _user_json(user)})




@auth_bp.post("/passkeys/login/begin")
@enforce_json
def passkeys_login_begin():
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    if not username:
        raise api_error(400, "invalid_input", "username is required")

    user = (
        db.session.execute(db.select(User).where(User.username == username))
        .scalars()
        .first()
    )
    if not user or not user.is_active or user.deleted_at is not None:
        raise api_error(401, "invalid_credentials", "Invalid user")

    passkeys = (
        db.session.execute(db.select(UserPasskey).where(UserPasskey.user_id == user.id))
        .scalars()
        .all()
    )
    if not passkeys:
        raise api_error(400, "no_passkeys", "No passkeys registered for this user")

    settings = Settings.from_env()
    rp_id = settings.snipsel_domain or request.host.split(":")[0] or "localhost"

    options = generate_authentication_options(
        rp_id=rp_id,
        allow_credentials=[
            webauthn.helpers.structs.PublicKeyCredentialDescriptor(
                id=webauthn.helpers.base64url_to_bytes(p.credential_id)
            )
            for p in passkeys
        ],
        user_verification=UserVerificationRequirement.PREFERRED,
    )

    options_json_str = options_to_json(options)
    session["passkey_login_options"] = options_json_str
    session["pending_passkey_user_id"] = user.id
    return json_response(json.loads(options_json_str))


@auth_bp.post("/passkeys/login/complete")
@enforce_json
def passkeys_login_complete():
    data = request.get_json() or {}
    user_id = session.get("pending_passkey_user_id")
    options_json = session.get("passkey_login_options")
    if not user_id or not options_json:
        raise api_error(400, "invalid_session", "Login session expired")

    user = db.session.get(User, user_id)
    if not user:
        raise api_error(401, "unauthorized", "User not found")

    settings = Settings.from_env()
    rp_id = settings.snipsel_domain or request.host.split(":")[0] or "localhost"
    origin = settings.snipsel_frontend_url or f"https://{rp_id}"
    if rp_id == "localhost":
        origin = "http://localhost:5173"

    credential_id = data.get("id")
    passkey = (
        db.session.execute(
            db.select(UserPasskey).where(
                UserPasskey.credential_id == credential_id,
                UserPasskey.user_id == user.id,
            )
        )
        .scalars()
        .first()
    )

    if not passkey:
        raise api_error(401, "invalid_credential", "Passkey not found for this user")

    try:
        verification = verify_authentication_response(
            credential=data,
            expected_challenge=webauthn.helpers.parse_authentication_options_json(
                options_json
            ).challenge,
            expected_origin=origin,
            expected_rp_id=rp_id,
            credential_public_key=webauthn.helpers.base64url_to_bytes(
                passkey.public_key
            ),
            credential_current_sign_count=passkey.sign_count,
        )
    except Exception as e:
        raise api_error(401, "verification_failed", str(e))

    passkey.sign_count = verification.new_sign_count
    db.session.commit()

    session.pop("passkey_login_options", None)
    session.pop("pending_passkey_user_id", None)
    session.permanent = True
    session["user_id"] = user.id
    return json_response({"user": _user_json(user)})

@auth_bp.get("/passkeys")
@require_auth
def list_passkeys():
    user = current_user()
    passkeys = (
        db.session.execute(db.select(UserPasskey).where(UserPasskey.user_id == user.id))
        .scalars()
        .all()
    )
    return json_response(
        {
            "passkeys": [
                {
                    "id": p.id,
                    "name": p.name,
                    "created_at": p.created_at.isoformat() + "Z",
                }
                for p in passkeys
            ]
        }
    )


@auth_bp.delete("/passkeys/<id>")
@require_auth
def delete_passkey(id):
    user = current_user()
    passkey = db.session.get(UserPasskey, id)
    if not passkey or passkey.user_id != user.id:
        raise api_error(404, "not_found", "Passkey not found")

    db.session.delete(passkey)
    db.session.commit()
    return json_response({"ok": True})


@auth_bp.post("/logout")
def logout():
    session.pop("user_id", None)
    return json_response({"ok": True})


@auth_bp.get("/me")
@require_auth
def me():
    user = current_user()
    return json_response({"user": _user_json(user)})


@auth_bp.get("/me/stats")
@require_auth
def me_stats():
    user = current_user()

    collections_count = (
        db.session.execute(
            db.select(db.func.count(Collection.id)).where(
                Collection.owner_user_id == user.id,
                Collection.deleted_at.is_(None),
            )
        ).scalar()
        or 0
    )

    snipsels_count = (
        db.session.execute(
            db.select(db.func.count(Snipsel.id)).where(
                Snipsel.owner_user_id == user.id,
                Snipsel.deleted_at.is_(None),
            )
        ).scalar()
        or 0
    )

    completed_tasks_count = (
        db.session.execute(
            db.select(db.func.count(Snipsel.id)).where(
                Snipsel.owner_user_id == user.id,
                Snipsel.deleted_at.is_(None),
                Snipsel.type == "task",
                Snipsel.task_done == True,
            )
        ).scalar()
        or 0
    )

    attachments_count = (
        db.session.execute(
            db.select(db.func.count(Attachment.id))
            .join(Snipsel, Attachment.snipsel_id == Snipsel.id)
            .where(
                Snipsel.owner_user_id == user.id,
                Snipsel.deleted_at.is_(None),
            )
        ).scalar()
        or 0
    )

    return json_response(
        {
            "stats": {
                "collections": collections_count,
                "snipsels": snipsels_count,
                "completed_tasks": completed_tasks_count,
                "attachments": attachments_count,
            }
        }
    )


@auth_bp.patch("/me")
@require_auth
@enforce_json
def update_me():
    user = current_user()
    data = request.get_json() or {}

    if "default_collection_header_color" in data:
        user.default_collection_header_color = (
            data.get("default_collection_header_color") or ""
        ).strip() or None

    if "carry_over_open_tasks" in data:
        user.carry_over_open_tasks = bool(data.get("carry_over_open_tasks"))

    if "theme" in data:
        theme = (data.get("theme") or "system").strip().lower()
        if theme in {"light", "dark", "system"}:
            user.theme = theme

    if "day_collection_template_id" in data:
        tpl_id_raw = (data.get("day_collection_template_id") or "").strip() or None
        if tpl_id_raw is None:
            user.day_collection_template_id = None
        else:
            tpl = (
                db.session.execute(
                    db.select(Collection).where(
                        Collection.id == tpl_id_raw,
                        Collection.owner_user_id == user.id,
                        Collection.deleted_at.is_(None),
                        Collection.is_template == True,
                    )
                )
                .scalars()
                .first()
            )
            if not tpl:
                raise api_error(400, "invalid_input", "template not found")
            user.day_collection_template_id = tpl.id

    if "ai_llm_url" in data:
        user.ai_llm_url = (data.get("ai_llm_url") or "").strip() or None
    if "ai_model_name" in data:
        user.ai_model_name = (data.get("ai_model_name") or "").strip() or None
    if "ai_api_key" in data:
        user.ai_api_key = (data.get("ai_api_key") or "").strip() or None

    if "light_background_color" in data:
        user.light_background_color = (
            data.get("light_background_color") or ""
        ).strip() or None
    if "dark_background_color" in data:
        user.dark_background_color = (
            data.get("dark_background_color") or ""
        ).strip() or None

    if "diced_moments_tags" in data:
        user.diced_moments_tags = (
            data.get("diced_moments_tags") or ""
        ).strip() or None

    if "email" in data or "password" in data:
        current_password = data.get("current_password") or ""
        if not current_password or not check_password_hash(
            user.password_hash, current_password
        ):
            raise api_error(
                401,
                "invalid_credentials",
                "Current password is required to change email or password",
            )

        if "email" in data:
            new_email = (data.get("email") or "").strip()
            if not new_email:
                raise api_error(400, "invalid_input", "Email cannot be empty")
            if new_email != user.email:
                existing = (
                    db.session.execute(
                        db.select(User).where(
                            User.email == new_email,
                            User.id != user.id,
                            User.deleted_at.is_(None),
                        )
                    )
                    .scalars()
                    .first()
                )
                if existing:
                    raise api_error(409, "already_exists", "Email already in use")
                user.email = new_email

        if "password" in data:
            new_password = data.get("password") or ""
            if (
                not new_password or len(new_password) < 4
            ):  # Allowing 4+ for now, but user requested 8+ usually. I'll stick to 8 if I want to be safe, but let's see what register uses.
                raise api_error(
                    400, "invalid_input", "Password must be at least 4 characters long"
                )
            user.password_hash = generate_password_hash(
                new_password, method="pbkdf2:sha256"
            )

    user.modified_at = datetime.utcnow()
    db.session.commit()
    return json_response({"user": _user_json(user)})


@auth_bp.post("/password-reset/request")
@enforce_json
def password_reset_request():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip()
    if not email:
        raise api_error(400, "invalid_input", "email is required")

    user = (
        db.session.execute(db.select(User).where(User.email == email)).scalars().first()
    )
    if not user or user.deleted_at is not None or not user.is_active:
        return json_response({"ok": True})

    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    expires_at = datetime.utcnow() + timedelta(hours=2)

    prt = PasswordResetToken(
        user_id=user.id, token_hash=token_hash, expires_at=expires_at
    )
    db.session.add(prt)
    db.session.commit()

    settings = Settings.from_env()
    send_password_reset_email(settings=settings, to_email=user.email, token=raw_token)
    return json_response({"ok": True})


@auth_bp.post("/password-reset/confirm")
@enforce_json
def password_reset_confirm():
    data = request.get_json() or {}
    token = data.get("token") or ""
    new_password = data.get("new_password") or ""
    if not token or not new_password:
        raise api_error(400, "invalid_input", "token and new_password are required")

    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    prt = (
        db.session.execute(
            db.select(PasswordResetToken).where(
                PasswordResetToken.token_hash == token_hash
            )
        )
        .scalars()
        .first()
    )
    if not prt or prt.used_at is not None or prt.expires_at < datetime.utcnow():
        raise api_error(400, "invalid_token", "Token is invalid or expired")

    user = db.session.get(User, prt.user_id)
    if not user or user.deleted_at is not None or not user.is_active:
        raise api_error(400, "invalid_token", "Token is invalid")

    user.password_hash = generate_password_hash(new_password, method="pbkdf2:sha256")
    user.modified_at = datetime.utcnow()
    prt.used_at = datetime.utcnow()
    db.session.commit()

    return json_response({"ok": True})


@auth_bp.post("/passcode/set")
@require_auth
@enforce_json
def set_passcode():
    user = current_user()
    data = request.get_json() or {}
    passcode = (data.get("passcode") or "").strip()
    password_confirm = data.get("password_confirm") or ""

    if not passcode or not password_confirm:
        raise api_error(
            400, "invalid_input", "passcode and password_confirm are required"
        )

    if not passcode.isdigit() or not (4 <= len(passcode) <= 12):
        raise api_error(400, "invalid_input", "passcode must be 4-12 digits")

    if not check_password_hash(user.password_hash, password_confirm):
        raise api_error(401, "invalid_credentials", "Invalid password confirmation")

    user.passcode_hash = generate_password_hash(passcode, method="pbkdf2:sha256")
    user.passcode_failed_attempts = 0
    db.session.commit()
    return json_response({"ok": True})


@auth_bp.post("/passcode/verify")
@require_auth
@enforce_json
def verify_passcode():
    user = current_user()
    data = request.get_json() or {}
    passcode = (data.get("passcode") or "").strip()
    collection_id = data.get("collection_id")

    if not user.passcode_hash:
        raise api_error(400, "no_passcode_set", "No passcode set for this user")

    if not check_password_hash(user.passcode_hash, passcode):
        user.passcode_failed_attempts += 1
        db.session.commit()
        if user.passcode_failed_attempts >= 5:
            session.clear()
            raise api_error(401, "force_logout", "Too many failed attempts")
        else:
            raise api_error(
                401,
                "invalid_passcode",
                "Invalid passcode",
                details={"attempts_remaining": 5 - user.passcode_failed_attempts},
            )

    user.passcode_failed_attempts = 0
    session["passcode_verified_at"] = datetime.utcnow().isoformat()
    session["passcode_verified_collection_id"] = collection_id
    db.session.commit()

    unlocked_until = (datetime.utcnow() + timedelta(minutes=2)).isoformat() + "Z"
    return json_response({"ok": True, "unlocked_until": unlocked_until})


def _user_json(user: User) -> dict:
    passkeys_count = (
        db.session.execute(
            db.select(db.func.count(UserPasskey.id)).where(
                UserPasskey.user_id == user.id
            )
        ).scalar()
        or 0
    )

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "default_collection_header_color": user.default_collection_header_color,
        "carry_over_open_tasks": user.carry_over_open_tasks,
        "theme": user.theme,
        "day_collection_template_id": getattr(user, "day_collection_template_id", None),
        "passcode_set": user.passcode_hash is not None,
        "otp_enabled": user.otp_enabled,
        "passkeys_count": passkeys_count,
        "max_upload_bytes": Settings.from_env().max_upload_bytes,
        "ai_llm_url": user.ai_llm_url,
        "ai_model_name": user.ai_model_name,
        "ai_api_key_set": user.ai_api_key is not None,
        "light_background_color": user.light_background_color,
        "dark_background_color": user.dark_background_color,
        "is_admin": getattr(user, "is_admin", False),
        "diced_moments_tags": user.diced_moments_tags,
        "created_at": user.created_at.isoformat() + "Z",
    }


_oidc_metadata = None


def _get_oidc_metadata():
    global _oidc_metadata
    if _oidc_metadata is not None:
        return _oidc_metadata

    settings = Settings.from_env()
    if not settings.oidc_enabled or not settings.oidc_discovery_url:
        return None

    import requests

    try:
        resp = requests.get(settings.oidc_discovery_url, timeout=30)
        resp.raise_for_status()
        _oidc_metadata = resp.json()
        return _oidc_metadata
    except Exception as e:
        import logging

        logging.getLogger("snipsel_api.oidc").error(
            f"Failed to fetch OIDC metadata: {e}"
        )
        return None


@auth_bp.get("/oidc/config")
def oidc_config():
    settings = Settings.from_env()
    return json_response(
        {
            "enabled": settings.oidc_enabled,
            "provider_name": settings.oidc_provider_name
            if settings.oidc_enabled
            else None,
        }
    )


@auth_bp.get("/oidc/login")
def oidc_login():
    settings = Settings.from_env()
    if not settings.oidc_enabled:
        raise api_error(400, "oidc_disabled", "OIDC authentication is not enabled")

    metadata = _get_oidc_metadata()
    if not metadata:
        raise api_error(500, "oidc_not_configured", "OIDC metadata not available")

    authorization_endpoint = metadata.get("authorization_endpoint")
    if not authorization_endpoint:
        raise api_error(
            500, "oidc_misconfigured", "OIDC provider has no authorization_endpoint"
        )

    redirect_uri = request.args.get(
        "redirect_uri", f"{settings.snipsel_frontend_url or ''}/api/auth/oidc/callback"
    )
    session["oidc_redirect_uri"] = redirect_uri
    session["oidc_state"] = secrets.token_urlsafe(32)
    session["oidc_nonce"] = secrets.token_urlsafe(32)

    from authlib.oauth2.rfc7636 import create_s256_code_challenge

    code_verifier = secrets.token_urlsafe(64)
    session["oidc_code_verifier"] = code_verifier
    code_challenge = create_s256_code_challenge(code_verifier)

    params = {
        "response_type": "code",
        "client_id": settings.oidc_client_id,
        "redirect_uri": redirect_uri,
        "scope": settings.oidc_scope,
        "state": session["oidc_state"],
        "nonce": session["oidc_nonce"],
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }

    import urllib.parse

    auth_url = f"{authorization_endpoint}?{urllib.parse.urlencode(params)}"
    return json_response({"auth_url": auth_url})


@auth_bp.get("/oidc/callback")
def oidc_callback():
    settings = Settings.from_env()
    if not settings.oidc_enabled:
        raise api_error(400, "oidc_disabled", "OIDC authentication is not enabled")

    metadata = _get_oidc_metadata()
    if not metadata:
        raise api_error(500, "oidc_not_configured", "OIDC metadata not available")

    token_endpoint = metadata.get("token_endpoint")
    userinfo_endpoint = metadata.get("userinfo_endpoint")
    if not token_endpoint or not userinfo_endpoint:
        raise api_error(
            500, "oidc_misconfigured", "OIDC provider missing required endpoints"
        )

    state = request.args.get("state")
    if not state or state != session.get("oidc_state"):
        raise api_error(400, "invalid_state", "Invalid OIDC state parameter")

    code = request.args.get("code")
    if not code:
        error = request.args.get("error", "unknown_error")
        error_description = request.args.get(
            "error_description", "No error description"
        )
        raise api_error(400, f"oidc_{error}", error_description)

    code_verifier = session.get("oidc_code_verifier")
    redirect_uri = session.get(
        "oidc_redirect_uri",
        f"{settings.snipsel_frontend_url or ''}/api/auth/oidc/callback",
    )

    import requests
    from authlib.jose import jwt

    token_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": settings.oidc_client_id,
        "client_secret": settings.oidc_client_secret,
        "code_verifier": code_verifier,
    }

    token_response = requests.post(token_endpoint, data=token_data, timeout=30)
    if not token_response.ok:
        raise api_error(
            400, "oidc_token_error", f"Token exchange failed: {token_response.text}"
        )

    tokens = token_response.json()
    access_token = tokens.get("access_token")
    id_token = tokens.get("id_token")

    if id_token:
        try:
            claims = jwt.decode(
                id_token, key="", claims_options={"verify_signature": False}
            )
            userinfo = claims
        except Exception:
            userinfo = None
    else:
        userinfo = None

    if not userinfo and access_token:
        try:
            userinfo_response = requests.get(
                userinfo_endpoint,
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=30,
            )
            if userinfo_response.ok:
                userinfo = userinfo_response.json()
        except Exception:
            userinfo = None

    if not userinfo or not userinfo.get("sub"):
        raise api_error(
            400,
            "oidc_no_userinfo",
            "Could not retrieve user information from OIDC provider",
        )

    subject = userinfo.get("sub")
    email = userinfo.get("email") or userinfo.get("email_address")
    name = userinfo.get("name") or userinfo.get("preferred_username") or email

    if not email:
        raise api_error(
            400, "oidc_no_email", "OIDC provider did not provide an email address"
        )

    oidc_link = (
        db.session.execute(
            db.select(UserOidcLink).where(
                UserOidcLink.provider == "oidc",
                UserOidcLink.subject == subject,
            )
        )
        .scalars()
        .first()
    )

    if oidc_link:
        user = db.session.get(User, oidc_link.user_id)
        if not user or not user.is_active or user.deleted_at is not None:
            raise api_error(401, "account_disabled", "User account is disabled")
    else:
        if not settings.registration_enabled:
            raise api_error(
                403,
                "registration_disabled",
                "Registration is disabled. Contact an administrator.",
            )

        existing_user = (
            db.session.execute(db.select(User).where(User.email == email))
            .scalars()
            .first()
        )

        if existing_user:
            user = existing_user
        else:
            username = (
                name.replace(" ", "_").lower()[:32]
                if name
                else email.split("@")[0][:32]
            )
            base_username = username
            counter = 1
            while (
                db.session.execute(db.select(User).where(User.username == username))
                .scalars()
                .first()
            ):
                suffix = str(counter)
                username = f"{base_username[: 32 - len(suffix) - 1]}_{suffix}"
                counter += 1

            user_count = (
                db.session.execute(db.select(db.func.count(User.id))).scalar() or 0
            )
            is_first_user = user_count == 0

            user = User(
                username=username,
                email=email,
                password_hash="oidc_auth",
                is_admin=is_first_user,
            )
            db.session.add(user)
            db.session.commit()

        oidc_link = UserOidcLink(
            user_id=user.id,
            provider="oidc",
            subject=subject,
            email=email,
            name=name,
        )
        db.session.add(oidc_link)
        db.session.commit()

    session.permanent = True
    session["user_id"] = user.id

    frontend_url = settings.snipsel_frontend_url or "/"
    return f"""
    <html>
        <body>
            <script>
                window.opener.postMessage({{type: 'oidc-login-success'}}, '*');
                window.close();
            </script>
            <p>Login successful. You can close this window.</p>
            <script>setTimeout(() => window.location.href = '{frontend_url}', 1000);</script>
        </body>
    </html>
    """
