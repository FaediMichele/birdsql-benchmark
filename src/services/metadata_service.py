import json
import os
from pathlib import Path

from config import settings
from models.schemas import ColumnMeaning, DatabaseMetadata, KnowledgeBaseItem


def get_database_metadata(database_name: str) -> DatabaseMetadata:
    db_path = Path(settings.METADATA_PATH) / database_name

    if not db_path.exists():
        raise FileNotFoundError(f"Metadata for database {database_name} not found in {settings.METADATA_PATH}")

    # Load Schema DDL
    schema_file = db_path / f"{database_name}_schema.txt"
    schema_ddl = ""
    if schema_file.exists():
        with open(schema_file, encoding="utf-8") as f:
            schema_ddl = f.read()

    # Load Column Meanings
    # Format is usually "db|table|col": "description"
    column_file = db_path / f"{database_name}_column_meaning_base.json"
    column_meanings = []
    if column_file.exists():
        with open(column_file, encoding="utf-8") as f:
            raw_meanings = json.load(f)
            for key, val in raw_meanings.items():
                parts = key.split("|")
                if len(parts) >= 3:
                    # If val is a dict, extract column_meaning or just stringify it
                    if isinstance(val, dict):
                        description = val.get("column_meaning", str(val))
                    else:
                        description = str(val)

                    column_meanings.append(
                        ColumnMeaning(table_name=parts[1], column_name=parts[2], description=description)
                    )

    # Load Knowledge Base (JSONL)
    kb_file = db_path / f"{database_name}_kb.jsonl"
    knowledge_base = []
    if kb_file.exists():
        with open(kb_file, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    item = json.loads(line)
                    knowledge_base.append(
                        KnowledgeBaseItem(
                            id=item.get("id"),
                            knowledge=item.get("knowledge"),
                            description=item.get("description"),
                            definition=item.get("definition"),
                            type=item.get("type"),
                        )
                    )

    return DatabaseMetadata(
        database_name=database_name,
        schema_ddl=schema_ddl,
        column_meanings=column_meanings,
        knowledge_base=knowledge_base,
    )


def list_databases() -> list[str]:
    metadata_path = Path(settings.METADATA_PATH)
    if not metadata_path.exists():
        return []
    return [d for d in os.listdir(metadata_path) if (metadata_path / d).is_dir() and not d.startswith(".")]
