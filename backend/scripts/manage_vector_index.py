#!/usr/bin/env python
"""
Vector index management CLI.

Manage pgvector indexes on the chunks.embedding column.
Supports HNSW and IVFFlat index types with configurable parameters.

Usage:
    uv run python scripts/manage_vector_index.py status
    uv run python scripts/manage_vector_index.py create
    uv run python scripts/manage_vector_index.py drop
    uv run python scripts/manage_vector_index.py recreate

Environment Variables:
    VECTOR_INDEX_TYPE: "hnsw" (default) or "ivfflat"
    VECTOR_DISTANCE_METRIC: "cosine" (default), "l2", or "inner_product"
    VECTOR_HNSW_M: Max connections per node (default: 16)
    VECTOR_HNSW_EF_CONSTRUCTION: Construction candidate list size (default: 64)
    VECTOR_IVFFLAT_LISTS: Number of IVF lists (default: 100)
"""

import sys
import os

# Add backend directory to path so we can import app modules
# Also load .env file
try:
    from dotenv import load_dotenv

    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    load_dotenv(env_path)
except ImportError:
    pass

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import argparse
from sqlalchemy import text

from app.core.db import sync_engine
from app.core.config import get_vector_config
from app.core.vector_config import VectorIndexType

INDEX_NAME = "ix_chunks_embedding"
TABLE_NAME = "chunks"
COLUMN_NAME = "embedding"


def get_current_index_info(conn) -> dict | None:
    """
    Get information about the current vector index.

    Returns:
        dict with index info or None if no index exists
    """
    result = conn.execute(
        text(
            """
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = :table
            AND indexname = :index_name
        """
        ),
        {"table": TABLE_NAME, "index_name": INDEX_NAME},
    )
    row = result.fetchone()

    if row:
        indexdef = row.indexdef.lower()
        # Parse index type from definition
        if "using hnsw" in indexdef:
            index_type = "hnsw"
        elif "using ivfflat" in indexdef:
            index_type = "ivfflat"
        else:
            index_type = "unknown"

        return {
            "name": row.indexname,
            "type": index_type,
            "definition": row.indexdef,
        }
    return None


def get_row_count(conn) -> int:
    """Get the number of rows in the chunks table."""
    result = conn.execute(text(f"SELECT COUNT(*) FROM {TABLE_NAME}"))
    return result.scalar()


def status_command():
    """Show current index status."""
    config = get_vector_config()

    print("\n=== Vector Index Configuration ===")
    print(f"  Index Type: {config.index_type.value}")
    print(f"  Distance Metric: {config.distance_metric.value}")
    print(f"  Embedding Dimensions: {config.embedding_dimensions}")

    if config.index_type == VectorIndexType.HNSW:
        print(f"  HNSW m: {config.hnsw.m}")
        print(f"  HNSW ef_construction: {config.hnsw.ef_construction}")
    elif config.index_type == VectorIndexType.IVFFLAT:
        print(f"  IVFFlat lists: {config.ivfflat.lists}")

    print("\n=== Current Index Status ===")

    with sync_engine.connect() as conn:
        index_info = get_current_index_info(conn)
        row_count = get_row_count(conn)

        print(f"  Table: {TABLE_NAME}")
        print(f"  Row Count: {row_count:,}")

        if index_info:
            print(f"  Index Name: {index_info['name']}")
            print(f"  Index Type: {index_info['type']}")
            print(f"  Definition: {index_info['definition']}")
        else:
            print("  Index: NOT CREATED")

    print()


def create_command(force: bool = False):
    """Create the vector index based on configuration."""
    config = get_vector_config()

    if config.index_type == VectorIndexType.NONE:
        print("Index type is 'none', skipping index creation.")
        return

    with sync_engine.connect() as conn:
        # Check if index already exists
        existing = get_current_index_info(conn)
        if existing and not force:
            print(f"Index '{INDEX_NAME}' already exists (type: {existing['type']}).")
            print("Use 'recreate' command to drop and recreate, or 'drop' first.")
            return

        if existing:
            print(f"Dropping existing index '{INDEX_NAME}'...")
            conn.execute(text(f"DROP INDEX IF EXISTS {INDEX_NAME}"))
            conn.commit()

        # Get ops class for the distance metric
        ops_class = config.get_ops_class()

        print(f"\nCreating {config.index_type.value.upper()} index...")
        print(f"  Distance metric: {config.distance_metric.value}")
        print(f"  Ops class: {ops_class}")

        if config.index_type == VectorIndexType.HNSW:
            params = config.get_index_parameters()
            print(f"  m: {params['m']}")
            print(f"  ef_construction: {params['ef_construction']}")

            sql = f"""
                CREATE INDEX {INDEX_NAME}
                ON {TABLE_NAME}
                USING hnsw ({COLUMN_NAME} {ops_class})
                WITH (m = {params['m']}, ef_construction = {params['ef_construction']})
            """

        elif config.index_type == VectorIndexType.IVFFLAT:
            params = config.get_index_parameters()
            print(f"  lists: {params['lists']}")

            # Check row count for IVFFlat recommendation
            row_count = get_row_count(conn)
            if row_count < params["lists"]:
                print(
                    f"\n  WARNING: IVFFlat works best when lists <= rows."
                    f"\n  Current rows: {row_count}, lists: {params['lists']}"
                    f"\n  Consider reducing VECTOR_IVFFLAT_LISTS or adding more data first."
                )

            sql = f"""
                CREATE INDEX {INDEX_NAME}
                ON {TABLE_NAME}
                USING ivfflat ({COLUMN_NAME} {ops_class})
                WITH (lists = {params['lists']})
            """

        conn.execute(text(sql))
        conn.commit()

        print(f"\n✓ Index '{INDEX_NAME}' created successfully!")


def drop_command():
    """Drop the vector index."""
    with sync_engine.connect() as conn:
        existing = get_current_index_info(conn)

        if not existing:
            print(f"Index '{INDEX_NAME}' does not exist.")
            return

        print(f"Dropping index '{INDEX_NAME}' (type: {existing['type']})...")
        conn.execute(text(f"DROP INDEX IF EXISTS {INDEX_NAME}"))
        conn.commit()

        print(f"✓ Index '{INDEX_NAME}' dropped successfully!")


def recreate_command():
    """Drop and recreate the vector index."""
    print("Recreating vector index...")
    drop_command()
    print()
    create_command(force=True)


def main():
    parser = argparse.ArgumentParser(
        description="Manage pgvector indexes on chunks.embedding",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Status command
    subparsers.add_parser("status", help="Show current index status and configuration")

    # Create command
    create_parser = subparsers.add_parser("create", help="Create the vector index")
    create_parser.add_argument(
        "--force", "-f", action="store_true", help="Force recreate if exists"
    )

    # Drop command
    subparsers.add_parser("drop", help="Drop the vector index")

    # Recreate command
    subparsers.add_parser("recreate", help="Drop and recreate the vector index")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "status":
        status_command()
    elif args.command == "create":
        create_command(force=args.force)
    elif args.command == "drop":
        drop_command()
    elif args.command == "recreate":
        recreate_command()


if __name__ == "__main__":
    main()
