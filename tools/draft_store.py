import json
import os


DATA_FILE = "data/drafts.json"


def load_drafts():

    if not os.path.exists(DATA_FILE):
        return {}

    with open(DATA_FILE, "r") as file:
        return json.load(file)


def save_drafts(drafts):

    os.makedirs("data", exist_ok=True)

    with open(DATA_FILE, "w") as file:
        json.dump(
            drafts,
            file,
            indent=2
        )


def save_draft(draft):

    drafts = load_drafts()

    drafts[draft.id] = {
        "id": draft.id,
        "proposed": draft.proposed,
        "actual": draft.actual,
        "status": draft.status,
        "diff": draft.diff,
        "created_at": draft.created_at,
        "converted_at": draft.converted_at
    }

    save_drafts(drafts)


def get_draft(draft_id):

    drafts = load_drafts()

    return drafts.get(draft_id)


def update_draft(draft_id, updates):

    drafts = load_drafts()

    if draft_id not in drafts:

        raise ValueError(
            f"Draft {draft_id} not found"
        )

    drafts[draft_id].update(updates)

    save_drafts(drafts)

    return drafts[draft_id]