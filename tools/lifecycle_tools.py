from datetime import datetime, timedelta

from tools.draft_store import (
    load_drafts,
    update_draft
)

from tools.reconciliation_tool import reconcile_draft

EXPIRATION_HOURS = 24


def expire_abandoned_drafts():

    drafts = load_drafts()

    expired = []

    now = datetime.now()

    for draft_id, draft in drafts.items():

        if draft["status"] != "OPEN":
            continue

        created_at = datetime.fromisoformat(
            draft["created_at"]
        )

        expiration_time = (
            created_at
            + timedelta(hours=EXPIRATION_HOURS)
        )

        if now >= expiration_time:

            update_draft(
                draft_id,
                {
                    "status": "EXPIRED",
                    "expired_at": now.isoformat()
                }
            )

            expired.append(draft_id)

    return {
        "expired_count": len(expired),
        "expired_drafts": expired
    }

# Poll the reconciliation tool depending on the status.
def poll_reconciliation():

    drafts = load_drafts()

    results = []

    for draft_id, draft in drafts.items():

        if draft["status"] not in {
            "CONVERTED",
            "CONVERTED_EDITED"
        }:
            continue

        result = reconcile_draft(
            draft_id
        )

        results.append(result)

    return results