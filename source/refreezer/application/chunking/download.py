"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

from typing import List


def download_chunk(
    inventory_size: int, maximum_inventory_record_size: int, chunk_size: int
) -> List[str]:

    # data = bytearray(b'1234\n123\n123456\n12345678\n123\1234\1234\123456\n12')
    data = bytearray(
        b"12345678\n12345678\n12345678\n12345678\n12345678\n12345678\n12345678\n"
    )

    N = 10
    max_record_size = 8

    data_0 = data[:N]
    print(data_0)
    data_1 = data[N - max_record_size :]
    print(data_1)
    # include all complete records in first part
    trimmed_0 = data_0[: data_0.rindex(b"\n")]
    print(trimmed_0)
    # include only incomplete record in second part
    trimmed_1 = data_1[data_1.rindex(b"\n", 0, max_record_size) + 1 :]
    print(trimmed_1)

    chunks = []
    start_index = 0
    end_index = min(inventory_size, chunk_size) - 1

    if chunk_size < maximum_inventory_record_size:
        raise Exception(
            f"Chunk size can not be smaller than maximum inventory record size: {maximum_inventory_record_size}"
        )

    while end_index < inventory_size - 1:
        chunks.append(f"{start_index}-{end_index}")
        start_index = end_index - maximum_inventory_record_size + 1
        end_index = min(start_index + chunk_size - 1, inventory_size - 1)

    chunks.append(f"{start_index}-{end_index}")
    return chunks
