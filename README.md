# Adaptive RAG Chatbot

Adaptive RAG Chatbot is an agentic Retrieval-Augmented Generation application that routes questions through document retrieval, general knowledge, or web search. It provides a FastAPI backend and a Streamlit interface with PDF/TXT upload, chat history, voice input, citations, and follow-up questions.

## Features

- Routes questions by intent:
  - `index` - Answer from uploaded documents.
  - `general` - Answer with the Groq LLM's general knowledge.
  - `search` - Search the web with Tavily.
- Uses FAISS and `sentence-transformers/all-MiniLM-L6-v2` for document retrieval.
- Keeps every uploaded PDF/TXT document in the in-process FAISS store.
- Answers document questions strictly from retrieved passages.
- Rewrites a document query once when the retrieved context is not relevant.
- Stores chat history by session in MongoDB.
- Uploads PDF and TXT files through the API or Streamlit sidebar.
- Adds document names and page numbers as a Sources footer.
- Generates up to three follow-up questions.
- Accepts typed or browser voice input.

## Technology

| Component | Implementation |
|---|---|
| API | FastAPI |
| UI | Streamlit |
| Agent workflow | LangGraph |
| LLM | Groq via `openai/gpt-oss-120b` |
| Embeddings | Hugging Face `sentence-transformers/all-MiniLM-L6-v2` |
| Vector store | FAISS, in process memory |
| Web search | Tavily |
| Chat history | MongoDB through Motor |
| Document loaders | PyPDF and TextLoader |
| Text splitting | LangChain RecursiveCharacterTextSplitter |
| Voice input | `streamlit-mic-recorder` |

## How It Works

1. The Streamlit application sends a query and session ID to the FastAPI backend.
2. LangGraph routes the query to `query_analysis`.
3. If documents have been uploaded, the system uses document-only index mode.
4. If no documents have been uploaded, the LLM classifies the query as `index`, `general`, or `search`.
5. Retrieved passages are graded for relevance.
6. The query is rewritten once if the first retrieval is irrelevant.
7. The selected answer is generated and the assistant message is saved to MongoDB.
8. Document answers include source filenames and PDF page numbers.

When no documents are uploaded, the system may still return an answer through its general or web-search route. After at least one document is uploaded, questions are answered only from the uploaded document collection.

## Project Structure

```text
generative_ai_project-main/
├── src/
│   ├── api/
│   │   └── routes.py
│   ├── config/
│   │   ├── prompts.yaml
│   │   └── settings.py
│   ├── core/
│   │   ├── config.py
│   │   └── logger.py
│   ├── db/
│   │   └── mongo_client.py
│   ├── llms/
│   │   ├── groq.py
│   │   └── openai.py
│   ├── memory/
│   │   ├── chat_history_mongo.py
│   │   └── chathistory_in_memory.py
│   ├── models/
│   ├── rag/
│   │   ├── document_upload.py
│   │   ├── graph_builder.py
│   │   ├── nodes.py
│   │   ├── reAct_agent.py
│   │   └── retriever_setup.py
│   ├── tools/
│   ├── __init__.py
│   └── main.py
├── streamlit_app/
│   ├── home.py
│   ├── pages/
│   │   └── chat.py
│   └── utils/
│       └── api_client.py
├── description.txt
├── requirements.txt
└── README.md
```

## Requirements

- Python 3.9 or newer
- MongoDB running locally
- A Groq API key
- A Tavily API key for web-search routing
- Internet access for model, embedding, and search services

## Installation

Clone the project and create a virtual environment:

```powershell
git clone <your-repository-url>
cd generative_ai_project-main
python -m venv venv
venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key
```

MongoDB is currently configured directly in `src/db/mongo_client.py`:

```text
MongoDB URL: mongodb://localhost:27017
Database: adaptive_rag
Collection: chat_history
```

## Running the Application

Start MongoDB, then start the FastAPI server:

```powershell
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

In a second terminal, activate the environment and start Streamlit:

```powershell
venv\Scripts\Activate.ps1
streamlit run streamlit_app/home.py
```

Open:

- Streamlit: `http://localhost:8501`
- API root: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Using the Streamlit Interface

1. Open `http://localhost:8501`.
2. Click **Start Chatting**.
3. Upload a PDF or TXT file from the sidebar.
4. Enter a short description of the document when prompted.
5. Ask a question in the chat input or use voice input.
6. Select a suggested follow-up question if one is shown.

Each uploaded file is uploaded only once for the same filename and description in the Streamlit session.

## API

### Health Check

```http
GET /
```

Example response:

```json
{
  "message": "Adaptive RAG API is running"
}
```

### Ask a Question

```http
POST /rag/query
Content-Type: application/json
```

```json
{
  "query": "What is explained in the document?",
  "session_id": "session-123"
}
```

The response contains the final LangGraph message and generated follow-up questions:

```json
{
  "result": {
    "type": "ai",
    "content": "The answer...",
    "additional_kwargs": {}
  },
  "suggestions": [
    "What else is covered?",
    "Who introduced the concept?"
  ]
}
```

Chat messages are loaded and stored using the supplied `session_id`.

### Upload a Document

```http
POST /rag/documents/upload
X-Description: Overview of the uploaded project document
Content-Type: multipart/form-data
```

Form field:

- `file`: A PDF or TXT file

Example:

```powershell
curl.exe -X POST "http://localhost:8000/rag/documents/upload" `
  -H "X-Description: Project architecture and implementation notes" `
  -F "file=@document.pdf"
```

Success response:

```json
{
  "status": true
}
```

Unsupported file types return HTTP `400`. Loading or processing failures return HTTP `500`.

## Configuration

Environment variables:

| Variable | Required | Purpose |
|---|---:|---|
| `GROQ_API_KEY` | Yes | Groq LLM and document description generation |
| `TAVILY_API_KEY` | For web search | Tavily external search |

Prompt templates are stored in `src/config/prompts.yaml`. They control classification, relevance grading, query rewriting, answer generation, and answer verification.

Document processing settings:

| Setting | Value |
|---|---|
| Chunk size | 1000 characters |
| Chunk overlap | 150 characters |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` |
| PDF metadata | Filename and page number |
| Retrieved passages per uploaded file | 3 |

## Storage and Session Behavior

- MongoDB stores chat history across API calls for a session ID.
- FAISS documents are stored in memory in the running Python process.
- FAISS and the uploaded-file list are lost when the backend restarts.
- MongoDB must be reachable before querying or saving chat history.
- Uploaded document descriptions are enhanced by the Groq LLM and saved to `description.txt`.
- The Streamlit session ID is generated locally with `uuid`.

## API Testing

Open `http://localhost:8000/docs` and use the interactive Swagger interface.

Query example:

```json
{
  "query": "Hello",
  "session_id": "test-session"
}
```

Document upload example:

```json
{
  "session_id": "test-session",
  "query": "Summarize the uploaded document"
}
```

## Limitations

- FAISS data is not persisted to disk or a separate vector database.
- Uploaded documents are process-wide, not isolated by session or user.
- The in-process backend must remain running while the FAISS store is in use.
- MongoDB configuration is fixed in source code and is not loaded from environment variables.
- Streamlit voice input depends on browser Web Speech API support.
- The project does not currently include Docker configuration or an automated test suite.

## Security

- Keep `.env` out of source control.
- Do not commit API keys.
- Use HTTPS and authentication before exposing the API publicly.
- Restrict network access to MongoDB and the FastAPI port in production.
