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
from aws_cdk import Duration
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_stepfunctions as sfn
from aws_cdk import aws_stepfunctions_tasks as tasks
from aws_cdk import RemovalPolicy
from constructs import Construct
from refreezer.infrastructure.nested_distributed_map import NestedDistributedMap
from typing import Optional


class OutputKeys:
    ASYNC_FACILITATOR_TABLE_NAME = "AsyncFacilitatorTableName"
    ASYNC_FACILITATOR_TOPIC_ARN = "AsyncFacilitatorTopicArn"
    INITIATE_RETRIEVAL_STATE_MACHINE_ARN = "InitiateRetrievalStateMachineArn"


class RefreezerStack(Stack):
    outputs: dict[str, CfnOutput]

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        mock_step: Optional[sfn.INextable] = None,
    ) -> None:
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

        access_log_bucket = s3.Bucket(
            self,
            "AccessLogBucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
            versioned=True,
            removal_policy=RemovalPolicy.DESTROY,
            server_access_logs_prefix="logBucketAccessLog",
        )

        inventory_bucket = s3.Bucket(
            self,
            "InventoryBucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
            versioned=True,
            removal_policy=RemovalPolicy.DESTROY,
            server_access_logs_bucket=access_log_bucket,
            server_access_logs_prefix="log",
        )

        # TODO to be replaced by Initiate Retrieval state machine inner logic.
        success_state = sfn.Succeed(self, "Test Success state")

        vault_name = "test-vault"
        state_json = {
            "Type": "Task",
            "Parameters": {
                "AccountId": Stack.of(self).account,
                "JobParameters": {
                    "Type": "archive-retrieval",
                    "ArchiveId.$": "$.item.ArchiveId",
                    "Tier": "Bulk",
                    "SnsTopic": topic.topic_arn,
                },
                "VaultName": vault_name,
            },
            "Resource": "arn:aws:states:::aws-sdk:glacier:initiateJob",
        }
        initiate_retrieval_glacier_initiate_job = sfn.CustomState(
            scope, "InitiateRetrievalGlacierInitiateJob", state_json=state_json
        )

        initiate_retrieval_dynamodb_put_item = tasks.DynamoPutItem(
            self,
            "PutItem",
            item={
                "job_id": tasks.DynamoAttributeValue.from_string(
                    sfn.JsonPath.string_at("$.JobId")
                )
            },
            table=table,
        )
        if mock_step is None:
            mock_step = initiate_retrieval_glacier_initiate_job

        inner_logic_definition = mock_step.next(
            initiate_retrieval_dynamodb_put_item
        ).next(success_state)

        initiate_retrieval_nested_distributed_map = NestedDistributedMap(
            self,
            nested_distributed_map_id="InitiateRetrievalNestedDistributedMap",
            bucket=inventory_bucket,
            definition=inner_logic_definition,
            max_concurrency=1,
        )

        state_policy = iam.Policy(
            self,
            "StateMachinePolicy",
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "glacier:InitiateJob",
                    ],
                    resources=[
                        "arn:aws:glacier:"
                        + Stack.of(self).region
                        + ":"
                        + Stack.of(self).account
                        + ":vaults/"
                        + vault_name
                    ],
                ),
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "lambda:InvokeFunction",
                    ],
                    resources=[
                        "arn:aws:lambda:us-east-1:439780116353:function:test-deploy-mock-MockGalcierServiceCA3E1726-q666VM0l7xH5"
                    ],
                ),
            ],
        )

        state_policy.attach_to_role(
            initiate_retrieval_nested_distributed_map.state_machine.role
        )

        table.grant_write_data(initiate_retrieval_nested_distributed_map.state_machine)

        self.outputs[OutputKeys.INITIATE_RETRIEVAL_STATE_MACHINE_ARN] = CfnOutput(
            self,
            OutputKeys.INITIATE_RETRIEVAL_STATE_MACHINE_ARN,
            value=initiate_retrieval_nested_distributed_map.state_machine.state_machine_arn,
        )
