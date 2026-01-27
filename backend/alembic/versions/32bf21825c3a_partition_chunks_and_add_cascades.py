"""partition_chunks_and_add_cascades

Revision ID: 32bf21825c3a
Revises: a6b32718b314
Create Date: 2026-01-27 03:22:48.961082

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '32bf21825c3a'
down_revision: Union[str, Sequence[str], None] = 'a6b32718b314'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Update existing Foreign Keys to use ON DELETE CASCADE
    
    # agent_llm_configs
    op.drop_constraint('agent_llm_configs_agent_id_fkey', 'agent_llm_configs', type_='foreignkey')
    op.create_foreign_key(
        'agent_llm_configs_agent_id_fkey', 'agent_llm_configs', 'agents', 
        ['agent_id'], ['id'], ondelete='CASCADE'
    )

    # agent_retrieval_configs
    op.drop_constraint('agent_retrieval_configs_agent_id_fkey', 'agent_retrieval_configs', type_='foreignkey')
    op.create_foreign_key(
        'agent_retrieval_configs_agent_id_fkey', 'agent_retrieval_configs', 'agents', 
        ['agent_id'], ['id'], ondelete='CASCADE'
    )

    # agent_documents
    op.drop_constraint('agent_documents_agent_id_fkey', 'agent_documents', type_='foreignkey')
    op.drop_constraint('agent_documents_document_id_fkey', 'agent_documents', type_='foreignkey')
    op.create_foreign_key('agent_documents_agent_id_fkey', 'agent_documents', 'agents', ['agent_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('agent_documents_document_id_fkey', 'agent_documents', 'documents', ['document_id'], ['id'], ondelete='CASCADE')

    # chat_messages
    op.drop_constraint('chat_messages_session_id_fkey', 'chat_messages', type_='foreignkey')
    op.create_foreign_key('chat_messages_session_id_fkey', 'chat_messages', 'chat_sessions', ['session_id'], ['id'], ondelete='CASCADE')

    # chat_contexts
    op.drop_constraint('chat_contexts_message_id_fkey', 'chat_contexts', type_='foreignkey')
    op.create_foreign_key('chat_contexts_message_id_fkey', 'chat_contexts', 'chat_messages', ['message_id'], ['id'], ondelete='CASCADE')

    # chunks
    op.drop_constraint('chunks_document_id_fkey', 'chunks', type_='foreignkey')
    op.create_foreign_key('chunks_document_id_fkey', 'chunks', 'documents', ['document_id'], ['id'], ondelete='CASCADE')
    
    # documents
    op.drop_constraint('documents_project_id_fkey', 'documents', type_='foreignkey')
    op.create_foreign_key('documents_project_id_fkey', 'documents', 'projects', ['project_id'], ['id'], ondelete='CASCADE')

def downgrade() -> None:
    pass
