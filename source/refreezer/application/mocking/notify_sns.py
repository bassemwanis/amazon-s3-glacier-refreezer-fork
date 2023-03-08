"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

from typing import Dict, Any, TYPE_CHECKING
import random
import string
import boto3
import json
import time

if TYPE_CHECKING:
    from mypy_boto3_sns import SNSClient
else:
    SNSClient = object

NOTIFICATION_DELAY_IN_SEC = 5
INVENTORY_SIZE_IN_BYTES = 1024


def notify_sns_job_completion(
    account_id: str, vault_name: str, job_id: str, sns_topic: str
) -> None:
    client: SNSClient = boto3.client("sns")
    time.sleep(NOTIFICATION_DELAY_IN_SEC)
    message = {
        "Action": "InventoryRetrieval",
        "Completed": True,
        "CompletionDate": "2023-01-01T01:01:01.001Z",
        "CreationDate": "2023-01-01T02:02:02.002Z",
        "InventoryRetrievalParameters": {
            "Format": "CSV",
        },
        "InventorySizeInBytes": INVENTORY_SIZE_IN_BYTES,
        "JobDescription": "This is a first test - from mock lambda",
        "JobId": job_id,
        "SNSTopic": sns_topic,
        "StatusCode": "Succeeded",
        "StatusMessage": "Succeeded",
        "VaultARN": "arn:aws:glacier:us-east-1:439780116353:vaults/test-vault-01",
    }

    client.publish(
        TopicArn=sns_topic,
        Message=json.dumps(message),
        Subject="Notification From Mocking Glacier Service",
        MessageStructure="json",
    )
