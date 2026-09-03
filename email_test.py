from tools.email_target import (
    create_email,
    get_email,
    edit_email
)


print("Creating email...")

email = create_email(
    to="rahul@example.com",
    cc="",
    subject="Project Discussion",
    body="Hi Rahul,\n\nLet's discuss the project."
)

print("\nCreated:")
print(email)


print("\nRetrieving email...")

retrieved = get_email(
    email["id"]
)

print(retrieved)


print("\nEditing email subject...")

edited = edit_email(
    email["id"],
    "subject",
    "Updated Project Discussion"
)

print(edited)