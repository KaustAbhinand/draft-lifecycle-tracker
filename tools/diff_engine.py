# Tracks the difference between the drafts and creates the report.

def calculate_diff(proposed, actual):

    diff = {}

    # Look at every field that exists
    # in either object.
    all_fields = (
        set(proposed.keys())
        | set(actual.keys())
    )

    for field in all_fields:

        proposed_value = proposed.get(field)
        actual_value = actual.get(field)

        # Ignore the target system's generated ID.
        if field == "id":
            continue

        if proposed_value != actual_value:

            diff[field] = {
                "proposed": proposed_value,
                "actual": actual_value
            }

    return diff