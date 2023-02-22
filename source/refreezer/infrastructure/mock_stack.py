"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

from aws_cdk import Stack
from aws_cdk import Duration
from aws_cdk import aws_stepfunctions as sfn
from constructs import Construct
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_stepfunctions_tasks as tasks

from cdk_nag import NagSuppressions


class MockStack(Stack):
    lambda_invoke_task: sfn.INextable

    def __init__(self, scope: Construct, construct_id: str) -> None:
        super().__init__(scope, construct_id)
        mock_lambda = lambda_.Function(
            self,
            "MockGalcierService",
            handler="refreezer.application.handlers.mock_galcier_services_handler",
            runtime=lambda_.Runtime.PYTHON_3_9,
            code=lambda_.Code.from_asset("source"),
            description="Lambda to mock Glacier service operations for integration tests.",
        )

        self.lambda_invoke_task = tasks.LambdaInvoke(
            scope, "MockLambdaTask", lambda_function=mock_lambda
        )

        assert mock_lambda.role is not None
        NagSuppressions.add_resource_suppressions(
            mock_lambda.role.node.find_child("Resource"),
            [
                {
                    "id": "AwsSolutions-IAM4",
                    "reason": "CDK grants AWS managed policy for Lambda basic execution by default. Replacing it with a customer managed policy will be addressed later.",
                    "appliesTo": [
                        "Policy::arn:<AWS::Partition>:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
                    ],
                },
            ],
        )
