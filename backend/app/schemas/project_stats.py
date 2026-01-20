from sqlmodel import SQLModel


class ProjectStats(SQLModel):
    total_documents: int
    active_agents: int
    total_chunks: int
    avg_retrieval_score: float  # Placeholder
