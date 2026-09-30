"""Export the n8n template workflow and strip everything instance-specific.

Usage: N8N_API_KEY=... python scripts/export_n8n_template.py [workflow_id] [base_url]
Writes n8n-template/intent-labeler-google-sheets.json with credential references reduced to generic
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
OUT = ROOT / "n8n-template" / "intent-labeler-google-sheets.json"
WORKFLOW_ID = sys.argv[1] if len(sys.argv) > 1 else "fOsP70JjwnJjHhPO"
BASE_URL = (sys.argv[2] if len(sys.argv) > 2 else "https://n8n.nimblio.work").rstrip("/")
CREDENTIAL_NAMES = {"httpBasicAuth": "DataForSEO", "openRouterApi": "OpenRouter",
                    "googleSheetsOAuth2Api": "Google Sheets"}
# The public, view-only template sheet is the one ID allowed in the file (users copy it).
ALLOWED_SHEET = "1jgeI2wWxi5eD2d89ztmebuPbdXxdeBEOK-HXDM6FJJE"


def main() -> None:
    request = urllib.request.Request(f"{BASE_URL}/api/v1/workflows/{WORKFLOW_ID}",
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
    OUT.write_text(text + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(template['nodes'])} nodes")


if __name__ == "__main__":
    main()
