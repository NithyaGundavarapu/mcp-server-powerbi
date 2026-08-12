from __future__ import annotations

import os
from typing import Any

import httpx
import truststore
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

truststore.inject_into_ssl()


class PowerBIAPIError(RuntimeError):
    """Raised when the Power BI REST API returns an error."""

load_dotenv()

mcp = FastMCP("powerbi-mcp")

POWERBI_RESOURCE = "https://analysis.windows.net/powerbi/api/.default"
POWERBI_API_BASE = "https://api.powerbi.com/v1.0/myorg"


def get_access_token() -> str:
    tenant_id = os.getenv("POWERBI_TENANT_ID")
    client_id = os.getenv("POWERBI_CLIENT_ID")
    client_secret = os.getenv("POWERBI_CLIENT_SECRET")

    if not all([tenant_id, client_id, client_secret]):
        raise RuntimeError(
            "Missing Power BI credentials. Set POWERBI_TENANT_ID, POWERBI_CLIENT_ID, and POWERBI_CLIENT_SECRET."
        )

    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": POWERBI_RESOURCE,
    }

    response = httpx.post(token_url, data=data, timeout=30)
    response.raise_for_status()
    payload = response.json()
    return payload["access_token"]


def _api_request(method: str, path: str, *, params: dict[str, Any] | None = None, json_body: dict[str, Any] | None = None) -> Any:
    token = get_access_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    url = f"{POWERBI_API_BASE}/{path.lstrip('/')}"
    with httpx.Client(timeout=60) as client:
        try:
            response = client.request(method, url, headers=headers, params=params, json=json_body)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text if exc.response else str(exc)
            raise PowerBIAPIError(f"Power BI API request failed: {detail}") from exc
        except httpx.RequestError as exc:
            raise PowerBIAPIError(f"Power BI API request failed: {exc}") from exc

        if response.content:
            return response.json()
        return {}


def summarize_table_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Convert a Power BI table payload into a compact, Claude-friendly summary."""
    tables = payload.get("value", [])
    return {
        "table_count": len(tables),
        "tables": [
            {
                "name": table.get("name"),
                "column_count": len(table.get("columns", [])),
                "columns": [
                    {
                        "name": column.get("name"),
                        "data_type": column.get("dataType"),
                    }
                    for column in table.get("columns", [])
                ],
            }
            for table in tables
        ],
    }


@mcp.tool()
def list_workspaces() -> list[dict[str, Any]]:
    """List Power BI workspaces available to the authenticated identity."""
    payload = _api_request("GET", "groups")
    return payload.get("value", [])


@mcp.tool()
def list_datasets(workspace_id: str) -> list[dict[str, Any]]:
    """List datasets inside a specific Power BI workspace."""
    payload = _api_request("GET", f"groups/{workspace_id}/datasets")
    return payload.get("value", [])


@mcp.tool()
def get_dataset_details(workspace_id: str, dataset_id: str) -> dict[str, Any]:
    """Retrieve details for a dataset in a workspace."""
    return _api_request("GET", f"groups/{workspace_id}/datasets/{dataset_id}")


@mcp.tool()
def execute_dax_query(workspace_id: str, dataset_id: str, dax_query: str) -> dict[str, Any]:
    """Execute a DAX query against a Power BI semantic model."""
    return _api_request(
        "POST",
        f"groups/{workspace_id}/datasets/{dataset_id}/executeQueries",
        json_body={"queries": [{"query": dax_query}]},
    )


@mcp.tool()
def refresh_dataset(workspace_id: str, dataset_id: str) -> dict[str, Any]:
    """Trigger a refresh for a Power BI dataset."""
    return _api_request("POST", f"groups/{workspace_id}/datasets/{dataset_id}/refreshes")


@mcp.tool()
def get_dataset_metadata(workspace_id: str, dataset_id: str) -> dict[str, Any]:
    """Return a lightweight metadata summary for a dataset, including basic details and table information if available."""
    try:
        dataset = _api_request("GET", f"groups/{workspace_id}/datasets/{dataset_id}")
    except PowerBIAPIError as exc:
        return {
            "workspace_id": workspace_id,
            "dataset_id": dataset_id,
            "error": str(exc),
        }

    return {
        "workspace_id": workspace_id,
        "dataset_id": dataset_id,
        "name": dataset.get("name"),
        "is_refreshable": dataset.get("isRefreshable"),
        "target_storage_mode": dataset.get("targetStorageMode"),
    }


@mcp.tool()
def list_dataset_tables(workspace_id: str, dataset_id: str) -> dict[str, Any]:
    """List tables and columns for a Power BI semantic model dataset."""
    payload = _api_request("GET", f"groups/{workspace_id}/datasets/{dataset_id}/tables")
    return summarize_table_payload(payload)


if __name__ == "__main__":
    mcp.run()
