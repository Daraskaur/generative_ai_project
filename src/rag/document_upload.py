"""
Document upload and processing module.
"""

import os
import tempfile

from fastapi import UploadFile, File
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.rag.retriever_setup import retriever_chain
from src.tools.common_tools import enhance_description_with_llm


def documents(description: str, file: UploadFile = File(...)):
    """
    Process and upload a document for RAG.

    Validates file type, loads content, enhances description, chunks documents,
    and stores them in the vector database.

    Args:
        description: User-provided document description.
        file: The uploaded file (PDF or TXT).

    Returns:
        Boolean indicating success of the upload process.

    Raises:
        HTTPException: If file type is not supported or any step fails.
    """
    import traceback
    from fastapi import HTTPException

    filename = file.filename
    print("Upload started for:", filename)

    if not filename.endswith(".pdf") and not filename.endswith(".txt"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF and TXT files are supported"
        )

    file_bytes = file.file.read()

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=os.path.splitext(filename)[1]
    ) as tmp_file:
        tmp_file.write(file_bytes)
        tmp_path = tmp_file.name

    # Step 1: load the file
    try:
        if filename.endswith(".pdf"):
            loader = PyPDFLoader(tmp_path)
        else:
            loader = TextLoader(tmp_path, encoding="utf-8")
        docs = loader.load()

        # Store the real file name (not the temp file name) so answers can cite it
        for doc in docs:
            doc.metadata["source"] = filename

        print("Step 1 OK: file loaded,", len(docs), "pages/sections")
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Step 1 failed (loading file): {e}"
        )
    finally:
        os.unlink(tmp_path)

    # Step 2: improve the description using the LLM
    try:
        description_llm = enhance_description_with_llm(description)
        with open("description.txt", "w", encoding="utf-8") as f:
            f.write(description_llm)
        print("Step 2 OK: description saved")
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Step 2 failed (LLM description): {e}"
        )

    # Step 3: split into chunks and store in the vector database
    try:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=150
        )
        chunks = splitter.split_documents(docs)
        print("Step 3 OK:", len(chunks), "chunks created")
        return retriever_chain(chunks)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Step 3 failed (chunking/storing): {e}"
        )

