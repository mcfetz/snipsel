#!/usr/bin/env python3
"""Stoesst das Redeploy des Portainer-Stacks "snipsel" an (letzter Schritt der Pipeline).

Warum nicht der Portainer-Webhook: dieses Portainer (CE 2.45) legt fuer Stacks keinen Webhook
an. Der Stack-Update per API macht dasselbe: Datei aus dem Repo, `PullImage` an, Swarm zieht das
frisch gebaute Image.

Wichtig: die Stack-Umgebungsvariablen (Snipsel-Zugangsdaten, OIDC-Client, VAPID-Schluessel)
liegen in Portainer, nicht im Repo. Sie werden vor dem Update gelesen und unveraendert
zurueckgeschrieben — ein PUT mit leerer Env-Liste wuerde sie loeschen.

Erwartet PORTAINER_URL und PORTAINER_API_KEY in der Umgebung; fehlt eines, endet das Skript mit
Exit 0 und deutlicher Meldung — ein fehlendes Secret soll den Build nicht rot machen, aber auch
nicht als Deployment durchgehen.
"""

from __future__ import annotations

import json
import os
import pathlib
import sys
import urllib.error
import urllib.request

STACK_FILE = pathlib.Path(__file__).resolve().parent / "portainer-stack.yml"
STACK_NAME = os.environ.get("PORTAINER_STACK_NAME", "snipsel")
ENDPOINT_ID = os.environ.get("PORTAINER_ENDPOINT_ID", "3")


def api(
    url: str, key: str, path: str, payload: dict | None = None, method: str = "GET"
):
    request = urllib.request.Request(
        f"{url}/api{path}",
        data=json.dumps(payload).encode() if payload is not None else None,
        method=method,
        headers={"X-API-Key": key, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        body = response.read().decode()
    return response.status, (json.loads(body) if body.strip() else None)


def main() -> int:
    url = (os.environ.get("PORTAINER_URL") or "").rstrip("/")
    key = os.environ.get("PORTAINER_API_KEY") or ""
    if not url or not key:
        print(
            "!! PORTAINER_URL/PORTAINER_API_KEY fehlen — NICHT deployt, nur Image gebaut"
        )
        return 0

    status, stacks = api(url, key, f"/stacks?endpointId={ENDPOINT_ID}")
    if status != 200 or not isinstance(stacks, list):
        print(f"!! Stack-Liste nicht lesbar (HTTP {status}) — NICHT deployt")
        return 1
    stack = next((s for s in stacks if s.get("Name") == STACK_NAME), None)
    if stack is None:
        print(
            f"!! Stack '{STACK_NAME}' existiert in Portainer noch nicht — nur Image gebaut. "
            f"Einmalig anlegen, danach deployt die Pipeline automatisch."
        )
        return 0

    stack_id = stack["Id"]
    env = stack.get("Env") or []  # Werte in Portainer lassen, nicht ueberschreiben
    status, body = api(
        url,
        key,
        f"/stacks/{stack_id}?endpointId={ENDPOINT_ID}",
        {
            "StackFileContent": STACK_FILE.read_text(encoding="utf-8"),
            "Env": env,
            "Prune": False,
            "PullImage": True,
        },
        method="PUT",
    )
    name = (
        (body or {}).get("Name", STACK_NAME) if isinstance(body, dict) else STACK_NAME
    )
    print(
        f"Portainer-Redeploy: HTTP {status} fuer Stack '{name}' "
        f"(Endpoint {ENDPOINT_ID}, {len(env)} Env-Variablen erhalten, Image neu ziehen an)"
    )
    if status not in (200, 201):
        print(str(body)[:400])
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
