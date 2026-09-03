import json

from llm.groq_agent import client

from tools.draft_tools import (
    create_draft,
    fetch_draft
)

from tools.reconciliation_tool import (
    reconcile_draft
)

from tools.conversion_tools import (
    convert_draft
)

from tools.analytics_tools import (
    generate_lifecycle_report
)

from tools.conversion_tools import convert_draft, edit_converted_draft


# --------------------------------------------------
# Tool definitions
# --------------------------------------------------

CREATE_DRAFT_TOOL = {
    "type": "function",
    "function": {
        "name": "create_draft",
        "description": (
            "Create a new email draft from the "
            "information provided by the user."
        ),
        "parameters": {
            "type": "object",
            "properties": {

                "to": {
                    "type": "string",
                    "description": (
                        "Email recipient. Use the email address "
                        "provided by the user."
                    )
                },

                "cc": {
                    "type": "string",
                    "description": (
                        "CC recipient email address, if provided. "
                        "Use an empty string if there is no CC."
                    )
                },

                "subject": {
                    "type": "string",
                    "description": (
                        "Subject line of the email."
                    )
                },

                "body": {
                    "type": "string",
                    "description": (
                        "Full body of the email."
                    )
                }
            },
            "required": [
                "to",
                "cc",
                "subject",
                "body"
            ]
        }
    }
}


GET_DRAFT_TOOL = {
    "type": "function",
    "function": {
        "name": "get_draft",
        "description": (
            "Retrieve an existing email draft using its ID."
        ),
        "parameters": {
            "type": "object",
            "properties": {

                "draft_id": {
                    "type": "string",
                    "description": (
                        "The ID of the draft to retrieve."
                    )
                }
            },
            "required": [
                "draft_id"
            ]
        }
    }
}


CONVERT_DRAFT_TOOL = {
    "type": "function",
    "function": {
        "name": "convert_draft",
        "description": (
            "Convert an OPEN email draft into the target "
            "email system. The user may request changes "
            "to one or more email fields as part of the "
            "conversion."
        ),
        "parameters": {
            "type": "object",
            "properties": {

                "draft_id": {
                    "type": "string",
                    "description": (
                        "The ID of the draft to convert."
                    )
                },

                "changes": {
                    "type": "object",
                    "description": (
                        "Optional changes requested by the "
                        "user during conversion. Only include "
                        "fields that the user explicitly asks "
                        "to change."
                    ),
                    "properties": {

                        "to": {
                            "type": "string",
                            "description": (
                                "New recipient if requested."
                            )
                        },

                        "cc": {
                            "type": "string",
                            "description": (
                                "New CC recipient if requested."
                            )
                        },

                        "subject": {
                            "type": "string",
                            "description": (
                                "New subject if requested."
                            )
                        },

                        "body": {
                            "type": "string",
                            "description": (
                                "New email body if requested."
                            )
                        }
                    }
                }
            },
            "required": [
                "draft_id"
            ]
        }
    }
}

EDIT_CONVERTED_DRAFT_TOOL = {
    "type": "function",
    "function": {
        "name": "edit_converted_draft",
        "description": (
            "Edit an already converted email. "
            "Use this when the user asks to change "
            "an email that has already been converted. "
            "The original proposed email must remain "
            "unchanged. After editing, reconcile the "
            "actual email against the original proposal."
        ),
        "parameters": {
            "type": "object",
            "properties": {

                "draft_id": {
                    "type": "string",
                    "description": (
                        "The ID of the already converted draft."
                    )
                },

                "changes": {
                    "type": "object",
                    "description": (
                        "Fields to change on the converted email."
                    ),
                    "properties": {

                        "to": {
                            "type": "string"
                        },

                        "cc": {
                            "type": "string"
                        },

                        "subject": {
                            "type": "string"
                        },

                        "body": {
                            "type": "string"
                        }
                    }
                }
            },
            "required": [
                "draft_id",
                "changes"
            ]
        }
    }
}


RECONCILE_DRAFT_TOOL = {
    "type": "function",
    "function": {
        "name": "reconcile_draft",
        "description": (
            "Reconcile a converted email draft against "
            "the actual email object in the target system."
        ),
        "parameters": {
            "type": "object",
            "properties": {

                "draft_id": {
                    "type": "string",
                    "description": (
                        "The ID of the draft to reconcile."
                    )
                }
            },
            "required": [
                "draft_id"
            ]
        }
    }
}


GET_LIFECYCLE_REPORT_TOOL = {
    "type": "function",
    "function": {
        "name": "get_lifecycle_report",
        "description": (
            "Generate a summary report of email draft "
            "lifecycle activity, including conversion, "
            "edits, expiration, and time-to-convert."
        ),
        "parameters": {
            "type": "object",
            "properties": {}
        }
    }
}


