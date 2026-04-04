"""Tests for configuration management."""
import json, os
import pytest

class TestConfigManager:
    def test_basic_get(self):
        from config.manager import ConfigManager
        cm = ConfigManager(); cm.add_source("test", {"db": {"host": "localhost", "port": 5432}})
        assert cm.get("db.host") == "localhost"; assert cm.get("db.port") == 5432
    def test_default_value(self):
        from config.manager import ConfigManager
        cm = ConfigManager(); assert cm.get("missing.key", "default") == "default"
    def test_require_raises(self):
        from config.manager import ConfigManager
        cm = ConfigManager()
        with pytest.raises(KeyError): cm.require("missing")
    def test_layered_sources(self):
        from config.manager import ConfigManager
        cm = ConfigManager()
        cm.add_source("base", {"db": {"host": "base-host", "port": 5432}}, priority=0)
        cm.add_source("override", {"db": {"host": "prod-host"}}, priority=10)
        assert cm.get("db.host") == "prod-host"; assert cm.get("db.port") == 5432
    def test_env_source(self, monkeypatch):
        from config.manager import ConfigManager
        monkeypatch.setenv("MYAPP_DB__HOST", "env-host")
        monkeypatch.setenv("MYAPP_DB__PORT", "3306")
        cm = ConfigManager(); cm.add_env_source("MYAPP")
        assert cm.get("db.host") == "env-host"; assert cm.get("db.port") == 3306
    def test_validation(self):
        from config.manager import ConfigManager, ConfigValidationError
        cm = ConfigManager()
        cm.add_validator(lambda c: ["port required"] if "port" not in c else [])
        with pytest.raises(ConfigValidationError): cm.add_source("bad", {"host": "x"})
    def test_change_watcher(self):
        from config.manager import ConfigManager
        cm = ConfigManager(); changes = []
        cm.on_change(lambda old, new: changes.append((old, new)))
        cm.add_source("v1", {"key": "a"}); cm.add_source("v2", {"key": "b"}, priority=10)
        assert len(changes) == 1
