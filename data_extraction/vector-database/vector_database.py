"""
Datenbank Verwaltung
"""

import json
import re
import chromadb
import numpy as np
from sentence_transformers import SentenceTransformer


class Database:
    def __init__(self, path_to_db : str, name: str):
        self.name : str = ""
        self.database : chromadb.ClientAPI = chromadb.PersistentClient(path_to_db)
        self.collection : chromadb.Collection = self.database.get_or_create_collection(name)
        self.embedding_model = SentenceTransformer( "Alibaba-NLP/gte-Qwen2-1.5B-instruct", trust_remote_code=True)
        self.chunk_id : int = self.collection.count()
        self.similarity_threshold : float = 0.7
        self.employee_info : list[str] = self.get_mitarbeiter()
        self.path_to_db : str = path_to_db


    def embed(self, chunks : list[str]) -> dict[list, list]:
        """
        Encodes chunks 
        """

        data = {
            "chunks": [],
            "embeddings": [],
        }

        for chunk in chunks:
            data["chunks"].append(chunk)
            data["embeddings"].append(self.embedding_model.encode(chunk))

        return data


    def save_embedding(self, data : dict[list, list], meta_data=None ) -> None:

        ids = []

        for id in range(len(data["chunks"])):
            ids.append( "id" + str(self.chunk_id + id))

        self.chunk_id += len(data["chunks"])

        self.collection.add(documents=data["chunks"],
                            embeddings=data["embeddings"],
                            metadatas=meta_data,
                            ids=ids)


    def semantic_chunking( self, initial_chunks: list[str]) -> list[str]:
        """
        Joins similar chunks (sentences, paragraphs etc) together 
        """
    
        embeddings = self.embedding_model.encode(initial_chunks)
        
        semantic_chunks = []
        current_chunk = [initial_chunks[0]]
        
        for i in range(1, len(initial_chunks)):
            similarity = np.dot(embeddings[i-1], embeddings[i]) / (np.linalg.norm(embeddings[i-1]) * np.linalg.norm(embeddings[i]))
            if similarity > self.similarity_threshold:  # Adjust threshold as needed
                current_chunk.append(initial_chunks[i])
            else:
                semantic_chunks.append(' '.join(current_chunk))
                current_chunk = [initial_chunks[i]]
        
        semantic_chunks.append(' '.join(current_chunk))

        return semantic_chunks


    def add_employee(self, person_info: list[str]):
        
        for elem in person_info:
            match = re.match(r"([^:]+): ([^,]+), (.+)", elem)
            if(match):
                mitarbeiter = "Mitarbeiter: " + " ".join([match.group(1).strip(), match.group(2).strip()]) 
                if mitarbeiter not in self.employee_info:
                    self.save_embedding(self.embed([elem]), meta_data= [{"role": "Mitarbeiter"}])
                    self.employee_info.append(mitarbeiter)


    def extract_paragraph(self, data : list[dict]) -> tuple[list, list]:
        paragraphs = []
        paragraph_titel = []
        for elem in data:
            item = elem.popitem()
            paragraphs.append(item[1])
            paragraph_titel.append(item[0])

        paragraph_meta = [ {"titel" : titel} for titel in paragraph_titel]

        return (paragraphs, paragraph_meta)


    def extract_data(self, data: dict):
        self.add_employee(data["persons_info"])
        paragraphs, paragraph_meta = self.extract_paragraph(data["paragraphs"])
        sentences = data['sentences']
        context_sentences = self.contexting_sentences(sentences)
        sentence_chunks = self.semantic_chunking(context_sentences)
        print(f"Paragraphs : {len(paragraphs)} \n Sentence Chunks: {len(sentence_chunks)}")
        return (paragraphs, paragraph_meta, sentence_chunks)


    def embed_and_save(self, data: dict):
        paragraphs, paragraph_meta, sentence_chunks = self.extract_data(data)
        meeting_data = data["meeting_data"]
        self.save_embedding(self.embed([meeting_data["content"]]), [{"date":meeting_data["date"]}])
        self.save_embedding(self.embed(sentence_chunks))
        self.save_embedding(self.embed(paragraphs), paragraph_meta)


    def vectorise(self, path_to_data: str, num : int):
        for i in range(1, num+1):
            path = path_to_data + f"/data_{i}.json"
            with open(path, 'r') as file:
                data = json.load(file)
            self.embed_and_save(data)


    def query_database(self, query_text : str) -> list[str]:
        query_embedding = self.embedding_model.encode(query_text)
        result = self.collection.query(query_embeddings=query_embedding, n_results=10)
        print(result["documents"], end="\n\n")
        return result['documents'][0][:10]


    def rank_results(results: chromadb.QueryResult ) -> list[str]:
        results_list = results["documents"][0]

        return results_list
    

    def get_mitarbeiter(self) -> list[str]:
        mitarbeiter = self.collection.get(where={"role":"Mitarbeiter"}, include=["documents"])
        return mitarbeiter["documents"]


    def contexting_sentences(self, sentences : list[str], whole_text: dict | None = None) -> list[str]:
        return sentences