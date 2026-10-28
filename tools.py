#!/usr/bin/env python3
"""Tool definitions for mcp-techdocs - Technical Documentation Service."""

from mcp.types import Tool

TOOLS: list = [
    Tool(
        name="generate_doc",
        description="Generate documentation from source code, specifications, or templates.",
        inputSchema={
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Document title."},
                "content": {"type": "string", "description": "Source content or template variables."},
                "format": {"type": "string", "enum": ["markdown", "html", "pdf", "rst", "asciidoc"], "default": "markdown"},
                "template": {"type": "string", "enum": ["api-reference", "tutorial", "readme", "changelog", "architecture", "custom"], "default": "api-reference"},
                "variables": {"type": "object", "description": "Template variables for substitution."},
            },
            "required": ["title", "content"],
        },
    ),
    Tool(
        name="get_doc",
        description="Retrieve a generated document by ID.",
        inputSchema={
            "type": "object",
            "properties": {
                "doc_id": {"type": "string", "description": "Document identifier."},
            },
            "required": ["doc_id"],
        },
    ),
    Tool(
        name="list_docs",
        description="List all generated documents with optional filtering.",
        inputSchema={
            "type": "object",
            "properties": {
                "category": {"type": "string", "description": "Filter by category."},
                "limit": {"type": "integer", "default": 50, "description": "Maximum results."},
                "offset": {"type": "integer", "default": 0, "description": "Pagination offset."},
            },
            "required": [],
        },
    ),
    Tool(
        name="generate_api_reference",
        description="Generate API reference documentation from OpenAPI/Swagger spec.",
        inputSchema={
            "type": "object",
            "properties": {
                "spec_url": {"type": "string", "description": "URL or path to OpenAPI/Swagger specification."},
                "format": {"type": "string", "enum": ["markdown", "html", "pdf"], "default": "markdown"},
                "include_examples": {"type": "boolean", "default": True},
                "auth_section": {"type": "boolean", "default": True},
            },
            "required": ["spec_url"],
        },
    ),
    Tool(
        name="create_architecture_diagram",
        description="Generate architecture diagram from component definitions.",
        inputSchema={
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Diagram title."},
                "components": {"type": "array", "items": {"type": "string"}, "description": "List of component names."},
                "connections": {"type": "array", "items": {"type": "array", "items": {"type": "string"}, "minItems": 2, "maxItems": 2}, "description": "List of [from, to] connections."},
                "format": {"type": "string", "enum": ["mermaid", "plantuml", "graphviz", "ascii"], "default": "mermaid"},
                "direction": {"type": "string", "enum": ["TB", "TD", "LR", "RL"], "default": "TB"},
            },
            "required": ["title", "components", "connections"],
        },
    ),
    Tool(
        name="search_docs",
        description="Search documents by query with optional filters.",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query."},
                "category": {"type": "string", "description": "Filter by category."},
                "tags": {"type": "array", "items": {"type": "string"}, "description": "Filter by tags."},
                "limit": {"type": "integer", "default": 20, "description": "Maximum results."},
            },
            "required": ["query"],
        },
    ),
    Tool(
        name="manage_versions",
        description="Manage document versions (create, list, compare, rollback).",
        inputSchema={
            "type": "object",
            "properties": {
                "doc_id": {"type": "string", "description": "Document identifier."},
                "action": {"type": "string", "enum": ["create_version", "list_versions", "get_version", "compare", "rollback"], "description": "Version management action."},
                "version": {"type": "string", "description": "Version identifier (for create_version, get_version, rollback)."},
                "changelog": {"type": "string", "description": "Changelog for new version."},
                "compare_with": {"type": "string", "description": "Version to compare with (for compare action)."},
            },
            "required": ["doc_id", "action"],
        },
    ),
    Tool(
        name="export_docs",
        description="Export documents to various formats.",
        inputSchema={
            "type": "object",
            "properties": {
                "format": {"type": "string", "enum": ["pdf", "html", "epub", "docx", "zip"], "default": "pdf"},
                "doc_ids": {"type": "array", "items": {"type": "string"}, "description": "Document IDs to export; omit for all."},
                "include_toc": {"type": "boolean", "default": True},
                "include_index": {"type": "boolean", "default": True},
            },
            "required": ["format"],
        },
    ),
]