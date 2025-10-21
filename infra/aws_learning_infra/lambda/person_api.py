import json
import os
from decimal import Decimal
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError

_TABLE_NAME = os.environ["TABLE_NAME"]
_DDB = boto3.resource("dynamodb")
_TABLE = _DDB.Table(_TABLE_NAME)


def _response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def _validate_payload(payload: Dict[str, Any]) -> tuple[bool, str]:
    name = payload.get("name")
    age = payload.get("age")

    if not isinstance(name, str) or not name.strip():
        return False, "Field 'name' must be a non-empty string"

    try:
        age_int = int(age)
    except (TypeError, ValueError):
        return False, "Field 'age' must be an integer"

    if age_int < 0:
        return False, "Field 'age' must be non-negative"

    return True, ""


def _decimal_to_native(value: Any) -> Any:
    if isinstance(value, list):
        return [_decimal_to_native(v) for v in value]
    if isinstance(value, dict):
        return {k: _decimal_to_native(v) for k, v in value.items()}
    if isinstance(value, Decimal):
        if value % 1 == 0:
            return int(value)
        return float(value)
    return value


def _handle_post(event: Dict[str, Any]) -> Dict[str, Any]:
    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return _response(400, {"message": "Invalid JSON body"})

    is_valid, message = _validate_payload(body)
    if not is_valid:
        return _response(400, {"message": message})

    name = body["name"]
    age = int(body["age"])

    try:
        _TABLE.put_item(
            Item={"name": name, "age": Decimal(age)},
            ConditionExpression="attribute_not_exists(#name)",
            ExpressionAttributeNames={"#name": "name"},
        )
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code")
        if error_code == "ConditionalCheckFailedException":
            return _response(409, {"message": "Person already exists"})
        raise

    return _response(201, {"name": name, "age": age})


def _handle_get(event: Dict[str, Any]) -> Dict[str, Any]:
    path_params = event.get("pathParameters") or {}
    name = path_params.get("name")
    if not name:
        return _response(400, {"message": "Path parameter 'name' is required"})

    try:
        result = _TABLE.get_item(Key={"name": name})
    except ClientError:
        raise

    item = result.get("Item")
    if not item:
        return _response(404, {"message": "Person not found"})

    native_item = _decimal_to_native(item)

    return _response(200, native_item)


def handler(event, context):
    method = event.get("httpMethod")

    try:
        if method == "POST":
            return _handle_post(event)
        if method == "GET":
            return _handle_get(event)
    except ClientError as exc:
        return _response(500, {"message": exc.response["Error"]["Message"]})

    return _response(405, {"message": f"Method {method} not allowed"})
