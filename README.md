# mcp-techdocs

MCP server for **Technical Documentation Service** — doc generation, API reference, architecture diagrams, version management, search, and export capabilities.

## Tools

### `generate_doc`
Generate documentation from source code, specifications, or templates.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `title` | string | **required** | Document title |
| `content` | string | **required** | Source content or template variables |
| `format` | string enum | `markdown` | markdown, html, pdf, rst, asciidoc |
| `template` | string enum | `api-reference` | api-reference, tutorial, readme, changelog, architecture, custom |
| `variables` | object | - | Template variables for substitution |

Returns generated document with ID, content, metadata, and version.

### `get_doc`
Retrieve a generated document by ID.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `doc_id` | string | **required** | Document identifier |

### `list_docs`
List all generated documents with optional filtering.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `category` | string | - | Filter by category |
| `limit` | integer | 50 | Maximum results |
| `offset` | integer | 0 | Pagination offset |

### `generate_api_reference`
Generate API reference documentation from OpenAPI/Swagger spec.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `spec_url` | string | **required** | URL or path to OpenAPI/Swagger specification |
| `format` | string enum | `markdown` | markdown, html, pdf |
| `include_examples` | boolean | `true` | Include request/response examples |
| `auth_section` | boolean | `true` | Include authentication section |

Returns generated API reference document.

### `create_architecture_diagram`
Generate architecture diagram from component definitions.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `title` | string | **required** | Diagram title |
| `components` | array | **required** | List of component names |
| `connections` | array | **required** | List of [from, to] connections |
| `format` | string enum | `mermaid` | mermaid, plantuml, graphviz, ascii |
| `direction` | string enum | `TB` | TB, TD, LR, RL |

Returns generated architecture diagram.

### `search_docs`
Search documents by query with optional filters.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `query` | string | **required** | Search query |
| `category` | string | - | Filter by category |
| `tags` | array | - | Filter by tags |
| `limit` | integer | 20 | Maximum results |

Returns matching documents with relevance scores.

### `manage_versions`
Manage document versions (create, list, compare, rollback).

| Parameter | Type | Default | Description |
|---|---|---|---|
| `doc_id` | string | **required** | Document identifier |
| `action` | string enum | **required** | create_version, list_versions, get_version, compare, rollback |
| `version` | string | - | Version identifier (for create_version, get_version, rollback) |
| `changelog` | string | - | Changelog for new version |
| `compare_with` | string | - | Version to compare with (for compare action) |

Returns version info or updated document.

### `export_docs`
Export documents to various formats.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `format` | string enum | `pdf` | pdf, html, epub, docx, zip |
| `doc_ids` | array | - | Document IDs to export; omit for all |
| `include_toc` | boolean | `true` | Include table of contents |
| `include_index` | boolean | `true` | Include index |

Returns export info with download URL.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

State persisted in `./state/`. Override with `MCP_TECHDOCS_STATE_DIR`.

## Connecting to an MCP client

```json
{
  "mcpServers": {
    "techdocs": {
      "command": "python3",
      "args": ["/tmp/v3-services/mcp-techdocs/main.py"]
    }
  }
}
```

## License

MIT