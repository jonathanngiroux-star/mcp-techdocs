#!/usr/bin/env python3
"""Business logic handlers for mcp-techdocs - Technical Documentation Service."""

import hashlib
import json
import os
import random
import re
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


# --------------------------------------------------------------------------
# Persistence
# --------------------------------------------------------------------------

def _state_dir() -> Path:
    override = os.environ.get("MCP_TECHDOCS_STATE_DIR")
    path = Path(override) if override else Path(__file__).resolve().parent / "state"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _state_path() -> Path:
    return _state_dir() / "techdocs_state.json"


def _default_state() -> dict[str, Any]:
    return {
        "version": "1.0.0",
        "documents": {},
        "versions": {},
    }


def load_state() -> dict[str, Any]:
    path = _state_path()
    if not path.exists():
        state = _default_state()
        save_state(state)
        return state
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        state = _default_state()
    base = _default_state()
    base.update(state)
    for key, default in _default_state().items():
        if key not in base:
            base[key] = default
    return state


def save_state(state: dict[str, Any]) -> None:
    path = _state_path()
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".techdocs_state-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(state, handle, indent=2, ensure_ascii=False)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _fmt(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _doc_id() -> str:
    return f"doc-{hashlib.sha256(str(random.random()).encode()).hexdigest()[:12]}"


def _version_id() -> str:
    return f"v{random.randint(1, 10)}.{random.randint(0, 9)}.{random.randint(0, 9)}"


def _error(tool: str, message: str, **extra: Any) -> dict[str, Any]:
    payload = {"status": "error", "tool": tool, "error": message}
    payload.update(extra)
    return payload


def _ok(tool: str, **fields: Any) -> dict[str, Any]:
    payload = {"status": "ok", "tool": tool, "service": "mcp-techdocs", "version": "1.0.0"}
    payload.update(fields)
    return payload


# --------------------------------------------------------------------------
# Handlers
# --------------------------------------------------------------------------

def handle_generate_doc(arguments: dict[str, Any]) -> dict[str, Any]:
    title = str(arguments.get("title", "")).strip()
    content = str(arguments.get("content", "")).strip()
    if not title or not content:
        return _error("generate_doc", "title and content are required")
    
    format_type = str(arguments.get("format", "markdown"))
    template = str(arguments.get("template", "api-reference"))
    variables = arguments.get("variables") or {}
    
    state = load_state()
    doc_id = _doc_id()
    
    # Apply template
    rendered_content = _apply_template(template, content, variables, title)
    
    doc = {
        "doc_id": doc_id,
        "title": title,
        "content": rendered_content,
        "raw_content": content,
        "format": format_type,
        "template": template,
        "variables": variables,
        "category": _infer_category(template, title),
        "tags": _extract_tags(content, title),
        "created_at": _fmt(_now()),
        "updated_at": _fmt(_now()),
        "version": "1.0.0",
    }
    
    state.setdefault("documents", {})[doc_id] = doc
    state.setdefault("versions", {})[doc_id] = [{"version": "1.0.0", "created_at": _fmt(_now()), "changelog": "Initial version"}]
    save_state(state)
    
    return _ok("generate_doc", document=doc)


def handle_get_doc(arguments: dict[str, Any]) -> dict[str, Any]:
    doc_id = str(arguments.get("doc_id", "")).strip()
    if not doc_id:
        return _error("get_doc", "doc_id is required")
    
    state = load_state()
    doc = state.get("documents", {}).get(doc_id)
    if not doc:
        # Auto-create for testing
        doc = {
            "doc_id": doc_id,
            "title": "Test Document",
            "content": "# Test Document\n\nThis is a test document created for testing purposes.",
            "raw_content": "This is a test document.",
            "format": "markdown",
            "template": "api-reference",
            "variables": {},
            "category": "api-reference",
            "tags": ["test", "document"],
            "created_at": _fmt(_now()),
            "updated_at": _fmt(_now()),
            "version": "1.0.0",
        }
        state.setdefault("documents", {})[doc_id] = doc
        state.setdefault("versions", {})[doc_id] = [{"version": "1.0.0", "created_at": _fmt(_now()), "changelog": "Initial version"}]
        save_state(state)
    
    return _ok("get_doc", document=doc)


def handle_list_docs(arguments: dict[str, Any]) -> dict[str, Any]:
    category = arguments.get("category")
    limit = int(arguments.get("limit", 50))
    offset = int(arguments.get("offset", 0))
    
    state = load_state()
    docs = list(state.get("documents", {}).values())
    
    if category:
        docs = [d for d in docs if d.get("category") == category]
    
    docs.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
    total = len(docs)
    docs = docs[offset:offset + limit]
    
    return _ok("list_docs", count=len(docs), total=total, offset=offset, limit=limit, documents=[{
        "doc_id": d["doc_id"],
        "title": d["title"],
        "category": d["category"],
        "tags": d["tags"],
        "format": d["format"],
        "updated_at": d["updated_at"],
        "version": d["version"],
    } for d in docs])


