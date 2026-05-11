import json
import os
import uuid
from datetime import datetime, timezone

import boto3

_table = None


def _table_resource():
    global _table
    if _table is None:
        _table = boto3.resource("dynamodb").Table(os.environ["USERS_TABLE_NAME"])
    return _table


def _response(status_code, payload):
    return {
        "statusCode": status_code,
        "headers": {"content-type": "application/json"},
        "body": json.dumps(payload),
    }


def list_users(event, context):
    """GET /users — scan DynamoDB (demo-sized; not for huge tables)."""
    table = _table_resource()
    result = table.scan(Limit=100)
    users = []
    for item in result.get("Items", []):
        users.append(
            {
                "id": item["userId"],
                "email": item.get("email", ""),
                "created_at": item.get("createdAt", ""),
            }
        )
    users.sort(key=lambda u: u["created_at"])
    return _response(200, {"users": users})


def create_user(event, context):
    """POST /users — expects JSON {"email":"..."}; writes new item with UUID."""
    table = _table_resource()
    body = event.get("body") or "{}"
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return _response(400, {"error": "Invalid JSON body"})
    email = (data.get("email") or "").strip()
    if not email:
        return _response(400, {"error": "Field 'email' is required"})

    user_id = str(uuid.uuid4())
    created = datetime.now(timezone.utc).isoformat()
    table.put_item(
        Item={
            "userId": user_id,
            "email": email,
            "createdAt": created,
        }
    )
    return _response(
        201,
        {"user": {"id": user_id, "email": email, "created_at": created}},
    )
