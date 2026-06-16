from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

import chromadb
from chromadb.api.types import EmbeddingFunction

from rag.parser import parse_policy_markdown

class CustomEmbeddingFunction(EmbeddingFunction):
    def __init__(self, embedding_model):
        self.embedding_model = embedding_model
        
    def __call__(self, input: list[str]) -> list[list[float]]:
        return self.embedding_model.embed_documents(input)


class ChromaPolicyStore:
    def __init__(
        self,
        persist_directory: Path,
        embedding_model: Any,
        collection_name: str = "policy_chunks",
    ) -> None:
        self.client = chromadb.PersistentClient(path=str(persist_directory))
        self.embedding_function = CustomEmbeddingFunction(embedding_model)
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_function
        )
        self.embedding_model = embedding_model

    def ensure_index(self, markdown_path: Path) -> None:
        if self.collection.count() == 0:
            self.rebuild(markdown_path)

    def rebuild(self, markdown_path: Path) -> None:
        with open(markdown_path, "r", encoding="utf-8") as f:
            markdown_text = f.read()
            
        chunks = parse_policy_markdown(markdown_text)
        
        ids = []
        documents = []
        metadatas = []
        
        for i, chunk in enumerate(chunks):
            ids.append(f"chunk_{i}")
            documents.append(chunk["rendered_text"])
            metadatas.append({
                "section_h2": chunk["section_h2"],
                "section_h3": chunk["section_h3"],
                "citation": chunk["citation"]
            })
            
        if ids:
            self.collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )

    def search(self, query: str, top_k: int = 4) -> list[dict[str, Any]]:
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k
        )
        
        hits = []
        if not results["documents"] or not results["documents"][0]:
            return hits
            
        docs = results["documents"][0]
        metas = results["metadatas"][0]
        distances = results["distances"][0] if "distances" in results and results["distances"] else [0.0]*len(docs)
        
        for i in range(len(docs)):
            hits.append({
                "citation": metas[i].get("citation", ""),
                "content": docs[i],
                "distance": distances[i]
            })
            
        return hits
