from __future__ import annotations

import json
import time
from pathlib import Path
from typing import List, Dict


class DataLogger:
    """把每一帧的人体数据持久化为 JSON 文件。"""

    def __init__(self, output_path: str = "output/pose_data.json"):
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.records: List[Dict[str, object]] = []

    def log_frame(self, frame_id: int, persons: List[Dict[str, object]]) -> None:
        frame_record = {
            "frame_id": frame_id,
            "timestamp": time.time(),
            "persons": persons,
        }
        self.records.append(frame_record)
        self._write_to_disk()

    def _write_to_disk(self) -> None:
        with self.output_path.open("w", encoding="utf-8") as handle:
            json.dump(self.records, handle, indent=2, ensure_ascii=False)
