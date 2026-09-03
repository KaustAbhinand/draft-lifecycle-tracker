import json
import os
import uuid


DATA_FILE = "data/target_objects.json"


def load_target_objects():

    if not os.path.exists(DATA_FILE):
        return {}

    with open(DATA_FILE, "r") as file:
        return json.load(file)


def save_target_objects(objects):

    os.makedirs("data", exist_ok=True)

    with open(DATA_FILE, "w") as file:
        json.dump(
            objects,
            file,
            indent=2
        )


def create_target_object(data):

    objects = load_target_objects()

    target_id = str(uuid.uuid4())

    target_object = {
        "id": target_id,
        **data
    }

    objects[target_id] = target_object

    save_target_objects(objects)

    return target_object


def get_target_object(target_id):

    objects = load_target_objects()

    return objects.get(target_id)


def edit_target_object(
    target_id,
    field,
    value
):

    targets = load_target_objects()

    if target_id not in targets:

        return {
            "success": False,
            "error": "Target object not found"
        }

    targets[target_id][field] = value

    save_target_objects(targets)

    return {
        "success": True,
        "target": targets[target_id]
    }