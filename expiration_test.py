from tools.lifecycle_tools import expire_abandoned_drafts


result = expire_abandoned_drafts()

print("Expiration result:")
print(result)