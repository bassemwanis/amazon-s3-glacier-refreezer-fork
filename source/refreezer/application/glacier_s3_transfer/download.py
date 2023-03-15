"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import boto3
import typing

from refreezer.application.util.exceptions import AccessViolation

if typing.TYPE_CHECKING:
    from mypy_boto3_glacier.client import GlacierClient
    from mypy_boto3_glacier.type_defs import GetJobOutputOutputTypeDef
else:
    GlacierClient = object
    GetJobOutputOutputTypeDef = object


class GlacierDownload:
    def __init__(
        self,
        job_id: str,
        vault_name: str,
        start_byte: int,
        end_byte: int,
    ) -> None:
        self.params = {
            "jobId": job_id,
            "range": f"bytes={start_byte}-{end_byte}",
            "vaultName": vault_name,
        }
        self.glacier: GlacierClient = boto3.client("glacier")
        self.response: GetJobOutputOutputTypeDef = self.glacier.get_job_output(
            **self.params
        )
        self.accessed = False

    def read(self) -> bytes:
        if self.accessed:
            raise AccessViolation()
        self.accessed = True
        return self.response["body"].read()

    def checksum(self) -> typing.Optional[str]:
        return self.response.get("checksum")