"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

from typing import Dict, Any
import logging

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)


def mock_galcier_services_handler(
    event: Dict[str, Any], context: Any
) -> Dict[str, Any]:
    LOGGER.info("InitiateJob - Inventory Retrieval lambda has been invoked.")

    type = event["Type"]
    description = event["Description"]
    format = event["Format"]
    sns_topic = event["SNSTopic"]
    import time

    LOGGER.info("Mock Start task.")
    time.sleep(30)
    LOGGER.info("Mock Finish task.")
    LOGGER.info("Mock post to SNS topic.")
    # TODO publish a message to SNS topic

    return {
        "Location": "/111122223333/vaults/examplevault/jobs/HkF9p6o7yjhFx-K3CGl6fuSm6VzW9T7esGQfco8nUXVYwS0jlb5gq1JZ55yHgt5vP54ZShjoQzQVVh7vEXAMPLEjobID",
        "x-amz-job-id": "HkF9p6o7yjhFx-K3CGl6fuSm6VzW9T7esGQfco8nUXVYwS0jlb5gq1JZ55yHgt5vP54ZShjoQzQVVh7vEXAMPLEjobID",
    }
