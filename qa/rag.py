"""RAG pipeline using LangChain + Chroma + OpenRouter LLM."""
from __future__ import annotations

import os
from functools import lru_cache
from typing import List, Tuple

from django.conf import settings
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.documents import Document as LCDocument
from langchain_core.prompts import ChatPromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings

SYSTEM_PROMPT = (
    "You are a helpful assistant that answers questions strictly using the "
    "provided document excerpts. If the answer is not contained in the "
    "context, say you don't know. Always cite the document titles you used."
)

PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"),
])


# @lru_cache(maxsize=1)
# def get_embeddings() -> OpenAIEmbeddings:
#     return OpenAIEmbeddings(
#         model=settings.EMBEDDING_MODEL,
#         base_url=settings.EMBEDDING_BASE_URL,
#         api_key=settings.EMBEDDING_API_KEY or "missing",
#         check_embedding_ctx_length=False,
#     )

@lru_cache(maxsize=1)
def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

@lru_cache(maxsize=1)
def get_vectorstore() -> Chroma:
    os.makedirs(settings.CHROMA_DIR, exist_ok=True)
    return Chroma(
        collection_name="documents",
        embedding_function=get_embeddings(),
        persist_directory=settings.CHROMA_DIR,
    )


@lru_cache(maxsize=1)
def get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.LLM_MODEL,
        base_url=settings.OPENROUTER_BASE_URL,
        api_key=settings.OPENROUTER_API_KEY or "missing",
        temperature=0.2,
        default_headers={
            "HTTP-Referer": "https://localhost",
            "X-Title": "LLM Document QA",
        },
    )


def _splitter() -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(chunk_size=900, chunk_overlap=120)


def index_document(doc_id: int, title: str, text: str) -> int:
    """Split and add a document to the vector store. Returns chunk count."""
    remove_document(doc_id)  # clear any old chunks
    chunks = _splitter().split_text(text)
    if not chunks:
        return 0
    lc_docs = [
        LCDocument(
            page_content=chunk,
            metadata={"doc_id": doc_id, "title": title, "chunk": i},
        )
        for i, chunk in enumerate(chunks)
    ]
    ids = [f"{doc_id}-{i}" for i in range(len(chunks))]
    get_vectorstore().add_documents(lc_docs, ids=ids)
    return len(chunks)


def remove_document(doc_id: int) -> None:
    try:
        get_vectorstore().delete(where={"doc_id": doc_id})
    except Exception:
        pass


def answer_question(question: str, k: int = 4) -> Tuple[str, List[dict]]:
    """Run RAG: retrieve top-k chunks, call LLM, return (answer, sources)."""
    vs = get_vectorstore()
    results = vs.similarity_search_with_score(question, k=k)
    if not results:
        return ("No documents have been indexed yet.", [])

    context_parts = []
    sources = []
    for doc, score in results:
        title = doc.metadata.get("title", "Untitled")
        chunk_idx = doc.metadata.get("chunk", 0)
        context_parts.append(f"[{title} #chunk{chunk_idx}]\n{doc.page_content}")
        sources.append({
            "doc_id": doc.metadata.get("doc_id"),
            "title": title,
            "chunk": chunk_idx,
            "score": float(score),
            "snippet": doc.page_content[:240],
        })

    context = "\n\n---\n\n".join(context_parts)
    chain = PROMPT | get_llm()
    response = chain.invoke({"context": context, "question": question})
    answer = response.content if hasattr(response, "content") else str(response)
    return (answer, sources)
