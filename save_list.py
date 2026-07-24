import os
import json
import base64
import sys
import requests

# Read environment variables set by GitHub Actions
TOKEN = os.environ.get("APP_GITHUB_TOKEN")
REPO_OWNER = "davileung1"
REPO_NAME = "product-checker"
FILE_PATH = "lists.json"

API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"

def update_lists():
    # Payload passed from frontend via GitHub Action event
    event_payload_path = os.environ.get("GITHUB_EVENT_PATH")
    with open(event_payload_path, "r") as f:
        event_data = json.load(f)

    client_payload = event_data.get("client_payload", {})
    action_type = client_payload.get("action")  # "save" or "delete"
    list_name = client_payload.get("list_name")
    codes = client_payload.get("codes", "")

    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    # 1. Fetch current lists.json content and SHA
    response = requests.get(API_URL, headers=headers)
    
    global_lists = {}
    sha = None

    if response.status_code == 200:
        data = response.json()
        sha = data["sha"]
        content_decoded = base64.b64decode(data["content"]).decode("utf-8")
        global_lists = json.loads(content_decoded)

    # 2. Update dictionary
    if action_type == "save":
        global_lists[list_name] = codes
        commit_message = f"Add list: {list_name}"
    elif action_type == "delete":
        global_lists.pop(list_name, None)
        commit_message = f"Delete list: {list_name}"
    else:
        print("Unknown action type.")
        sys.exit(1)

    # 3. Commit back to repository
    new_content = json.dumps(global_lists, indent=2)
    encoded_content = base64.b64encode(new_content.encode("utf-8")).decode("utf-8")

    put_body = {
        "message": commit_message,
        "content": encoded_content,
    }
    if sha:
        put_body["sha"] = sha

    put_response = requests.put(API_URL, headers=headers, json=put_body)

    if put_response.status_code in [200, 201]:
        print(f"Successfully updated lists.json via Python!")
    else:
        print(f"Failed to update GitHub: {put_response.text}")
        sys.exit(1)

if __name__ == "__main__":
    update_lists()
