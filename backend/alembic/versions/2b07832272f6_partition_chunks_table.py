"""partition_chunks_table

Revision ID: 2b07832272f6
Revises: 32bf21825c3a
Create Date: 2026-01-27 03:28:55.321558

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2b07832272f6'
down_revision: Union[str, Sequence[str], None] = '32bf21825c3a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 0. Update chat_contexts schema first (it references chunks)
    op.add_column('chat_contexts', sa.Column('project_id', sa.Uuid(), nullable=True))
    op.execute("""
        UPDATE chat_contexts SET project_id = documents.project_id 
        FROM documents WHERE chat_contexts.document_id = documents.id
    """)
    op.alter_column('chat_contexts', 'project_id', nullable=False)
    op.create_index(op.f('ix_chat_contexts_project_id'), 'chat_contexts', ['project_id'], unique=False)

    # 1. Create the new partitioned chunks table with SERIAL
    op.execute("""
        CREATE TABLE chunks_new (
            id SERIAL,
            project_id UUID NOT NULL,
            document_id UUID NOT NULL,
            text VARCHAR NOT NULL,
            metadata_ JSONB,
            page_number INTEGER,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL,
            embedding VECTOR(1536),
            content_vector TSVECTOR GENERATED ALWAYS AS (to_tsvector('english', text)) STORED,
            PRIMARY KEY (id, project_id)
        ) PARTITION BY HASH (project_id);
    """)

    # 2. Create partitions
    for i in range(4):
        op.execute(f"CREATE TABLE chunks_p{i} PARTITION OF chunks_new FOR VALUES WITH (MODULUS 4, REMAINDER {i});")

    # 3. Migrate data
    op.execute("""
        INSERT INTO chunks_new (id, project_id, document_id, text, metadata_, page_number, created_at, embedding)
        SELECT id, project_id, document_id, text, metadata_, page_number, created_at, embedding FROM chunks;
    """)

    # 4. Sync sequence value
    op.execute("SELECT setval(pg_get_serial_sequence('chunks_new', 'id'), max(id)) FROM chunks_new;")

    # 5. Swap tables
    op.execute("DROP TABLE chunks CASCADE;")
    op.execute("ALTER TABLE chunks_new RENAME TO chunks;")
    # Rename the automatic sequence too for consistency
    op.execute("ALTER SEQUENCE chunks_new_id_seq RENAME TO chunks_id_seq;")

    # 6. Recreate Indexes
    op.execute("""
        CREATE INDEX ix_chunks_embedding ON chunks USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
    """)
    op.execute("CREATE INDEX ix_chunks_content_vector ON chunks USING gin (content_vector);")
    op.create_index(op.f('ix_chunks_document_id'), 'chunks', ['document_id'], unique=False)
    op.create_index(op.f('ix_chunks_project_id'), 'chunks', ['project_id'], unique=False)

    # 7. Recreate Foreign Keys
    op.create_foreign_key(
        'chunks_document_id_fkey', 'chunks', 'documents', 
        ['document_id'], ['id'], ondelete='CASCADE'
    )
    op.create_foreign_key(
        'chunks_project_id_fkey', 'chunks', 'projects', 
        ['project_id'], ['id'], ondelete='CASCADE'
    )
    
    # 8. Recreate chat_contexts schema additions
    # Note: the column project_id was added in chunks_new creation above, 
    # but we also added it to chat_contexts in previous step of this migration.
    # Wait, I should make sure chat_contexts has the column before creating the FK.
    # I'll move the chat_contexts alter to the top.
    
    # 9. Recreate chat_contexts FK to chunks
    op.create_foreign_key(
        'chat_contexts_chunk_id_project_id_fkey', 'chat_contexts', 'chunks',
        ['chunk_id', 'project_id'], ['id', 'project_id'], ondelete='CASCADE'
    )
