"""Tests for CLI commands."""
import pytest
from cli.commands import create_parser, run_command


class TestCLI:
    def test_status_command(self):
        parser = create_parser()
        args = parser.parse_args(["status"])
        assert run_command(args) == 0

    def test_query_command(self):
        parser = create_parser()
        args = parser.parse_args(["query", "-i", "MALARIA_CASES", "-c", "BGD"])
        assert run_command(args) == 0

    def test_forecast_command(self):
        parser = create_parser()
        args = parser.parse_args(["forecast", "-i", "CASES", "-c", "BGD", "-H", "6"])
        assert run_command(args) == 0

    def test_export_command(self):
        parser = create_parser()
        args = parser.parse_args(["export", "-q", "malaria 2024", "-f", "csv"])
        assert run_command(args) == 0

    def test_validate_command(self):
        parser = create_parser()
        args = parser.parse_args(["validate", "-s", "who_gho", "--threshold", "0.9"])
        assert run_command(args) == 0

    def test_unknown_command(self):
        parser = create_parser()
        args = parser.parse_args([])
        assert run_command(args) == 1
