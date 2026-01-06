from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List


class DemoReplay:
    def __init__(self, data_path: Path) -> None:
        self.data = json.loads(data_path.read_text(encoding="utf-8"))
        self.index = 0

    def next_batch(self, batch_size: int = 1) -> List[dict[str, Any]]:
        if not self.data:
            return []
        batch = []
        for _ in range(batch_size):
            batch.append(self.data[self.index])
            self.index = (self.index + 1) % len(self.data)
        return batch
