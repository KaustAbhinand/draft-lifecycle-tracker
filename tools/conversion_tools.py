from datetime import datetime

from tools.draft_store import (
    get_draft,
    update_draft
)

from tools.email_target import (
    create_email,
    edit_email
)


# Fields that can be changed on an email.
EDITABLE_FIELDS = {
    "to",
    "cc",
    "subject",
    "body"
}


def convert_draft(
    draft_id: str,
    changes: dict | None = None
):

    draft = get_draft(draft_id)

    if draft is None:

        return {
            "success": False,
            "error": "Draft not found"
        }

    if draft["status"] != "OPEN":

        return {
            "success": False,
            "error": (
                f"Draft is already "
                f"{draft['status']}"
            )
        }

    proposed = draft["proposed"]

    # ------------------------------------------
    # Create actual email from proposal
    # ------------------------------------------

    actual_to_create = proposed.copy()

    # ------------------------------------------
    # Apply conversion-time changes
    # ------------------------------------------

    if changes:

        for field, value in changes.items():

            if field not in EDITABLE_FIELDS:

                return {
                    "success": False,
                    "error": (
                        f"Field '{field}' "
                        f"cannot be changed."
                    )
                }

            actual_to_create[field] = value

    # ------------------------------------------
    # Create actual email
    # ------------------------------------------

    actual = create_email(
        to=actual_to_create["to"],
        cc=actual_to_create["cc"],
        subject=actual_to_create["subject"],
        body=actual_to_create["body"]
    )

    converted_at = datetime.now()

    created_at = datetime.fromisoformat(
        draft["created_at"]
    )

    time_to_convert_seconds = (
        converted_at - created_at
    ).total_seconds()

    # ------------------------------------------
    # Save conversion information
    # ------------------------------------------

    updated = update_draft(
        draft_id,
        {
            "actual": actual,
            "converted_at": converted_at.isoformat(),
            "time_to_convert_seconds": (
                time_to_convert_seconds
            )
        }
    )

    return {
        "success": True,
        "draft_id": draft_id,
        "actual": actual,
        "status": updated["status"],
        "time_to_convert_seconds": (
            time_to_convert_seconds
        ),
        "changes_applied": changes or {}
    }


def edit_converted_draft(
    draft_id: str,
    changes: dict
):

    draft = get_draft(draft_id)

    if draft is None:

        return {
            "success": False,
            "error": "Draft not found"
        }

    # ------------------------------------------
    # Must already be converted
    # ------------------------------------------

    if draft["status"] not in {
        "CONVERTED",
        "CONVERTED_EDITED"
    }:

        return {
            "success": False,
            "error": (
                "Only converted drafts can be "
                "edited."
            )
        }

    # ------------------------------------------
    # Check that an actual email exists
    # ------------------------------------------

    actual = draft.get("actual")

    if actual is None:

        return {
            "success": False,
            "error": (
                "Draft has no converted email."
            )
        }

    email_id = actual["id"]

    # ------------------------------------------
    # Apply each requested change
    # ------------------------------------------

    updated_email = actual.copy()

    for field, value in changes.items():

        if field not in EDITABLE_FIELDS:

            return {
                "success": False,
                "error": (
                    f"Field '{field}' "
                    f"cannot be changed."
                )
            }

        result = edit_email(
            email_id,
            field,
            value
        )

        if not result["success"]:

            return result

        updated_email = result["email"]

    # ------------------------------------------
    # Reconcile against ORIGINAL proposal
    # ------------------------------------------

    proposed = draft["proposed"]

    from tools.diff_engine import (
        calculate_diff
    )

    diff = calculate_diff(
        proposed,
        updated_email
    )

    status = (
        "CONVERTED_EDITED"
        if diff
        else "CONVERTED"
    )

    # ------------------------------------------
    # Save updated lifecycle state
    # ------------------------------------------

    updated = update_draft(
        draft_id,
        {
            "actual": updated_email,
            "diff": diff,
            "status": status
        }
    )

    return {
        "success": True,
        "draft_id": draft_id,
        "status": status,
        "actual": updated_email,
        "diff": diff,
        "changes_applied": changes
    }