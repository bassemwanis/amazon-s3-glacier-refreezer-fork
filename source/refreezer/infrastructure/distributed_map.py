"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

from aws_cdk import aws_stepfunctions as sfn
from constructs import Construct
from typing import Dict, Any

DEFAULT_MAX_CONCURRENCY = 10000


class DistributedMap(sfn.CustomState):
    def __init__(
        self,
        scope: Construct,
        distributed_map_id: str,
        definition: sfn.IChainable,
        **kwargs: Any,
    ) -> None:
        max_concurrency = kwargs.get("max_concurrency")
        item_reader_resource = kwargs.get("item_reader_resource")
        items_path = kwargs.get("items_path")
        reader_config = kwargs.get("reader_config")
        item_reader_parameters = kwargs.get("item_reader_parameters")
        item_selector = kwargs.get("item_selector")
        result_selector = kwargs.get("result_selector")
        result_path = kwargs.get("result_path")

        map = sfn.Map(scope, f"{distributed_map_id}InlineMap")
        map.iterator(definition)
        map_iterator = map.to_state_json()["Iterator"]

        state_json: Dict[str, Any]
        state_json = {
            "Type": "Map",
            "ItemProcessor": {
                "ProcessorConfig": {
                    "Mode": "DISTRIBUTED",
                    "ExecutionType": "STANDARD",
                },
            },
        }

        state_json["MaxConcurrency"] = DEFAULT_MAX_CONCURRENCY
        if max_concurrency is not None:
            state_json["MaxConcurrency"] = max_concurrency

        if item_selector is not None:
            state_json["ItemSelector"] = item_selector

        if items_path is not None:
            state_json["ItemsPath"] = items_path

        if result_selector is not None:
            state_json["ResultSelector"] = result_selector

        if result_path is not None:
            state_json["ResultPath"] = result_path

        if item_reader_resource is not None:
            state_json["ItemReader"] = {
                "Resource": item_reader_resource,
                "ReaderConfig": reader_config,
                "Parameters": item_reader_parameters,
            }

        state_json["ItemProcessor"].update(map_iterator)

        super().__init__(scope, distributed_map_id, state_json=state_json)
