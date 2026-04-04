"""Configuration management with validation, layered sources, and hot reload."""
from __future__ import annotations
import json, os, threading, time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

@dataclass
class ConfigSource:
    name: str
    priority: int
    data: dict[str, Any] = field(default_factory=dict)

class ConfigValidationError(Exception):
    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__(f"Config validation failed: {'; '.join(errors)}")

class ConfigManager:
    def __init__(self) -> None:
        self._sources: list[ConfigSource] = []
        self._merged: dict[str, Any] = {}
        self._validators: list[Callable[[dict], list[str]]] = []
        self._watchers: list[Callable[[dict, dict], None]] = []
        self._lock = threading.RLock()
        self._last_reload = 0.0

    def add_source(self, name: str, data: dict[str, Any], priority: int = 0) -> None:
        with self._lock:
            self._sources.append(ConfigSource(name=name, priority=priority, data=data))
            self._sources.sort(key=lambda s: s.priority)
            self._rebuild()

    def add_env_source(self, prefix: str = "APP", priority: int = 100) -> None:
        data = {}
        for key, value in os.environ.items():
            if key.startswith(f"{prefix}_"):
                config_key = key[len(prefix) + 1:].lower().replace("__", ".")
                data[config_key] = self._parse_value(value)
        self.add_source(f"env:{prefix}", data, priority)

    def add_file_source(self, path: str | Path, priority: int = 50) -> None:
        p = Path(path)
        if not p.exists(): return
        with open(p) as f:
            data = json.load(f)
        self.add_source(f"file:{p.name}", data, priority)

    def _parse_value(self, value: str) -> Any:
        if value.lower() in ("true", "yes", "1"): return True
        if value.lower() in ("false", "no", "0"): return False
        try: return int(value)
        except ValueError: pass
        try: return float(value)
        except ValueError: pass
        return value

    def _rebuild(self) -> None:
        old = dict(self._merged)
        merged: dict[str, Any] = {}
        for source in self._sources:
            self._deep_merge(merged, source.data)
        errors = []
        for validator in self._validators:
            errors.extend(validator(merged))
        if errors: raise ConfigValidationError(errors)
        self._merged = merged
        if old and old != merged:
            for watcher in self._watchers:
                try: watcher(old, merged)
                except Exception: pass

    def _deep_merge(self, base: dict, override: dict) -> None:
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            parts = key.split(".")
            current: Any = self._merged
            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return default
            return current

    def require(self, key: str) -> Any:
        value = self.get(key)
        if value is None: raise KeyError(f"Required config key '{key}' not found")
        return value

    def add_validator(self, validator: Callable[[dict], list[str]]) -> None:
        self._validators.append(validator)

    def on_change(self, callback: Callable[[dict, dict], None]) -> None:
        self._watchers.append(callback)

    def as_dict(self) -> dict[str, Any]:
        with self._lock: return dict(self._merged)

    def reload(self) -> None:
        with self._lock:
            self._rebuild()
            self._last_reload = time.monotonic()
