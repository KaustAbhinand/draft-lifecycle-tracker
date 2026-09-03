from agents.lifecycle_agent import run_agent

from tools.analytics_tools import (
    print_lifecycle_report
)


def main():
    conversation_history = []
    print("==============================")
    print("   Draft Lifecycle AI Agent")
    print("==============================")
    print("Type 'exit' to stop.")

    while True:

        user_request = input("\nYou: ")

        command = user_request.strip().lower()

        if command in {
            "exit",
            "quit"
        }:
            break

        try:

            # -------------------------------
            # Local lifecycle commands
            # -------------------------------

            if command in {
                "show report",
                "show the report",
                "lifecycle report",
                "show lifecycle report",
                "all"
            }:

                print_lifecycle_report()

                continue

            # -------------------------------
            # AI agent
            # -------------------------------

            result, conversation_history = run_agent(
                user_request,
                conversation_history
            )

            print("\nAgent:")
            print(result)

        except Exception as error:

            print("\nERROR:")
            print(error)


if __name__ == "__main__":
    main()