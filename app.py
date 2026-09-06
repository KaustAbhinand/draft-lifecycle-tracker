import json
import os
from datetime import datetime

from flask import Flask, request, jsonify
from flask_cors import CORS

from tools.draft_store import load_drafts, get_draft
from tools.draft_tools import create_draft as tool_create_draft, fetch_draft
from tools.conversion_tools import convert_draft, edit_converted_draft
from tools.reconciliation_tool import reconcile_draft
from tools.analytics_tools import generate_lifecycle_report
from agents.lifecycle_agent import run_agent


app = Flask(__name__, static_folder="frontend", static_url_path="")
CORS(app)

MEMORY_FILE = "data/agent_memory.json"


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