TOOLS = [
    CREATE_DRAFT_TOOL,
    GET_DRAFT_TOOL,
    CONVERT_DRAFT_TOOL,
    EDIT_CONVERTED_DRAFT_TOOL,
    RECONCILE_DRAFT_TOOL,
    GET_LIFECYCLE_REPORT_TOOL
]


# --------------------------------------------------
# Tool execution
# --------------------------------------------------

def execute_tool(tool_name, arguments):

    if tool_name == "create_draft":

        return create_draft(
            to=arguments["to"],
            cc=arguments["cc"],
            subject=arguments["subject"],
            body=arguments["body"]
        )

    if tool_name == "get_draft":

        return fetch_draft(
            draft_id=arguments["draft_id"]
        )

    if tool_name == "convert_draft":

        return convert_draft(
            draft_id=arguments["draft_id"],
            changes=arguments.get("changes")
        )

    if tool_name == "edit_converted_draft":

        return edit_converted_draft(
            draft_id=arguments["draft_id"],
            changes=arguments["changes"]
        )

    if tool_name == "reconcile_draft":

        return reconcile_draft(
            draft_id=arguments["draft_id"]
        )

    if tool_name == "get_lifecycle_report":

        return generate_lifecycle_report()

    raise ValueError(
        f"Unknown tool: {tool_name}"
    )


# --------------------------------------------------
# Agent instructions
# --------------------------------------------------

SYSTEM_INSTRUCTION = """
You are an Email Draft Lifecycle Agent.

Your job is to manage the lifecycle of email drafts.

Available actions:

1. Create an email draft.
2. Retrieve an email draft.
3. Convert an email draft.
4. Edit an already converted email draft.
5. Reconcile a converted email draft.
6. Generate a lifecycle report.

Rules:

- When the user asks to create or draft an email,
  use create_draft.

- Extract the recipient, CC, subject, and body
  from the user's request.

- If the user does not provide a CC recipient,
  use an empty string.

- Do not send real emails. This system only creates
  and manages simulated email objects.

- When the user asks to inspect a draft,
  use get_draft.

- When the user explicitly asks to convert
  or finalize a draft, use convert_draft.

- If the user requests changes as part of the
  conversion, include those changes in the
  "changes" argument.

- Changes can apply to ANY EDITABLE email field:
  to, cc, subject, or body.

- Only include fields that the user explicitly
  asks to change.

- The original proposed draft must remain unchanged.

- The requested changes must be applied to the
  actual object during conversion.

- If the user requests changes to an already converted email,
  use edit_converted_draft. The state needs to change to CONVERTED_EDITED 
  after the changes are applied. The original proposed draft must remain unchanged.

- After successfully converting a draft,
  reconcile it using reconcile_draft.

- If the actual object matches the original proposal,
  the lifecycle state should be CONVERTED.

- If the actual object differs from the original
  proposal, the lifecycle state should be
  CONVERTED_EDITED.

- When reconciliation finds differences, clearly
  report the field-level differences.

- When the user asks for lifecycle statistics,
  conversion rates, edit rates, expiration rates,
  time-to-convert, or other lifecycle metrics,
  use get_lifecycle_report.

- Never claim that a conversion succeeded
  unless the tool confirms it.

- Never claim that a draft is converted without
  checking the tool result.

- Never invent a draft ID.

- Use tool results as the source of truth.

- Maintain conversational context across turns.

- If the user says "it", "this draft", or
  "that draft", use the most recently discussed
  draft ID when the reference is unambiguous.

- Do not ask for a draft ID when the conversation
  already provides an unambiguous draft ID.

Keep your final response concise.
"""


# --------------------------------------------------
# Agent
# --------------------------------------------------

def run_agent(
    user_request,
    conversation_history=None
):

    if conversation_history is None:
        conversation_history = []

    messages = [
        {
            "role": "system",
            "content": SYSTEM_INSTRUCTION
        }
    ]

    messages.extend(
        conversation_history
    )

    messages.append(
        {
            "role": "user",
            "content": user_request
        }
    )

    while True:

        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=messages,
            tools=TOOLS,
            tool_choice="auto"
        )

        message = response.choices[0].message

        if not message.tool_calls:

            return (
                message.content,
                messages
            )

        messages.append(
            message
        )

        for tool_call in message.tool_calls:

            tool_name = tool_call.function.name

            arguments = json.loads(
                tool_call.function.arguments
            )

            print(
                f"\n[Agent calling: {tool_name}]"
            )

            print(
                f"[Arguments: {arguments}]"
            )

            result = execute_tool(
                tool_name,
                arguments
            )

            print(
                f"[Tool result: {result}]"
            )

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(
                        result
                    )
                }
            )