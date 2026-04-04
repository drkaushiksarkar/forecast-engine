"""Application configuration with environment variable support.

Provides typed configuration loading with validation, defaults,
and environment-specific overrides.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DatabaseConfig:
    host: str = "localhost"
    port: int = 5432
    name: str = "health_intelligence"
    user: str = "app"
    password: str = ""
    pool_size: int = 10
    ssl_mode: str = "require"

    @property
    def connection_string(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}?sslmode={self.ssl_mode}"


@dataclass(frozen=True)
class S3Config:
    bucket: str = "imacs-mm-foundation-data-prod"
    region: str = "us-east-1"
    prefix: str = ""
    endpoint_url: str | None = None


@dataclass(frozen=True)
class CacheConfig:
    memory_size: int = 1024
    memory_ttl: float = 600.0
    disk_dir: str = "/tmp/cache"
    disk_ttl: float = 86400.0
    enabled: bool = True


@dataclass(frozen=True)
class AppConfig:
    env: str = "production"
    debug: bool = False
    log_level: str = "INFO"
    log_json: bool = True
    service_name: str = "health-intelligence"
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    s3: S3Config = field(default_factory=S3Config)
    cache: CacheConfig = field(default_factory=CacheConfig)

    @classmethod
    def from_env(cls) -> AppConfig:
        return cls(
            env=os.getenv("APP_ENV", "production"),
            debug=os.getenv("APP_DEBUG", "").lower() in ("1", "true"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            log_json=os.getenv("LOG_JSON", "true").lower() != "false",
            service_name=os.getenv("SERVICE_NAME", "health-intelligence"),
            database=DatabaseConfig(
                host=os.getenv("DB_HOST", "localhost"),
                port=int(os.getenv("DB_PORT", "5432")),
                name=os.getenv("DB_NAME", "health_intelligence"),
                user=os.getenv("DB_USER", "app"),
                password=os.getenv("DB_PASSWORD", ""),
                pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
            ),
            s3=S3Config(
                bucket=os.getenv("S3_BUCKET", "imacs-mm-foundation-data-prod"),
                region=os.getenv("AWS_REGION", "us-east-1"),
            ),
            cache=CacheConfig(
                memory_size=int(os.getenv("CACHE_MEMORY_SIZE", "1024")),
                enabled=os.getenv("CACHE_ENABLED", "true").lower() != "false",
            ),
        )
