import json
from typing import Any

from config import settings


def get_benchmark_data() -> list[dict[str, Any]]:
    input_data = {}
    with open(settings.BENCHMARK_INPUT_FILE_PATH) as f:
        for line in f:
            if line.strip():
                item = json.loads(line)
                input_data[item["instance_id"]] = item

    gt_data = {}
    with open(settings.BENCHMARK_GT_FILE_PATH) as f:
        for line in f:
            if line.strip():
                item = json.loads(line)
                gt_data[item["instance_id"]] = item

    merged_data = []
    for instance_id, item in input_data.items():
        if instance_id in gt_data:
            item.update(gt_data[instance_id])
            merged_data.append(item)

    return merged_data
