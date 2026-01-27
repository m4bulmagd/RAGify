# RAGify (WIP)

**RAGify** is a modern Retrieval-Augmented Generation (RAG) application built for scalability, performance, and developer experience. It enables users to upload documents, ingest them into a vector database, and chat with them using advanced LLM capabilities.

## 🚀 Features

-   **🤖 Intelligent Chat**: Chat with your documents using streaming responses and context-aware LLMs.
-   **⚙️ Agent Playground**: Test and iterate on different system prompts and agent configurations.
-   **📄 Robust Ingestion**: Support for PDF and text document ingestion with background processing via Celery.
-   **🔍 Vector Search**: Powered by `pgvector` for efficient and scalable similarity search.
-   **📊 Observability**: Full LLM tracing and observability integrated with **Arize Phoenix**.
-   **☁️ Cloud Native**: Dockerized architecture with services for DB, Cache, and Object Storage.

## 🛠️ Tech Stack

### Backend
-   **Language**: Python 3.12+
-   **Framework**: FastAPI
-   **RAG Engine**: LlamaIndex & LangChain (via integration)
-   **Task Queue**: Celery with Redis
-   **Database**: PostgreSQL with `pgvector`
-   **Object Storage**: MinIO (S3 compatible)
-   **Package Manager**: `uv` (Fast Python package installer)

### Frontend
-   **Framework**: Next.js 16 (App Router)
-   **UI Library**: React 19
-   **Styling**: Tailwind CSS 4
-   **Components**: Shadcn UI (Radix UI)
-   **AI Integration**: Vercel AI SDK

### Infrastructure
-   **Containerization**: Docker & Docker Compose
-   **Observability**: Arize Phoenix (OTEL compatible)
-   **Email Testing**: Mailcatcher

## 🏁 Getting Started

### Prerequisites

-   Docker & Docker Compose installed on your machine.
-   `uv` installed for local backend development (optional but recommended).
-   Node.js 20+ for local frontend development.

### Quick Start (Docker)

The easiest way to get RAGify up and running is using Docker Compose.

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/RAGify.git
    cd RAGify
    ```

2.  **Environment Setup**:
    Copy the example environment file for the backend.
    ```bash
    cp backend/.env.example backend/.env
    ```
    *Note: You may need to add your `OPENAI_API_KEY` or other provider keys in `backend/.env` for LLM features to work.*

3.  **Start Services**:
    ```bash
    docker-compose up -d --build
    ```

4.  **Access the Application**:
    -   **Frontend**: [http://localhost:3000](http://localhost:3000)
    -   **Backend API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
    -   **Phoenix Tracing**: [http://localhost:6006](http://localhost:6006)
    -   **MinIO Console**: [http://localhost:9001](http://localhost:9001)
    -   **Mailcatcher**: [http://localhost:1080](http://localhost:1080)

## 🔧 Local Development

### Backend

1.  Navigate to the backend directory:
    ```bash
    cd backend
    ```
2.  Install dependencies using `uv`:
    ```bash
    uv sync
    ```
3.  Run the development server:
    ```bash
    uv run uvicorn app.main:app --reload
    ```

### Frontend

1.  Navigate to the frontend directory:
    ```bash
    cd frontend
    ```
2.  Install dependencies:
    ```bash
    npm install
    ```
3.  Run the development server:
    ```bash
    npm run dev
    ```

## 🧪 Testing

### Backend Tests
Run the pytest suite to ensure everything is working correctly.
```bash
cd backend
uv run pytest
```

## 📜 License

This project is licensed under the MIT License.
