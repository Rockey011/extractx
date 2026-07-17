"""
Export extracted data to various formats.
"""

import csv
import json
import io
from typing import Any, Optional


def to_json(data: Any, pretty: bool = True) -> str:
    """Convert data to JSON string."""
    indent = 2 if pretty else None
    return json.dumps(data, indent=indent, ensure_ascii=False, default=str)


def to_csv(data: list, columns: Optional[list] = None) -> str:
    """Convert list of dicts to CSV string."""
    if not data:
        return ""
    
    if not columns:
        columns = list(data[0].keys())
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=columns, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(data)
    
    return output.getvalue()


def save_file(content: str, filepath: str) -> str:
    """Save content to a file and return the absolute path."""
    import os
    filepath = os.path.abspath(filepath)
    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    
    return filepath


def export(data: Any, format: str = "json", output: str = "") -> str:
    """
    Export data to the specified format.
    
    Args:
        data: The data to export
        format: 'json', 'csv', or 'md' (markdown table)
        output: File path to save to (prints to stdout if empty)
    
    Returns:
        The formatted string
    """
    if format == "json":
        result = to_json(data)
    elif format == "csv":
        if isinstance(data, list):
            result = to_csv(data)
        elif isinstance(data, dict) and "items" in data:
            result = to_csv(data["items"])
        else:
            # Try to convert single dict to list
            result = to_csv([data])
    elif format == "md":
        result = _to_markdown(data)
    else:
        result = str(data)
    
    if output:
        save_file(result, output)
        return f"Saved to {output}"
    
    return result


def _to_markdown(data: Any) -> str:
    """Convert data to a markdown table."""
    if isinstance(data, list) and len(data) > 0:
        keys = list(data[0].keys())
        header = "| " + " | ".join(keys) + " |"
        sep = "|" + "|".join([" --- " for _ in keys]) + "|"
        rows = []
        for item in data:
            row = "| " + " | ".join(str(item.get(k, "")) for k in keys) + " |"
            rows.append(row)
        return "\n".join([header, sep] + rows)
    
    if isinstance(data, dict):
        lines = []
        for k, v in data.items():
            if not k.startswith("_"):
                lines.append(f"- **{k}**: {v}")
        return "\n".join(lines)
    
    return str(data)
