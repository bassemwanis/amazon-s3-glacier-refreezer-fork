"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

from typing import Dict, Any
import logging
import time

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)


def mock_galcier_services_handler(
    event: Dict[str, Any], context: Any
) -> Dict[str, Any]:
    LOGGER.info("InitiateJob - Inventory Retrieval lambda has been invoked.")

    if "Type" in event:
        type = event["Type"]
    if "Description" in event:
        description = event["Description"]
    if "Format" in event:
        format = event["Format"]
    if "SNSTopic" in event:
        sns_topic = event["SNSTopic"]

    if type == "archive-retrieval":
        LOGGER.info("Mock Start task: archive-retrieval")
    elif type == "inventory-retrieval":
        LOGGER.info("Mock Start task: inventory-retrieval")

    time.sleep(5)
    LOGGER.info("Mock Finish task.")
    LOGGER.info("Mock post to SNS topic.")
    # TODO publish a message to SNS topic

    return {
        "JobId": "vIvvhoHkEV_2nDRzeU5q_4nyk0z5L6aFme7KzZltXQjNCIhSJOb71Mkr1j4hkdxne6jVqFzL-JedkHFR8gth2YbRXVc0",
        "Action": "InventoryRetrieval",
        "VaultARN": "arn:aws:glacier:us-east-1:439780116353:vaults/test-vault-01",
        "CreationDate": "2023-02-23T17:12:37.661Z",
        "Completed": True,
        "StatusCode": "Succeeded",
        "StatusMessage": "Succeeded",
        "InventorySizeInBytes": 130,
        "CompletionDate": "2023-02-23T21:01:53.364Z",
        "InventoryRetrievalParameters": {"Format": "JSON"},
    }
