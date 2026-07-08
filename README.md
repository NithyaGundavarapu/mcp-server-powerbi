# MCP Server for Power BI

A Python-based [Model Context Protocol](https://modelcontextprotocol.io) server that exposes Power BI semantic models to Claude and Claude Code, enabling natural-language querying of your Power BI data from any MCP-compatible chat client.

## What this project does

This implementation provides MCP tools to:

- list Power BI workspaces
- list datasets inside a workspace
- inspect dataset metadata
- list the tables and columns in a semantic model
- execute DAX queries against a dataset
- trigger a dataset refresh

This makes it possible for Claude to answer questions such as:

- “Which workspaces do I have access to?”
- “Show me the datasets in the Sales workspace.”
- “Run a DAX query against the Finance dataset.”

## Architecture

```mermaid
flowchart LR
    A[Claude / Claude Code] --> B[MCP Client]
    B --> C[MCP Server - Python]
    C --> D[Power BI REST API]
    D --> E[Power BI Semantic Model]
```

## Prerequisites

- Python 3.10+
- A Power BI service principal or user account with access to the required workspaces
- Power BI tenant ID, client ID, and client secret for service principal authentication

## Setup

1. Create and activate a virtual environment
2. Install dependencies
3. Copy the environment template and set your credentials
4. Run the server

### 1) Create a virtual environment

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 2) Install dependencies

```bash
pip install -r requirements.txt
```

### 3) Configure environment variables

```bash
copy .env.example .env
```

Update .env with your values:

```env
POWERBI_TENANT_ID=your-tenant-id
POWERBI_CLIENT_ID=your-client-id
POWERBI_CLIENT_SECRET=your-client-secret
```

### 4) Run the server

```bash
python -m powerbi_mcp_server.server
```

### 5) Connect it to Claude Desktop or Claude Code

Point your MCP client config at this server — see [examples/claude_desktop_config.json](examples/claude_desktop_config.json) for a ready-to-copy snippet, and [examples/demo_prompts.md](examples/demo_prompts.md) for prompts to try once it's connected.

## MCP tools exposed

- `list_workspaces()`
- `list_datasets(workspace_id)`
- `get_dataset_details(workspace_id, dataset_id)`
- `get_dataset_metadata(workspace_id, dataset_id)`
- `list_dataset_tables(workspace_id, dataset_id)`
- `execute_dax_query(workspace_id, dataset_id, dax_query)`
- `refresh_dataset(workspace_id, dataset_id)`

## Running tests

```bash
pip install pytest
python -m pytest tests/ -v
```

## Authentication

This server authenticates via an Azure AD **service principal** (client credentials flow). The service principal must be added to the Power BI tenant's allowed service principals and granted access to the relevant workspaces. Interactive/user-delegated login is a possible future addition if you need a lighter-weight local demo flow.

## Next steps

- add interactive user-login (device code) auth as an alternative to the service principal flow
- add a tool that surfaces DAX measures per table for richer natural-language grounding
- capture a short screen recording/GIF of a live Claude session for the README

## License

[MIT](LICENSE)
