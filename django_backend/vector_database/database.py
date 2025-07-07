"""
Datenbank Verwaltung
"""

import os
import chromadb
import numpy as np
import logging
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings
from langchain_core.documents import Document 
from langchain_huggingface import HuggingFaceEmbeddings


models = ["Alibaba-NLP/gte-Qwen2-1.5B-instruct", "Qwen/Qwen3-Embedding-0.6B", "Qwen/Qwen3-Embedding-4B"]
rerankers = ["Qwen/Qwen3-Reranker-0.6B", "Qwen/Qwen3-Reranker-4B"]


class Database:
    def __init__(self, path_to_db : str, collection_name: str, embedding_model : str = models[1]):
        self.name : str = ""
        # self.database : chromadb.ClientAPI = chromadb.PersistentClient(path_to_db)
        # TODO Verify that this model the best one is 
        self.path_to_db : str = path_to_db
        self.embedding = HuggingFaceEmbeddings(model_name=embedding_model)
        # self.embedding.encode_kwargs = {'prompt' : "Encode this document chunk's meaning for semantic retrieval"}
        self.GEMINI_API_KEY = self.load_key()
        self.database : Chroma = Chroma(collection_name=collection_name, embedding_function=self.embedding, create_collection_if_not_exists=True, persist_directory=path_to_db)
        self.collection = self.database._collection



    def load_key(self):
        return os.getenv('GEMINI_API_KEY')


    def embed_documents(self, docs: list[Document]):
        lists = self.database.add_documents(docs)
        logging.info(f"Embedded Docs")


    def embed_text(self, texts : list[str], metadata : list[dict]):
        lists = self.database.add_texts(texts, metadatas=metadata)
        print(lists)


    def save_embedding(self, data : dict[list, list], meta_data=None ) -> None:
        
        pass


    @staticmethod
    def similarity_func(embed1: np.ndarray, embed2: np.ndarray):
        return np.dot(embed1, embed2) / (np.linalg.norm(embed1) * np.linalg.norm(embed2))


    def query_database(self, query_text : str) -> list[Document]:
        lists = self.database.search(query_text,search_type="similarity")
        logging.info(f"Found Docs for Query {lists}")
        # ranked_result = self.rank_results(lists, query_text)
        # logging.info(f"Ranked results {ranked_result}")
        # return ranked_result
        return lists


    # def rank_results(self, results: list[Document], query : str, n=7) -> list[Document]:
    #     chunks = results

    #     # Tokenize and score each query-chunk pair
    #     scores = []
    #     for chunk in chunks:
    #         inputs = self.rank_tokenizer(query, chunk, return_tensors="pt", truncation=True, padding=True)
    #         with torch.no_grad():
    #             outputs = self.rank_model(**inputs)
    #             score = outputs.logits[0].item()  # Extract the relevance score
    #             scores.append(score)

    #     # Pair each chunk with its score
    #     scored_chunks = list(zip(chunks, scores))

    #     scored_chunks.sort(key=lambda x: x[1], reverse=True)
    #     top_k_chunks = [chunk for chunk, score in scored_chunks[:n]]
        
    #     return top_k_chunks
    

    