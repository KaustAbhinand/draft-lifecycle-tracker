from collections import Counter

from tools.draft_store import load_drafts
from tools.analytics_tools import (
    generate_lifecycle_report
)


def prepare_analysis_data():

    drafts = load_drafts()

    report = generate_lifecycle_report()

    edited_drafts = []

    expired_drafts = []

    field_changes = Counter()

    value_changes = Counter()

    for draft in drafts.values():

        # -------------------------------
        # Edited conversions
        # -------------------------------

        if draft.get("status") == "CONVERTED_EDITED":

            diff = draft.get("diff") or {}

            for field, change in diff.items():

                field_changes[field] += 1

                proposed = change.get(
                    "proposed"
                )

                actual = change.get(
                    "actual"
                )

                value_changes[
                    f"{proposed} -> {actual}"
                ] += 1

            edited_drafts.append({
                "draft_id": draft["id"],
                "proposed": draft.get("proposed"),
                "actual": draft.get("actual"),
                "diff": diff
            })

        # -------------------------------
        # Expired drafts
        # -------------------------------

        elif draft.get("status") == "EXPIRED":

            expired_drafts.append({
                "draft_id": draft["id"],
                "proposed": draft.get("proposed"),
                "created_at": draft.get(
                    "created_at"
                ),
                "expired_at": draft.get(
                    "expired_at"
                )
            })

    return {
        "summary": report,

        "edit_patterns": {
            "fields_changed": dict(
                field_changes
            ),

            "value_changes": dict(
                value_changes
            )
        },

        "edited_drafts": edited_drafts,

        "expired_drafts": expired_drafts
    }