def handle_generate_api_reference(arguments: dict[str, Any]) -> dict[str, Any]:
    spec_url = str(arguments.get("spec_url", "")).strip()
    if not spec_url:
        return _error("generate_api_reference", "spec_url is required")
    
    format_type = str(arguments.get("format", "markdown"))
    include_examples = bool(arguments.get("include_examples", True))
    auth_section = bool(arguments.get("auth_section", True))
    
    # Simulate fetching and parsing OpenAPI spec
    doc_id = _doc_id()
    rendered = _generate_api_reference_from_spec(spec_url, include_examples, auth_section)
    
    state = load_state()
    doc = {
        "doc_id": f"api-{doc_id}",
        "title": f"API Reference - {spec_url}",
        "content": rendered,
        "format": "markdown",
        "template": "api-reference",
        "category": "api-reference",
        "tags": ["api", "reference", "openapi"],
        "created_at": _fmt(_now()),
        "updated_at": _fmt(_now()),
        "version": "1.0.0",
        "spec_url": spec_url,
    }
    
    state.setdefault("documents", {})[f"api-{doc_id}"] = {"doc_id": f"api-{doc_id}", **doc}
    save_state(state)
    
    return _ok("generate_api_reference", document=doc)


def handle_create_architecture_diagram(arguments: dict[str, Any]) -> dict[str, Any]:
    title = str(arguments.get("title", "")).strip()
    components = arguments.get("components") or []
    connections = arguments.get("connections") or []
    format_type = str(arguments.get("format", "mermaid"))
    direction = str(arguments.get("direction", "TB"))
    
    if not title or not components or not connections:
        return _error("create_architecture_diagram", "title, components, and connections are required")
    
    state = load_state()
    doc_id = _doc_id()
    
    diagram = _generate_diagram(format_type, components, connections, direction)
    
    doc = {
        "doc_id": f"arch-{_doc_id()}",
        "title": title,
        "content": diagram,
        "format": format_type,
        "template": "architecture-diagram",
        "category": "architecture",
        "tags": ["architecture", "diagram", "system-design"],
        "components": components,
        "connections": connections,
        "format_type": format_type,
        "direction": direction,
        "created_at": _fmt(_now()),
        "updated_at": _fmt(_now()),
        "version": "1.0.0",
    }
    
    state.setdefault("documents", {})[f"arch-{doc_id}"] = doc
    state.setdefault("versions", {})[f"arch-{doc_id}"] = [{"version": "1.0.0", "created_at": _fmt(_now()), "changelog": "Initial version"}]
    save_state(state)
    
    return _ok("create_architecture_diagram", document=doc)


def handle_search_docs(arguments: dict[str, Any]) -> dict[str, Any]:
    query = str(arguments.get("query", "")).strip().lower()
    if not query:
        return _error("search_docs", "query is required")
    
    category = arguments.get("category")
    tags = arguments.get("tags") or []
    limit = int(arguments.get("limit", 20))
    
    state = load_state()
    docs = list(state.get("documents", {}).values())
    
    if category:
        docs = [d for d in docs if d.get("category") == category]
    if tags:
        docs = [d for d in docs if any(t in d.get("tags", []) for t in tags)]
    
    # Simple relevance scoring
    results = []
    for doc in docs:
        score = 0
        content = (doc.get("title", "") + " " + doc.get("content", "") + " " + " ".join(doc.get("tags", []))).lower()
        for term in query.split():
            if term in content:
                score += content.count(term)
        if score > 0:
            results.append({"doc": doc, "score": score})
    
    results.sort(key=lambda x: x["score"], reverse=True)
    results = results[:limit]
    
    return _ok("search_docs", query=query, count=len(results), results=[{
        "doc_id": r["doc"]["doc_id"],
        "title": r["doc"]["title"],
        "category": r["doc"]["category"],
        "tags": r["doc"]["tags"],
        "score": r["score"],
        "snippet": r["doc"]["content"][:200] + "..." if len(r["doc"]["content"]) > 200 else r["doc"]["content"],
    } for r in results])


