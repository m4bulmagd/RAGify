import sys
import os

# Add backend directory to path so we can import app modules
# Also load .env file
try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    load_dotenv(env_path)
    print(f"Loaded environment from {env_path}")
except ImportError:
    print("python-dotenv not found, assuming environment variables are set")

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from sqlmodel import Session, delete
from app.core.db import sync_engine
from app.models.document import Document
from app.models.project import Project
from app.models.chunk import Chunk
from app.models.agent import Agent, AgentLLMConfig, AgentRetrievalConfig, AgentDocument
from app.models.chat import ChatSession, ChatMessage, ChatContext, ChatFeedback

def clean_db():
    with Session(sync_engine) as session:
        print("Cleaning database...")
        
        # Order matters due to foreign keys
        
        # 1. Chat related
        print("Deleting ChatContexts...")
        session.exec(delete(ChatContext))
        
        print("Deleting ChatFeedbacks...")
        session.exec(delete(ChatFeedback))
        
        print("Deleting ChatMessages...")
        session.exec(delete(ChatMessage))
        
        print("Deleting ChatSessions...")
        session.exec(delete(ChatSession))
        
        # 2. Agent related
        print("Deleting AgentDocuments...")
        session.exec(delete(AgentDocument))
        
        print("Deleting AgentRetrievalConfigs...")
        session.exec(delete(AgentRetrievalConfig))
        
        print("Deleting AgentLLMConfigs...")
        session.exec(delete(AgentLLMConfig))
        
        print("Deleting Agents...")
        session.exec(delete(Agent))
        
        # 3. Document related
        print("Deleting Chunks...")
        session.exec(delete(Chunk))
        
        print("Deleting Documents...")
        session.exec(delete(Document))
        
        # 4. Project related
        # print("Deleting Projects...")
        # session.exec(delete(Project))
        
        session.commit()
        print("Database cleaned successfully!")

if __name__ == "__main__":
    confirm = input("Are you sure you want to delete all Projects, Documents, Agents, and Chats? (y/n): ")
    if confirm.lower() == 'y':
        clean_db()
    else:
        print("Operation cancelled.")
