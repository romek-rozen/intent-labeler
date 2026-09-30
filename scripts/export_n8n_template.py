"""Export the n8n template workflow and strip everything instance-specific.

Usage: N8N_API_KEY=... python scripts/export_n8n_template.py [base_url]
Writes every workflow in TEMPLATES to n8n-template/ with credential references reduced to generic
names (no IDs, no account names), no node IDs and no pinned data. Fails if a known personal
identifier is still in the file.
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = {"fOsP70JjwnJjHhPO": "intent-labeler-google-sheets.json",
             "TrPsqb5yieit1G00": "intent-labeler-webhook.json"}
BASE_URL = (sys.argv[1] if len(sys.argv) > 1 else "https://n8n.nimblio.work").rstrip("/")
CREDENTIAL_NAMES = {"httpBasicAuth": "DataForSEO", "dataForSeoApi": "DataForSEO API", "openRouterApi": "OpenRouter",
                    "googleSheetsOAuth2Api": "Google Sheets"}
# The public, view-only template sheet is the one ID allowed in the file (users copy it).
ALLOWED_SHEET = "1jgeI2wWxi5eD2d89ztmebuPbdXxdeBEOK-HXDM6FJJE"


def export(workflow_id: str, out: Path) -> None:
    request = urllib.request.Request(f"{BASE_URL}/api/v1/workflows/{workflow_id}",
                                     headers={"X-N8N-API-KEY": os.environ["N8N_API_KEY"]})
    with urllib.request.urlopen(request, timeout=60) as response:
        workflow = json.loads(response.read())
    for node in workflow["nodes"]:
        node.pop("id", None)
        node.pop("webhookId", None)
        if "credentials" in node:
            node["credentials"] = {key: {"id": "", "name": CREDENTIAL_NAMES.get(key, key)}
                                   for key in node["credentials"]}
    template = {"name": workflow["name"], "nodes": workflow["nodes"],
                "connections": workflow["connections"], "settings": {"executionOrder": "v1"},
                "pinData": {}, "meta": {"templateCredsSetupCompleted": False}}
    text = json.dumps(template, ensure_ascii=False, indent=2)
    sheets = set(re.findall(r"/d/([a-zA-Z0-9_-]{30,})", text)) - {ALLOWED_SHEET}
    if sheets or "@" in re.sub(r"https?://\S+", "", text).replace("@n8n", ""):
        raise SystemExit(f"personal identifiers left in the export: {sheets or 'an email address'}")
    out.write_text(text + "\n", encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)}: {len(template['nodes'])} nodes")


def main() -> None:
    for workflow_id, name in TEMPLATES.items():
        export(workflow_id, ROOT / "n8n-template" / name)


if __name__ == "__main__":
    main()
