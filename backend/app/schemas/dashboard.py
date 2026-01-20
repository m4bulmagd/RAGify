from sqlmodel import SQLModel


class DashboardStats(SQLModel):
    total_projects: int
    total_requests: int
    storage_usage: int  # in bytes
    processing_docs: int
