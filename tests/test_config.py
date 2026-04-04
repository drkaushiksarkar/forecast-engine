"""Tests for application configuration."""
import os
import pytest
from config import AppConfig, DatabaseConfig, S3Config, CacheConfig


class TestDatabaseConfig:
    def test_defaults(self):
        cfg = DatabaseConfig()
        assert cfg.host == "localhost"
        assert cfg.port == 5432
        assert cfg.pool_size == 10

    def test_connection_string(self):
        cfg = DatabaseConfig(host="db.example.com", port=5432, name="testdb", user="admin", password="secret")
        cs = cfg.connection_string
        assert "db.example.com" in cs
        assert "admin:secret" in cs
        assert "testdb" in cs


class TestS3Config:
    def test_defaults(self):
        cfg = S3Config()
        assert cfg.bucket == "imacs-mm-foundation-data-prod"
        assert cfg.region == "us-east-1"


class TestAppConfig:
    def test_defaults(self):
        cfg = AppConfig()
        assert cfg.env == "production"
        assert cfg.debug is False
        assert cfg.log_level == "INFO"

    def test_from_env(self, monkeypatch):
        monkeypatch.setenv("APP_ENV", "staging")
        monkeypatch.setenv("APP_DEBUG", "true")
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        monkeypatch.setenv("DB_HOST", "staging-db")
        monkeypatch.setenv("DB_PORT", "5433")
        monkeypatch.setenv("S3_BUCKET", "test-bucket")
        cfg = AppConfig.from_env()
        assert cfg.env == "staging"
        assert cfg.debug is True
        assert cfg.log_level == "DEBUG"
        assert cfg.database.host == "staging-db"
        assert cfg.database.port == 5433
        assert cfg.s3.bucket == "test-bucket"

    def test_cache_config(self):
        cfg = CacheConfig()
        assert cfg.enabled is True
        assert cfg.memory_size == 1024
