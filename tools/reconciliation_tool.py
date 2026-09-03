from tools.draft_store import (
    get_draft,
    update_draft
)

from tools.email_target import (
    get_email
)

from tools.diff_engine import (
    calculate_diff
)


def reconcile_draft(draft_id: str):

    draft = get_draft(draft_id)

    if draft is None:

        return {
            "success": False,
            "error": "Draft not found"
        }

    if draft["actual"] is None:

        return {
            "success": False,
            "error": "Draft has not been converted"
        }

    email_id = draft["actual"]["id"]

    actual = get_email(
        email_id
    )

    if actual is None:

        return {
            "success": False,
            "error": "Email object not found"
        }

    proposed = draft["proposed"]

    diff = calculate_diff(
        proposed,
        actual
    )

    if diff:

        status = "CONVERTED_EDITED"

    else:

        status = "CONVERTED"

    updated = update_draft(
        draft_id,
        {
            "actual": actual,
            "diff": diff,
            "status": status
        }
    )

    return {
        "success": True,
        "draft_id": draft_id,
        "status": status,
        "diff": diff,
        "actual": actual
    }