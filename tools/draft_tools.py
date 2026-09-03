# Tools to create and fetch email drafts

import uuid

from models import Draft
from tools.draft_store import (
    save_draft,
    get_draft
)


def create_draft(
    to: str,
    cc: str,
    subject: str,
    body: str
):

    draft = Draft(
        id=str(uuid.uuid4()),
        proposed={
            "to": to,
            "cc": cc,
            "subject": subject,
            "body": body
        }
    )

    save_draft(draft)

    return {
        "success": True,
        "draft_id": draft.id,
        "status": draft.status,
        "proposed": draft.proposed
    }


def fetch_draft(draft_id: str):

    draft = get_draft(draft_id)

    if draft is None:

        return {
            "success": False,
            "error": "Draft not found"
        }

    return {
        "success": True,
        "draft": draft
    }