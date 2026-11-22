"""
Retriever setup and vector store configuration.
"""

import os

from langchain_core.documents import Document
from langchain_core.tools import create_retriever_tool
from langchain_community.embeddings import HuggingFaceEmbeddings
# from langchain_qdrant import QdrantVectorStore
from langchain_community.vectorstores import FAISS

from src.core.config import settings

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True}
)

# Global variable to store the FAISS vectorstore instance
# This ensures get_retriever() can access documents stored by retriever_chain()
_faiss_vectorstore = None

from langchain_core.tools import Tool

# Names of all files uploaded so far. The store now keeps EVERY uploaded file.
_uploaded_files = []


def retriever_chain(chunks: list[Document]):
    """
    Add document chunks to the FAISS vector database.

    Chunks from every uploaded file are kept together, so questions can be
    answered from several documents at once.

    Args:
        chunks: List of document chunks to store.

    Returns:
        Boolean indicating success of the operation.
    """
    global _faiss_vectorstore

    try:
        if _faiss_vectorstore is None:
            _faiss_vectorstore = FAISS.from_documents(
                documents=chunks,
                embedding=embeddings
            )
        else:
            _faiss_vectorstore.add_documents(chunks)

        for chunk in chunks:
            file_name = chunk.metadata.get("source")
            if file_name and file_name not in _uploaded_files:
                _uploaded_files.append(file_name)

        print("Files in the store:", _uploaded_files)
        print(f"Added {len(chunks)} chunks to the vector store")
        return True
    except Exception as e:
        print(f"Error storing documents in FAISS: {e}")
        return False


def documents_uploaded() -> bool:
    """
    Check whether at least one document has been uploaded.

    Returns:
        True if the store holds any uploaded document.
    """
    return len(_uploaded_files) > 0


def _search_chunks(query: str, per_file: int = 3) -> list:
    """
    Find the best passages for a query from EACH uploaded file.

    Searching file by file makes sure a conflicting passage in the second
    document is not crowded out by the first one.

    Args:
        query: The search query.
        per_file: How many passages to take from each file.

    Returns:
        A list of matching Document chunks.
    """
    if _faiss_vectorstore is None or not _uploaded_files:
        return []

    collected = []
    seen_text = set()
    for file_name in _uploaded_files:
        found = _faiss_vectorstore.similarity_search(
            query,
            k=per_file,
            fetch_k=1000,
            filter={"source": file_name},
        )
        for doc in found:
            if doc.page_content in seen_text:
                continue
            seen_text.add(doc.page_content)
            collected.append(doc)

    return collected


def _label(doc: Document) -> str:
    """
    Build a label like [Document: name.pdf | Page 3] for a chunk.

    Args:
        doc: A document chunk with metadata.

    Returns:
        The label text.
    """
    file_name = doc.metadata.get("source", "unknown")
    page = doc.metadata.get("page")
    if isinstance(page, int):
        return f"[Document: {file_name} | Page {page + 1}]"
    return f"[Document: {file_name}]"


def search_documents(query: str) -> str:
    """
    Search all uploaded documents and return labelled passages as text.

    Args:
        query: The search query.

    Returns:
        Passages, each starting with its document name and page.
    """
    docs = _search_chunks(query)
    if not docs:
        return "No documents have been uploaded yet."

    parts = [f"{_label(doc)}\n{doc.page_content}" for doc in docs]
    return "\n\n".join(parts)


def get_retriever():
    """
    Get a retriever tool that searches every uploaded document.

    Returns:
        A LangChain tool. Calling .invoke(question) returns labelled passages.
    """
    import os

    description = None
    if os.path.exists("description.txt"):
        with open("description.txt", "r", encoding="utf-8") as f:
            description = f.read()

    return Tool.from_function(
        func=search_documents,
        name="retriever_customer_uploaded_documents",
        description=(
            f"Use this tool only to answer questions about: {description}\n"
            "Don't use this tool to answer anything else."
        ),
    )


def get_source_references(query: str, k: int = 3) -> list:
    """
    Find which files and pages the retrieved passages for a query come from.

    Args:
        query: The query used for retrieval.
        k: Number of passages to look up per file.

    Returns:
        A list of dicts with "file" and "page" (page is None for text files).
    """
    references = []
    for doc in _search_chunks(query, per_file=k):
        file_name = doc.metadata.get("source", "unknown")
        page = doc.metadata.get("page")
        page_number = page + 1 if isinstance(page, int) else None
        references.append({"file": file_name, "page": page_number})

    return references