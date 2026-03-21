from __future__ import annotations

import base64
import json
from pathlib import Path
from urllib import request as urllib_request
from urllib.error import URLError, HTTPError

from flask import Blueprint, request, current_app
from snipsel_api.auth_session import json_response, require_auth, current_user
from snipsel_api.errors import api_error
from snipsel_api.extensions import db
from snipsel_api.models import Attachment
from snipsel_api.permissions import can_read_snipsel_via_collections

ai_bp = Blueprint("ai", __name__)


@ai_bp.post("/generate")
@require_auth
def generate():
    user = current_user()
    if not user.ai_llm_url or not user.ai_api_key:
        raise api_error(
            400, "ai_not_configured", "AI settings are not fully configured"
        )

    data = request.get_json() or {}
    prompt = data.get("prompt")
    context = data.get("context", "")
    attachment_ids = data.get("attachment_ids", [])

    if not prompt:
        raise api_error(400, "invalid_input", "Prompt is required")

    model = user.ai_model_name or "gpt-3.5-turbo"

    # Message content can be a string or a list of parts (for vision)
    message_content = []

    # 1. Add text context
    text_content = f"Context/Note content:\n{context}"
    message_content.append(
        {"type": "text", "text": f"{text_content}\n\nTask: {prompt}"}
    )

    # 2. Add attachments
    if attachment_ids:
        # Import the helper from routes_attachments to avoid duplication
        from snipsel_api.routes_attachments import _resolve_attachment_path

        attachments = (
            db.session.execute(
                db.select(Attachment).where(Attachment.id.in_(attachment_ids))
            )
            .scalars()
            .all()
        )

        for att in attachments:
            # Verify permission: either owner OR can read the snipsel it belongs to
            is_authorized = False
            if att.created_by_id == user.id:
                is_authorized = True
            elif att.snipsel_id and can_read_snipsel_via_collections(
                user.id, att.snipsel_id
            ):
                is_authorized = True

            if not is_authorized:
                continue

            # Only handle images for now
            if att.mime_type and att.mime_type.startswith("image/"):
                path = _resolve_attachment_path(att)
                if path and path.exists():
                    try:
                        with open(path, "rb") as f:
                            encoded_image = base64.b64encode(f.read()).decode("utf-8")
                            message_content.append(
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:{att.mime_type};base64,{encoded_image}"
                                    },
                                }
                            )
                    except Exception as e:
                        print(f"Error encoding image attachment {att.id}: {e}")
            else:
                if att.size_bytes < 500000:
                    path = _resolve_attachment_path(att)
                    if path and path.exists():
                        try:
                            with open(
                                path, "r", encoding="utf-8", errors="ignore"
                            ) as f:
                                message_content.append(
                                    {
                                        "type": "text",
                                        "text": f"Attachment Content ({att.filename}):\n{f.read()}",
                                    }
                                )
                        except:
                            pass

    # OpenAI compatible payload
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant integrated into a note-taking app called Snipsel. Help the user with their notes. You can see images and contents of files attached to the notes.",
            },
            {"role": "user", "content": message_content},
        ],
    }

    try:
        req = urllib_request.Request(
            user.ai_llm_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {user.ai_api_key}",
            },
            method="POST",
        )
        with urllib_request.urlopen(req, timeout=30) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            # Expecting OpenAI format
            if "choices" in res_data and len(res_data["choices"]) > 0:
                ai_text = res_data["choices"][0]["message"]["content"]
                return json_response({"text": ai_text})
            else:
                return json_response(
                    {
                        "error": "Unexpected response format from LLM",
                        "details": res_data,
                    },
                    status=502,
                )

    except HTTPError as e:
        error_body = e.read().decode("utf-8")
        try:
            error_json = json.loads(error_body)
            return json_response(
                {"error": f"LLM Error: {e.code}", "details": error_json}, status=e.code
            )
        except:
            return json_response(
                {"error": f"LLM Error: {e.code}", "details": error_body}, status=e.code
            )
    except URLError as e:
        raise api_error(502, "external_error", f"Failed to connect to LLM: {str(e)}")
    except Exception as e:
        raise api_error(500, "internal_error", str(e))


@ai_bp.get("/models")
@require_auth
def get_models():
    user = current_user()
    if not user.ai_llm_url or not user.ai_api_key:
        raise api_error(
            400, "ai_not_configured", "AI settings are not fully configured"
        )

    # Derive the models endpoint from the chat completions URL
    # OpenAI compatible APIs usually have /v1/chat/completions and /v1/models
    models_url = user.ai_llm_url.replace("/chat/completions", "/models")

    try:
        req = urllib_request.Request(
            models_url,
            headers={
                "Authorization": f"Bearer {user.ai_api_key}",
            },
            method="GET",
        )
        with urllib_request.urlopen(req, timeout=10) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            # OpenAI format: { "data": [{ "id": "model-name", ... }, ...] }
            models = []
            if "data" in res_data and isinstance(res_data["data"], list):
                for model in res_data["data"]:
                    if "id" in model:
                        models.append(
                            {
                                "id": model["id"],
                                "name": model.get("name", model["id"]),
                            }
                        )
            return json_response({"models": models})

    except HTTPError as e:
        error_body = e.read().decode("utf-8")
        try:
            error_json = json.loads(error_body)
            return json_response(
                {"error": f"LLM Error: {e.code}", "details": error_json}, status=e.code
            )
        except:
            return json_response(
                {"error": f"LLM Error: {e.code}", "details": error_body}, status=e.code
            )
    except URLError as e:
        raise api_error(502, "external_error", f"Failed to connect to LLM: {str(e)}")
    except Exception as e:
        raise api_error(500, "internal_error", str(e))
