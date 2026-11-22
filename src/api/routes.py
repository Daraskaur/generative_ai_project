"""
API routes for RAG operations.
"""

from fastapi import APIRouter, UploadFile, File, Header
from langchain_core.messages import HumanMessage, AIMessage

from src.memory.chat_history_mongo import ChatHistory
from src.models.query_request import QueryRequest
from src.rag.document_upload import documents
from src.rag.graph_builder import builder
from src.tools.citations import build_citation_footer
from src.tools.suggestions import get_followup_questions

router = APIRouter()


@router.post("/rag/query")
async def rag_query(req: QueryRequest):
    """
    Process a RAG query and return the result with follow-up suggestions.

    Args:
        req: The query request containing query text and session_id.

    Returns:
        The generated response and a list of suggested follow-up questions.
    """
    chat_history = ChatHistory.get_session_history(req.session_id)
    await chat_history.add_message(HumanMessage(content=req.query))

    # Fetch full history
    messages = await chat_history.get_messages()
    result = builder.invoke({
        "messages": messages
    })
    output_text = result["messages"][-1].content

    # Save assistant message
    await chat_history.add_message(AIMessage(content=output_text))

    # Add "Sources" under the answer the user sees. The chat history saved
    # above keeps the plain answer without this footer.
    result["messages"][-1].content = output_text + build_citation_footer(result)

    # Generate follow-up question suggestions
    suggestions = get_followup_questions(req.query, output_text)

    return {"result": result["messages"][-1], "suggestions": suggestions}


@router.post("/rag/documents/upload")
async def upload_file(
    file: UploadFile = File(...),
    description: str = Header(..., alias="X-Description")
):
    """
    Upload a document for RAG processing.

    Args:
        file: The file to upload (PDF or TXT).
        description: Document description provided via header.

    Returns:
        Upload status.
    """
    status_upload = documents(description, file)
    return {"status": status_upload}
