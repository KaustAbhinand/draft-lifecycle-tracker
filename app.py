import json
import os
import threading
import time
from datetime import datetime, timedelta

from flask import Flask, request, jsonify
from flask_cors import CORS

from tools.draft_store import load_drafts, get_draft, save_drafts
from tools.draft_tools import create_draft as tool_create_draft, fetch_draft
from tools.conversion_tools import convert_draft, edit_converted_draft
from tools.reconciliation_tool import reconcile_draft
from tools.analytics_tools import generate_lifecycle_report
from tools.lifecycle_tools import expire_abandoned_drafts
from agents.lifecycle_agent import run_agent


app = Flask(__name__, static_folder="frontend", static_url_path="")
CORS(app)

MEMORY_FILE = "data/agent_memory.json"
EXPIRATION_HOURS = 24


# --------------------------------------------------
# Background expiry poller (runs every 60 seconds)
# --------------------------------------------------

def _expiry_poller():
    """Daemon thread that auto-expires abandoned OPEN drafts."""
    while True:
        try:
            result = expire_abandoned_drafts()
            if result["expired_count"] > 0:
                print(f"[Poller] Auto-expired {result['expired_count']} draft(s): {result['expired_drafts']}")
        except Exception as e:
            print(f"[Poller ERROR] {e}")
        time.sleep(60)


_poller_thread = threading.Thread(target=_expiry_poller, daemon=True)
_poller_thread.start()


# --------------------------------------------------
# Agent Memory helpers
# --------------------------------------------------

def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {"edits": [], "patterns": "No patterns learned yet."}
    with open(MEMORY_FILE, "r") as f:
        return json.load(f)


def save_memory(memory):
    os.makedirs("data", exist_ok=True)
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)


def summarize_patterns(edits):
    """Ask Groq to summarize edit patterns from accumulated diffs."""
    if not edits:
        return "No patterns learned yet."

    from llm.groq_agent import client

    diff_lines = []
    for e in edits[-20:]:  # last 20 edits
        for field, change in e.get("diff", {}).items():
            diff_lines.append(
                f"Field '{field}': proposed='{change.get('proposed','')}' → actual='{change.get('actual','')}'"
            )

    if not diff_lines:
        return "No field differences recorded yet."

    prompt = (
        "You are an AI learning assistant for an email draft system.\n"
        "Below are recent edits users made to email drafts (proposed vs actual).\n"
        "Summarize in 3-5 bullet points what patterns or preferences the user consistently shows.\n"
        "Be concise and specific.\n\n"
        + "\n".join(diff_lines)
    )

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


# --------------------------------------------------
# Serve frontend
# --------------------------------------------------

@app.route("/")
def index():
    return app.send_static_file("index.html")


# --------------------------------------------------
# API: Drafts
# --------------------------------------------------

@app.route("/api/drafts", methods=["GET"])
def api_list_drafts():
    drafts = load_drafts()
    return jsonify(list(drafts.values()))


@app.route("/api/drafts/<draft_id>", methods=["GET"])
def api_get_draft(draft_id):
    draft = get_draft(draft_id)
    if draft is None:
        return jsonify({"error": "Draft not found"}), 404
    return jsonify(draft)


@app.route("/api/drafts", methods=["POST"])
def api_create_draft():
    data = request.json
    result = tool_create_draft(
        to=data.get("to", ""),
        cc=data.get("cc", ""),
        subject=data.get("subject", ""),
        body=data.get("body", "")
    )
    return jsonify(result)


@app.route("/api/drafts/<draft_id>/convert", methods=["POST"])
def api_convert_draft(draft_id):
    data = request.json or {}
    result = convert_draft(draft_id, changes=data.get("changes"))

    # Reconcile immediately so status is set to CONVERTED / CONVERTED_EDITED
    if result.get("success"):
        reconciled = reconcile_draft(draft_id)
        if reconciled.get("success"):
            result["status"] = reconciled["status"]
            result["diff"] = reconciled.get("diff")

    return jsonify(result)



@app.route("/api/drafts/<draft_id>/edit", methods=["POST"])
def api_edit_draft(draft_id):
    data = request.json
    changes = data.get("changes", {})

    result = edit_converted_draft(draft_id, changes)

    if result.get("success"):
        # Record in agent memory
        memory = load_memory()
        memory["edits"].append({
            "draft_id": draft_id,
            "timestamp": datetime.now().isoformat(),
            "changes": changes,
            "diff": result.get("diff", {})
        })
        # Refresh learned patterns every 3 edits
        if len(memory["edits"]) % 3 == 0 or len(memory["edits"]) == 1:
            memory["patterns"] = summarize_patterns(memory["edits"])
        save_memory(memory)

    return jsonify(result)


@app.route("/api/drafts/<draft_id>/reconcile", methods=["POST"])
def api_reconcile_draft(draft_id):
    result = reconcile_draft(draft_id)
    return jsonify(result)


@app.route("/api/drafts/<draft_id>", methods=["DELETE"])
def api_delete_draft(draft_id):
    """Permanently delete a draft."""
    drafts = load_drafts()
    if draft_id not in drafts:
        return jsonify({"error": "Draft not found"}), 404
    del drafts[draft_id]
    save_drafts(drafts)
    return jsonify({"success": True, "deleted_id": draft_id})


@app.route("/api/drafts/expire-abandoned", methods=["POST"])
def api_expire_abandoned():
    """Manually trigger expiry check for all OPEN drafts."""
    result = expire_abandoned_drafts()
    return jsonify(result)


@app.route("/api/drafts/<draft_id>/expiry-info", methods=["GET"])
def api_expiry_info(draft_id):
    """Return expiry countdown info for an OPEN draft."""
    draft = get_draft(draft_id)
    if draft is None:
        return jsonify({"error": "Draft not found"}), 404
    if draft["status"] != "OPEN":
        return jsonify({"expires_in_seconds": None, "status": draft["status"]})

    created_at = datetime.fromisoformat(draft["created_at"])
    expires_at = created_at + timedelta(hours=EXPIRATION_HOURS)
    now = datetime.now()
    seconds_left = (expires_at - now).total_seconds()
    return jsonify({
        "expires_in_seconds": max(0, round(seconds_left)),
        "expires_at": expires_at.isoformat(),
        "is_expired": seconds_left <= 0
    })


# --------------------------------------------------
# API: Report
# --------------------------------------------------

@app.route("/api/report", methods=["GET"])
def api_report():
    report = generate_lifecycle_report()
    return jsonify(report)


# --------------------------------------------------
# API: Chat agent
# --------------------------------------------------

_conversation_history = []


@app.route("/api/chat", methods=["POST"])
def api_chat():
    global _conversation_history
    data = request.json
    user_message = data.get("message", "")

    result, _conversation_history = run_agent(
        user_message,
        _conversation_history
    )

    return jsonify({"reply": result})


# --------------------------------------------------
# API: Agent memory / learned patterns
# --------------------------------------------------

@app.route("/api/memory", methods=["GET"])
def api_memory():
    return jsonify(load_memory())


@app.route("/api/memory/refresh", methods=["POST"])
def api_memory_refresh():
    memory = load_memory()
    memory["patterns"] = summarize_patterns(memory["edits"])
    save_memory(memory)
    return jsonify({"patterns": memory["patterns"]})


# --------------------------------------------------
# Run
# --------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True, port=5000)
