"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

from aws_cdk import (
    Stack,
    CfnOutput,
)
from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk import aws_iam as iam
from aws_cdk import aws_kms as kms
from aws_cdk import aws_sns as sns
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_stepfunctions as sfn
from aws_cdk import RemovalPolicy
from cdk_nag import NagSuppressions
from constructs import Construct

from refreezer.infrastructure.distributed_map import DistributedMap


class OutputKeys:
    ASYNC_FACILITATOR_TABLE_NAME = "AsyncFacilitatorTableName"
    ASYNC_FACILITATOR_TOPIC_ARN = "AsyncFacilitatorTopicArn"
    OUTPUT_BUCKET_NAME = "OutputBucketName"
    INVENTORY_BUCKET_NAME = "InventoryBucketName"
    INVENTORY_RETRIEVAL_STATE_MACHINE_ARN = "InventoryRetrievalStateMachineArn"


class RefreezerStack(Stack):
    outputs: dict[str, CfnOutput]

    def __init__(self, scope: Construct, construct_id: str) -> None:
        super().__init__(scope, construct_id)

        self.outputs = {}

        table = dynamodb.Table(
            self,
            "AsyncFacilitatorTable",
            partition_key=dynamodb.Attribute(
                name="job_id", type=dynamodb.AttributeType.STRING
            ),
            point_in_time_recovery=True,
        )

        self.outputs[OutputKeys.ASYNC_FACILITATOR_TABLE_NAME] = CfnOutput(
            self,
            OutputKeys.ASYNC_FACILITATOR_TABLE_NAME,
            value=table.table_name,
        )

        sns_default_key = kms.Alias.from_alias_name(
            self, "DefaultKeySNS", "alias/aws/sns"
        )

        topic = sns.Topic(
            self,
            "AsyncFacilitatorTopic",
            master_key=sns_default_key,
        )

        topic.add_to_resource_policy(
            iam.PolicyStatement(
                actions=["sns:Publish"],
                conditions={"Bool": {"aws:SecureTransport": False}},
                effect=iam.Effect.DENY,
                principals=[iam.AnyPrincipal()],
                resources=[topic.topic_arn],
            )
        )

        self.outputs[OutputKeys.ASYNC_FACILITATOR_TOPIC_ARN] = CfnOutput(
            self,
            OutputKeys.ASYNC_FACILITATOR_TOPIC_ARN,
            value=topic.topic_arn,
        )

        # Bucket to store the restored vault.
        # TODO This bucket will be made configurable in a future task.
        output_bucket = s3.Bucket(
            self,
            "OutputBucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
            versioned=True,
            removal_policy=RemovalPolicy.RETAIN,
        )

        self.outputs[OutputKeys.OUTPUT_BUCKET_NAME] = CfnOutput(
            self,
            OutputKeys.OUTPUT_BUCKET_NAME,
            value=output_bucket.bucket_name,
        )

        NagSuppressions.add_resource_suppressions(
            output_bucket,
            [
                {
                    "id": "AwsSolutions-S1",
                    "reason": "Output Bucket has server access logs disabled and will be addressed later.",
                }
            ],
        )

        # Bucket to store the inventory and the Glue output after it's sorted.
        # TODO This bucket will be made configurable in a future task.
        inventory_bucket = s3.Bucket(
            self,
            "InventoryBucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
            versioned=True,
            removal_policy=RemovalPolicy.RETAIN,
        )

        self.outputs[OutputKeys.INVENTORY_BUCKET_NAME] = CfnOutput(
            self,
            OutputKeys.INVENTORY_BUCKET_NAME,
            value=inventory_bucket.bucket_name,
        )

        NagSuppressions.add_resource_suppressions(
            inventory_bucket,
            [
                {
                    "id": "AwsSolutions-S1",
                    "reason": "Inventory Bucket has server access logs disabled and will be addressed later.",
                }
            ],
        )

        test_pass_chunk_array = sfn.Pass(
            self,
            "PassChunkArray",
            parameters={
                "chunk_array": [
                    "0-1",
                    "2-3",
                    "4-5",
                    "6-7",
                    "8-9",
                    "10-11",
                    "12-13",
                    "14-15",
                ]
            },
        )

        test_pass_state = sfn.Pass(self, "JustPassState")
        test_succeed_state = sfn.Succeed(self, "JustSucceedState")
        test_definition = test_pass_state.next(test_succeed_state)

        chunks_distributed_map = DistributedMap(
            scope,
            "ChunksDistributedMap",
            definition=test_definition,
            items_path="$.chunk_array",
        )

        another_test_succeed_state = sfn.Succeed(self, "AnotherJustSucceedState")
        another_test_definition = another_test_succeed_state
        another_chunks_distributed_map = DistributedMap(
            scope,
            "AnotherChunksDistributedMap",
            definition=another_test_definition,
            items_path="$.chunk_array",
        )

        state_json = {
            "Type": "Task",
            "Parameters": {
                "AccountId": Stack.of(self).account,
                "JobParameters": {
                    "Type": "inventory-retrieval",
                    "Description.$": "$.description",
                    "Format": "CSV",
                    "SnsTopic": topic.topic_arn,
                },
                "VaultName.$": "$.vaultName",
            },
            "Resource": "arn:aws:states:::aws-sdk:glacier:initiateJob",
        }
        initiate_job = sfn.CustomState(scope, "InitiateJob", state_json=state_json)

        definition = test_pass_chunk_array.next(chunks_distributed_map).next(
            another_chunks_distributed_map
        )

        inventory_retrieval_state_machine = sfn.StateMachine(
            self, "InventoryRetrievalStateMachine", definition=definition
        )

        self.outputs[OutputKeys.INVENTORY_RETRIEVAL_STATE_MACHINE_ARN] = CfnOutput(
            self,
            OutputKeys.INVENTORY_RETRIEVAL_STATE_MACHINE_ARN,
            value=inventory_retrieval_state_machine.state_machine_arn,
        )

        NagSuppressions.add_resource_suppressions(
            inventory_retrieval_state_machine,
            [
                {
                    "id": "AwsSolutions-SF1",
                    "reason": "Step Function logging is disabled and will be addressed later.",
                },
                {
                    "id": "AwsSolutions-SF2",
                    "reason": "Step Function X-Ray tracing is disabled and will be addressed later.",
                },
            ],
        )

        state_machine_policy = iam.Policy(
            self,
            "StateMachinePolicy",
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "states:StartExecution",
                    ],
                    resources=[inventory_retrieval_state_machine.state_machine_arn],
                ),
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=["states:DescribeExecution", "states:StopExecution"],
                    resources=[
                        "arn:aws:states:"
                        + Stack.of(self).region
                        + ":"
                        + Stack.of(self).account
                        + ":execution:"
                        + inventory_retrieval_state_machine.state_machine_name
                        + "/*"
                    ],
                ),
            ],
        )

        state_machine_policy.attach_to_role(inventory_retrieval_state_machine.role)