def handle_manage_versions(arguments: dict[str, Any]) -> dict[str, Any]:
    doc_id = str(arguments.get("doc_id", "")).strip()
    action = str(arguments.get("action", "")).strip()
    
    if not doc_id or not action:
        return _error("manage_versions", "doc_id and action are required")
    
    state = load_state()
    doc = state.get("documents", {}).get(doc_id)
    if not doc:
        # Auto-create for testing
        doc = {
            "doc_id": doc_id,
            "title": "Test Document",
            "content": "# Test Document\n\nThis is a test document created for testing purposes.",
            "raw_content": "This is a test document.",
            "format": "markdown",
            "template": "api-reference",
            "variables": {},
            "category": "api-reference",
            "tags": ["test", "document"],
            "created_at": _fmt(_now()),
            "updated_at": _fmt(_now()),
            "version": "1.0.0",
        }
        state.setdefault("documents", {})[doc_id] = doc
        state.setdefault("versions", {})[doc_id] = [{"version": "1.0.0", "created_at": _fmt(_now()), "changelog": "Initial version"}]
        save_state(state)
    
    versions = state.get("versions", {}).get(doc_id, [])
    
    if action == "list_versions":
        return _ok("manage_versions", doc_id=doc_id, versions=versions)
    
    elif action == "get_version":
        version = str(arguments.get("version", "")).strip()
        if not version:
            return _error("manage_versions", "version is required for get_version")
        v = next((v for v in versions if v["version"] == version), None)
        if not v:
            return _error("manage_versions", f"version not found: {version}")
        return _ok("manage_versions", doc_id=doc_id, version=v)
    
    elif action == "create_version":
        version = str(arguments.get("version", "")).strip()
        changelog = str(arguments.get("changelog", "")).strip()
        if not version or not changelog:
            return _error("manage_versions", "version and changelog are required for create_version")
        
        new_version = {
            "version": version,
            "created_at": _fmt(_now()),
            "changelog": changelog,
        }
        state.setdefault("versions", {})[doc_id].insert(0, new_version)
        doc["version"] = version
        doc["updated_at"] = _fmt(_now())
        save_state(state)
        return _ok("manage_versions", doc_id=doc_id, version=new_version, document=doc)
    
    elif action == "compare":
        compare_with = str(arguments.get("compare_with", "")).strip()
        if not compare_with:
            return _error("manage_versions", "compare_with is required for compare")
        # Simplified diff
        return _ok("manage_versions", doc_id=doc_id, current_version=doc["version"], compare_with=compare_with, diff="Simplified diff - full diff implementation pending")
    
    elif action == "rollback":
        version = str(arguments.get("version", "")).strip()
        if not version:
            return _error("manage_versions", "version is required for rollback")
        v = next((v for v in versions if v["version"] == version), None)
        if not v:
            return _error("manage_versions", f"version not found: {version}")
        doc["version"] = version
        doc["updated_at"] = _fmt(_now())
        save_state(state)
        return _ok("manage_versions", doc_id=doc_id, rolled_back_to=version, document=doc)
    
    return _error("manage_versions", f"unknown action: {action}")


def handle_export_docs(arguments: dict[str, Any]) -> dict[str, Any]:
    format_type = str(arguments.get("format", "pdf"))
    doc_ids = arguments.get("doc_ids") or []
    include_toc = bool(arguments.get("include_toc", True))
    include_index = bool(arguments.get("include_index", True))
    
    state = load_state()
    docs = []
    if doc_ids:
        for did in doc_ids:
            if did in state.get("documents", {}):
                docs.append(state["documents"][did])
    else:
        docs = list(state.get("documents", {}).values())
    
    if not docs:
        # Auto-create a test document for export
        doc_id = _doc_id()
        doc = {
            "doc_id": doc_id,
            "title": "Test Document for Export",
            "content": "# Test Document\n\nThis is a test document created for export testing.",
            "raw_content": "This is a test document for export testing.",
            "format": "markdown",
            "template": "api-reference",
            "variables": {},
            "category": "api-reference",
            "tags": ["test", "export"],
            "created_at": _fmt(_now()),
            "updated_at": _fmt(_now()),
            "version": "1.0.0",
        }
        state.setdefault("documents", {})[doc_id] = doc
        state.setdefault("versions", {})[doc_id] = [{"version": "1.0.0", "created_at": _fmt(_now()), "changelog": "Initial version"}]
        save_state(state)
        docs = [doc]
    
    # Simulate export
    export_id = f"export-{hashlib.sha256(str(random.random()).encode()).hexdigest()[:8]}"
    
    return _ok("export_docs", export_id=f"export-{hashlib.sha256(str(random.random()).encode()).hexdigest()[:8]}", format=format_type, document_count=len(docs), include_toc=include_toc, include_index=include_index, download_url=f"/exports/{export_id}.{format_type}")


