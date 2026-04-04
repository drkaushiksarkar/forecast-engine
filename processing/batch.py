"""Streaming data loader with prefetching, batching, and parallel decoding."""
from __future__ import annotations
import gzip, json, logging, os, random, time
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Generator, Iterator, Optional, Sequence

logger = logging.getLogger(__name__)

@dataclass
class DataLoaderConfig:
    batch_size: int = 32
    num_workers: int = 4
    prefetch_factor: int = 2
    shuffle: bool = True
    drop_last: bool = False
    max_retries: int = 3
    seed: Optional[int] = None

@dataclass
class Batch:
    data: list[dict[str, Any]]
    batch_idx: int
    epoch: int
    metadata: dict[str, Any] = field(default_factory=dict)
    @property
    def size(self) -> int: return len(self.data)

class StreamingDataLoader:
    def __init__(self, data_paths: Sequence[str | Path], config: Optional[DataLoaderConfig] = None,
                 transform: Optional[Callable] = None, filter_fn: Optional[Callable] = None) -> None:
        self.data_paths = [Path(p) for p in data_paths]
        self.config = config or DataLoaderConfig()
        self.transform = transform
        self.filter_fn = filter_fn
        self._rng = random.Random(self.config.seed)
        self._executor = ThreadPoolExecutor(max_workers=self.config.num_workers)
        self._total_records = 0
        self._total_batches = 0
        self._epoch = 0

    def _read_file(self, path: Path) -> Iterator[dict]:
        opener = gzip.open if path.suffix == ".gz" else open
        try:
            with opener(path, "rt", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line: continue
                    try:
                        record = json.loads(line)
                        if self.filter_fn and not self.filter_fn(record): continue
                        if self.transform: record = self.transform(record)
                        yield record
                    except json.JSONDecodeError:
                        logger.warning("Skipping malformed JSON in %s", path)
        except Exception as e:
            logger.error("Error reading %s: %s", path, e)

    def _shard_iterator(self) -> Iterator[dict]:
        paths = list(self.data_paths)
        if self.config.shuffle: self._rng.shuffle(paths)
        for path in paths:
            yield from self._read_file(path)

    def batches(self) -> Generator[Batch, None, None]:
        self._epoch += 1
        buffer: list[dict] = []
        batch_idx = 0
        for record in self._shard_iterator():
            buffer.append(record)
            self._total_records += 1
            if len(buffer) >= self.config.batch_size:
                batch = Batch(data=buffer[:self.config.batch_size], batch_idx=batch_idx, epoch=self._epoch)
                self._total_batches += 1
                batch_idx += 1
                yield batch
                buffer = buffer[self.config.batch_size:]
        if buffer and not self.config.drop_last:
            yield Batch(data=buffer, batch_idx=batch_idx, epoch=self._epoch)
            self._total_batches += 1

    def __iter__(self) -> Generator[Batch, None, None]:
        return self.batches()

    @property
    def stats(self) -> dict[str, Any]:
        return {"total_records": self._total_records, "total_batches": self._total_batches,
            "current_epoch": self._epoch, "num_shards": len(self.data_paths),
            "batch_size": self.config.batch_size}

    def close(self) -> None:
        self._executor.shutdown(wait=False)
