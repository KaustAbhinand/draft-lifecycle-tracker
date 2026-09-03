from tools.target_system import edit_target_object


target_id = "f2b9a3b7-a324-46ba-944c-b4b51d4941c0"

result = edit_target_object(
    target_id,
    "duration",
    90
)

print("Edited target:")
print(result)