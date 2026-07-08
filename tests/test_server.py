import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from powerbi_mcp_server.server import summarize_table_payload


def test_summarize_table_payload_extracts_tables_and_columns():
    payload = {
        "value": [
            {
                "name": "Sales",
                "columns": [
                    {"name": "OrderID", "dataType": "Int64"},
                    {"name": "Amount", "dataType": "Decimal"},
                ],
            },
            {
                "name": "Customers",
                "columns": [
                    {"name": "CustomerID", "dataType": "String"},
                ],
            },
        ]
    }

    summary = summarize_table_payload(payload)

    assert summary["table_count"] == 2
    assert summary["tables"][0]["name"] == "Sales"
    assert summary["tables"][0]["column_count"] == 2
    assert summary["tables"][0]["columns"][0]["name"] == "OrderID"
