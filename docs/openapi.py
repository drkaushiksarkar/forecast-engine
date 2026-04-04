"""OpenAPI specification generator with automatic endpoint discovery."""
from __future__ import annotations
import inspect, json, re
from dataclasses import dataclass, field
from typing import Any, Callable, Optional, get_type_hints

@dataclass
class APIEndpoint:
    path: str
    method: str
    summary: str
    description: str = ""
    parameters: list[dict[str, Any]] = field(default_factory=list)
    request_body: Optional[dict[str, Any]] = None
    responses: dict[str, dict[str, Any]] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    deprecated: bool = False

class OpenAPIGenerator:
    def __init__(self, title: str, version: str = "1.0.0", description: str = "") -> None:
        self.title = title
        self.version = version
        self.description = description
        self._endpoints: list[APIEndpoint] = []
        self._schemas: dict[str, dict] = {}
        self._tags: list[dict[str, str]] = []

    def add_endpoint(self, endpoint: APIEndpoint) -> None:
        self._endpoints.append(endpoint)

    def add_schema(self, name: str, schema: dict[str, Any]) -> None:
        self._schemas[name] = schema

    def add_tag(self, name: str, description: str = "") -> None:
        self._tags.append({"name": name, "description": description})

    def from_function(self, path: str, method: str, func: Callable, tags: Optional[list[str]] = None) -> APIEndpoint:
        sig = inspect.signature(func)
        doc = inspect.getdoc(func) or ""
        lines = doc.split("\n")
        summary = lines[0] if lines else func.__name__
        description = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""
        params = []
        for name, param in sig.parameters.items():
            if name in ("self", "cls", "request", "response"): continue
            p: dict[str, Any] = {"name": name, "in": "query", "required": param.default == inspect.Parameter.empty}
            annotation = param.annotation
            if annotation != inspect.Parameter.empty:
                if annotation == int: p["schema"] = {"type": "integer"}
                elif annotation == float: p["schema"] = {"type": "number"}
                elif annotation == bool: p["schema"] = {"type": "boolean"}
                elif annotation == str: p["schema"] = {"type": "string"}
                else: p["schema"] = {"type": "string"}
            if param.default != inspect.Parameter.empty and param.default is not None:
                p["schema"] = p.get("schema", {}); p["schema"]["default"] = param.default
            params.append(p)
        endpoint = APIEndpoint(path=path, method=method.upper(), summary=summary,
            description=description, parameters=params, tags=tags or [],
            responses={"200": {"description": "Successful response"},
                       "400": {"description": "Bad request"},
                       "500": {"description": "Internal server error"}})
        self._endpoints.append(endpoint)
        return endpoint

    def generate(self) -> dict[str, Any]:
        paths: dict[str, dict] = {}
        for ep in self._endpoints:
            if ep.path not in paths: paths[ep.path] = {}
            operation: dict[str, Any] = {"summary": ep.summary, "responses": ep.responses}
            if ep.description: operation["description"] = ep.description
            if ep.parameters: operation["parameters"] = ep.parameters
            if ep.request_body: operation["requestBody"] = ep.request_body
            if ep.tags: operation["tags"] = ep.tags
            if ep.deprecated: operation["deprecated"] = True
            paths[ep.path][ep.method.lower()] = operation
        spec: dict[str, Any] = {
            "openapi": "3.0.3",
            "info": {"title": self.title, "version": self.version, "description": self.description},
            "paths": paths,
        }
        if self._tags: spec["tags"] = self._tags
        if self._schemas: spec["components"] = {"schemas": self._schemas}
        return spec

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.generate(), indent=indent)

    def to_yaml(self) -> str:
        spec = self.generate()
        lines = ["openapi: '3.0.3'", f"info:", f"  title: '{self.title}'",
                 f"  version: '{self.version}'", f"  description: '{self.description}'", "paths:"]
        for path, methods in spec.get("paths", {}).items():
            lines.append(f"  {path}:")
            for method, op in methods.items():
                lines.append(f"    {method}:")
                lines.append(f"      summary: '{op.get('summary', '')}'")
                if op.get("tags"): lines.append(f"      tags: {op['tags']}")
        return "\n".join(lines)
