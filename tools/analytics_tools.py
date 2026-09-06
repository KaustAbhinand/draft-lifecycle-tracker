from tools.draft_store import load_drafts


def generate_lifecycle_report():

    drafts = load_drafts()

    total = len(drafts)

    converted = 0
    converted_edited = 0
    expired = 0

    conversion_times = []

    for draft in drafts.values():

        status = draft.get("status")

        if status == "CONVERTED":

            converted += 1

        elif status == "CONVERTED_EDITED":

            converted_edited += 1

        elif status == "EXPIRED":

            expired += 1

        time_to_convert = draft.get(
            "time_to_convert_seconds"
        )

        if time_to_convert is not None:

            conversion_times.append(
                time_to_convert
            )

    converted_total = (
        converted + converted_edited
    )

    if total > 0:

        conversion_rate = (
            converted_total / total
        ) * 100

        expiration_rate = (
            expired / total
        ) * 100

        edit_rate = (
            converted_edited / total
        ) * 100

        post_conversion_edit_rate = converted_edited/converted_total * 100 if converted_total > 0 else 0

    else:

        conversion_rate = 0
        expiration_rate = 0
        edit_rate = 0
        post_conversion_edit_rate = 0

    if conversion_times:

        average_time = (
            sum(conversion_times)
            / len(conversion_times)
        )

    else:

        average_time = 0

    return {
        "total_drafts": total,

        "converted": converted,

        "converted_edited": converted_edited,

        "expired": expired,

        "conversion_rate": round(
            conversion_rate,
            2
        ),

        "edit_rate": round(
            edit_rate,
            2
        ),

        "post_conversion_edit_rate": round(
            post_conversion_edit_rate,
            2
        ),

        "expiration_rate": round(
            expiration_rate,
            2
        ),

        "average_time_to_convert_seconds": round(
            average_time,
            2
        )
    }

def print_lifecycle_report():

    report = generate_lifecycle_report()

    print("\n")
    print("==============================")
    print("      LIFECYCLE REPORT")
    print("==============================")

    print(
        f"Total drafts:       "
        f"{report['total_drafts']}"
    )

    print(
        f"Converted:          "
        f"{report['converted']}"
    )

    print(
        f"Converted + edits:  "
        f"{report['converted_edited']}"
    )

    print(
        f"Expired:            "
        f"{report['expired']}"
    )

    print()

    print(
        f"Conversion rate:    "
        f"{report['conversion_rate']}%"
    )

    print(
        f"Edit rate:          "
        f"{report['edit_rate']}%"
    )

    print(
        f"Expiration rate:    "
        f"{report['expiration_rate']}%"
    )

    average_seconds = (
        report[
            "average_time_to_convert_seconds"
        ]
    )

    average_minutes = (
        average_seconds / 60
    )

    print(
        f"Avg time-to-convert: "
        f"{average_minutes:.2f} minutes"
    )

    print("==============================")