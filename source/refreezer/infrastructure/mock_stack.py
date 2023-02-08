"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

from aws_cdk import Stack
from aws_cdk import Duration
from aws_cdk import aws_stepfunctions as sfn
from constructs import Construct


class MockStack(Stack):
    wait_state: sfn.INextable

    def __init__(self, scope: Construct, construct_id: str) -> None:
        super().__init__(scope, construct_id)
        self.wait_state = sfn.Wait(
            scope, "waitState", time=sfn.WaitTime.duration(Duration.seconds(2))
        )
