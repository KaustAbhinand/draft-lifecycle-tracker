import json
import os
import uuid


EMAIL_FILE = "data/emails.json"


def load_emails():

    if not os.path.exists(EMAIL_FILE):
        return {}

    with open(
        EMAIL_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


def save_emails(emails):

    with open(
        EMAIL_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            emails,
            file,
            indent=4
        )


def create_email(
    to,
    cc,
    subject,
    body
):

    emails = load_emails()

    email_id = str(
        uuid.uuid4()
    )

    email = {
        "id": email_id,
        "to": to,
        "cc": cc,
        "subject": subject,
        "body": body
    }

    emails[email_id] = email

    save_emails(emails)

    return email


def get_email(email_id):

    emails = load_emails()

    return emails.get(
        email_id
    )


def edit_email(
    email_id,
    field,
    value
):

    emails = load_emails()

    if email_id not in emails:

        return {
            "success": False,
            "error": "Email not found"
        }

    emails[email_id][field] = value

    save_emails(emails)

    return {
        "success": True,
        "email": emails[email_id]
    }