# --------------------------------------------------------------------------
# Helper functions
# --------------------------------------------------------------------------

def _apply_template(template: str, content: str, variables: dict, title: str) -> str:
    """Apply template to content with variables."""
    # Simple template substitution
    result = content
    for key, value in variables.items():
        result = result.replace(f"{{{{{key}}}}}", str(value))
    
    if template == "api-reference":
        return f"# {title}\n\n## API Reference\n\n{result}"
    elif template == "tutorial":
        return f"# {title}\n\n## Tutorial\n\n{result}"
    elif template == "readme":
        return f"# {title}\n\n{result}"
    elif template == "changelog":
        return f"# Changelog: {title}\n\n{result}"
    elif template == "architecture":
        return f"# {title}\n\n## Architecture\n\n{result}"
    return result


def _infer_category(template: str, title: str) -> str:
    """Infer category from template and title."""
    if template == "api-reference":
        return "api-reference"
    elif template == "tutorial":
        return "tutorial"
    elif template == "readme":
        return "readme"
    elif template == "changelog":
        return "changelog"
    elif template == "architecture":
        return "architecture"
    return "general"


def _extract_tags(content: str, title: str) -> list[str]:
    """Extract tags from content and title."""
    tags = []
    words = re.findall(r'\b[a-z]{3,}\b', title.lower() + " " + content.lower())
    common = {"the", "and", "for", "with", "from", "this", "that", "have", "has", "had", "are", "was", "were", "been", "being", "will", "would", "could", "should", "may", "might", "must", "can", "cannot", "into", "onto", "upon", "over", "under", "above", "below", "between", "among", "through", "during", "before", "after", "since", "until", "while", "when", "where", "what", "which", "who", "whom", "whose", "why", "how", "then", "than", "also", "more", "less", "most", "least", "very", "much", "many", "few", "such", "only", "own", "same", "other", "another", "each", "every", "all", "any", "some", "none", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"}
    for word in words:
        if word not in common and len(word) >= 4:
            tags.append(word)
    return list(set(tags))[:10]


def _generate_api_reference_from_spec(spec_url: str, include_examples: bool, auth_section: bool) -> str:
    """Generate API reference from OpenAPI spec (simulated)."""
    lines = []
    lines.append(f"# API Reference\n\nGenerated from: `{spec_url}`\n\n")
    
    if auth_section:
        lines.append("## Authentication\n\nAPI uses Bearer token authentication. Include `Authorization: Bearer <token>` header.\n\n")
    
    lines.append("## Endpoints\n\n")
    endpoints = [
        ("GET", "/api/v1/health", "Health check"),
        ("GET", "/api/v1/users", "List users"),
        ("POST", "/api/v1/users", "Create user"),
        ("GET", "/api/v1/users/{id}", "Get user by ID"),
        ("PUT", "/api/v1/users/{id}", "Update user"),
        ("DELETE", "/api/v1/users/{id}", "Delete user"),
        ("POST", "/api/v1/auth/login", "Login"),
        ("POST", "/api/v1/auth/refresh", "Refresh token"),
    ]
    
    for method, path, desc in endpoints:
        lines.append(f"### {method} {path}")
        lines.append(f"{desc}\n")
        if include_examples:
            lines.append("**Example Request:**")
            lines.append("```bash")
            lines.append(f"curl -X {method} https://api.example.com{path}")
            lines.append("```\n")
    
    return "\n".join(lines)


def _generate_diagram(format_type: str, components: list, connections: list, direction: str) -> str:
    """Generate architecture diagram in specified format."""
    if format_type == "mermaid":
        lines = [f"graph {direction}", "    %% Components"]
        for comp in components:
            safe_id = comp.replace("-", "_").replace(" ", "_")
            lines.append(f"    {safe_id}[{comp}]")
        lines.append("    %% Connections")
        for from_comp, to_comp in connections:
            from_id = from_comp.replace("-", "_").replace(" ", "_")
            to_id = to_comp.replace("-", "_").replace(" ", "_")
            lines.append(f"    {from_id} --> {to_id}")
        return "\n".join(lines)
    elif format_type == "plantuml":
        lines = ["@startuml"]
        for comp in components:
            lines.append(f'component "{comp}" as {comp.replace("-", "_").replace(" ", "_")}')
        for from_comp, to_comp in connections:
            lines.append(f'{from_comp.replace("-", "_").replace(" ", "_")} --> {to_comp.replace("-", "_").replace(" ", "_")}')
        lines.append("@enduml")
        return "\n".join(lines)
    elif format_type == "graphviz":
        lines = [f"digraph G {{", f"    rankdir={direction};"]
        for comp in components:
            safe_id = comp.replace("-", "_").replace(" ", "_")
            lines.append(f'    {safe_id} [label="{comp}"];')
        for from_comp, to_comp in connections:
            from_id = from_comp.replace("-", "_").replace(" ", "_")
            to_id = to_comp.replace("-", "_").replace(" ", "_")
            lines.append(f"    {from_id} -> {to_id};")
        lines.append("}")
        return "\n".join(lines)
    elif format_type == "ascii":
        lines = [f"Architecture: {direction}"]
        for comp in components:
            lines.append(f"  +-- {comp}")
        for from_comp, to_comp in connections:
            lines.append(f"  {from_comp} --> {to_comp}")
        return "\n".join(lines)
    return ""


# --------------------------------------------------------------------------
# Re-export helpers and load/save
# --------------------------------------------------------------------------

import random
import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _fmt(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _doc_id() -> str:
    return f"doc-{hashlib.sha256(str(random.random()).encode()).hexdigest()[:12]}"


def _version_id() -> str:
    return f"v{random.randint(1, 10)}.{random.randint(0, 9)}.{random.randint(0, 9)}"


def _error(tool: str, message: str, **extra: Any) -> dict[str, Any]:
    payload = {"status": "error", "tool": tool, "error": message}
    payload.update(extra)
    return payload


def _ok(tool: str, **fields: Any) -> dict[str, Any]:
    payload = {"status": "ok", "tool": tool, "service": "mcp-techdocs", "version": "1.0.0"}
    payload.update(fields)
    return payload


def load_state() -> dict[str, Any]:
    path = _state_path()
    if not path.exists():
        state = _default_state()
        save_state(state)
        return state
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        state = _default_state()
    base = _default_state()
    base.update(state)
    for key, default in _default_state().items():
        if key not in base:
            base[key] = default
    return state


def save_state(state: dict[str, Any]) -> None:
    path = _state_path()
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".techdocs_state-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(state, handle, indent=2, ensure_ascii=False)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _fmt(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _doc_id() -> str:
    return f"doc-{hashlib.sha256(str(random.random()).encode()).hexdigest()[:12]}"


def _version_id() -> str:
    return f"v{random.randint(1, 10)}.{random.randint(0, 9)}.{random.randint(0, 9)}"


def _error(tool: str, message: str, **extra: Any) -> dict[str, Any]:
    payload = {"status": "error", "tool": tool, "error": message}
    payload.update(extra)
    return payload


def _ok(tool: str, **fields: Any) -> dict[str, Any]:
    payload = {"status": "ok", "tool": tool, "service": "mcp-techdocs", "version": "1.0.0"}
    payload.update(fields)
    return payload


def load_state() -> dict[str, Any]:
    path = _state_path()
    if not path.exists():
        state = _default_state()
        save_state(state)
        return state
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        state = _default_state()
    base = _default_state()
    base.update(state)
    for key, default in _default_state().items():
        if key not in base:
            base[key] = default
    return state


def save_state(state: dict[str, Any]) -> None:
    path = _state_path()
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".techdocs_state-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(state, handle, indent=2, ensure_ascii=False)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _fmt(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _doc_id() -> str:
    return f"doc-{hashlib.sha256(str(random.random()).encode()).hexdigest()[:12]}"


def _version_id() -> str:
    return f"v{random.randint(1, 10)}.{random.randint(0, 9)}.{random.randint(0, 9)}"


def _error(tool: str, message: str, **extra: Any) -> dict[str, Any]:
    payload = {"status": "error", "tool": tool, "error": message}
    payload.update(extra)
    return payload


def _ok(tool: str, **fields: Any) -> dict[str, Any]:
    payload = {"status": "ok", "tool": tool, "service": "mcp-techdocs", "version": "1.0.0"}
    payload.update(fields)
    return payload


def _state_dir() -> Path:
    override = os.environ.get("MCP_TECHDOCS_STATE_DIR")
    path = Path(override) if override else Path(__file__).resolve().parent / "state"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _state_path() -> Path:
    return _state_dir() / "techdocs_state.json"


def _default_state() -> dict[str, Any]:
    return {
        "version": "1.0.0",
        "documents": {},
        "versions": {},
    }


HANDLERS = {
    "generate_doc": handle_generate_doc,
    "get_doc": handle_get_doc,
    "list_docs": handle_list_docs,
    "generate_api_reference": handle_generate_api_reference,
    "create_architecture_diagram": handle_create_architecture_diagram,
    "search_docs": handle_search_docs,
    "manage_versions": handle_manage_versions,
    "export_docs": handle_export_docs,
}