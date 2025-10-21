import json
import os
from decimal import Decimal
from typing import Any, Dict

import boto3
from boto3.dynamodb.types import TypeDeserializer
from botocore.exceptions import BotoCoreError, ClientError

_QUEUE_URL = os.environ["QUEUE_URL"]
_SQS_CLIENT = boto3.client("sqs")
_DESERIALIZER = TypeDeserializer()


def _ddb_item_to_dict(item: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a DynamoDB stream image into a plain dict."""
    return {key: _DESERIALIZER.deserialize(value) for key, value in item.items()}


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


def handler(event, context):
    """DynamoDB stream handler pushing inserts to SQS."""
    for record in event.get("Records", []):
        if record.get("eventName") != "INSERT":
            continue

        new_image = record.get("dynamodb", {}).get("NewImage")
        if not new_image:
            continue

        payload = _decimal_to_native(_ddb_item_to_dict(new_image))

        try:
            print("Sending message to SQS in PERSON STREAM PUBLISHER: ")
            _SQS_CLIENT.send_message(
                QueueUrl=_QUEUE_URL,
                MessageBody=json.dumps(payload),
            )
        except (BotoCoreError, ClientError) as exc:
            # Surface the failure so Lambda retries; adjust to DLQ in production.
            raise RuntimeError("Failed to send message to SQS") from exc
