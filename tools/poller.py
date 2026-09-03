# Make polling automatic

import time

from tools.lifecycle_tools import expire_abandoned_drafts, poll_reconciliation


POLL_INTERVAL_SECONDS = 30


def run_poller():

    print("\n[Lifecycle poller started]")

    while True:

        try:

            print(
                "\n[Poller] Checking lifecycle..."
            )

            # Check abandoned drafts
            expiration_result = (
                expire_abandoned_drafts()
            )

            if expiration_result["expired_count"] > 0:

                print(
                    "[Poller] Expired drafts:",
                    expiration_result[
                        "expired_drafts"
                    ]
                )

            # Check converted drafts
            reconciliation_results = (
                poll_reconciliation()
            )

            if reconciliation_results:

                print(
                    "[Poller] Reconciled:",
                    len(reconciliation_results),
                    "draft(s)"
                )

            else:

                print(
                    "[Poller] Nothing to reconcile."
                )

        except Exception as error:

            print(
                "[Poller ERROR]",
                error
            )

        time.sleep(
            POLL_INTERVAL_SECONDS
        )