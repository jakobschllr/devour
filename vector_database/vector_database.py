"""
Datenbank Verwaltung
"""

import json
import os
import re
import chromadb
from dotenv import load_dotenv
import numpy as np
import requests
from sentence_transformers import SentenceTransformer
from transformers import AutoModelForSequenceClassification, AutoTokenizer
import torch


class Database:
    def __init__(self, path_to_db : str, collection_name: str, model="Alibaba-NLP/gte-Qwen2-1.5B-instruct", sim_treshold=0.7, rank_model_name="cross-encoder/stsb-roberta-large"):
        self.name : str = ""
        self.database : chromadb.ClientAPI = chromadb.PersistentClient(path_to_db)
        self.collection : chromadb.Collection = self.database.get_or_create_collection(collection_name)
        self.embedding_model = SentenceTransformer(model, trust_remote_code=True)
        self.chunk_id : int = self.collection.count()
        self.similarity_threshold : float = sim_treshold
        self.employee_info : list[str] = self.get_mitarbeiter()
        self.path_to_db : str = path_to_db
        self.GEMINI_API_KEY = self.load_key()
        self.rank_model_name = rank_model_name
        self.rank_tokenizer = AutoTokenizer.from_pretrained(self.rank_model_name)
        self.rank_model = AutoModelForSequenceClassification.from_pretrained(self.rank_model_name)


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
            similarity = Database.similarity_func(embeddings[i-1], embeddings[i])
            if similarity > self.similarity_threshold:  # Adjust threshold as needed
                current_chunk.append(initial_chunks[i])
            else:
                semantic_chunks.append(' '.join(current_chunk))
                current_chunk = [initial_chunks[i]]
        
        semantic_chunks.append(' '.join(current_chunk))

        return semantic_chunks


    def similarity_func( embed1: np.ndarray, embed2: np.ndarray):
        return np.dot(embed1, embed2) / (np.linalg.norm(embed1) * np.linalg.norm(embed2))


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
        result = self.collection.query(query_embeddings=query_embedding, n_results=15)
        ranked_result = self.rank_results(result, query_text)
        return ranked_result


    def rank_results(self, results: chromadb.QueryResult, query : str, n=7) -> list[str]:
        chunks = results["documents"][0]

        # Tokenize and score each query-chunk pair
        scores = []
        for chunk in chunks:
            inputs = self.rank_tokenizer(query, chunk, return_tensors="pt", truncation=True, padding=True)
            with torch.no_grad():
                outputs = self.rank_model(**inputs)
                score = outputs.logits[0].item()  # Extract the relevance score
                scores.append(score)

        # Pair each chunk with its score
        scored_chunks = list(zip(chunks, scores))

        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        top_k_chunks = [chunk for chunk, score in scored_chunks[:n]]
        
        return top_k_chunks
    

    def get_mitarbeiter(self) -> list[str]:
        mitarbeiter = self.collection.get(where={"role":"Mitarbeiter"}, include=["documents"])
        return mitarbeiter["documents"]


    def contexting_sentences(self, sentences : list[str], whole_text: dict | None = None) -> list[str]:
        prompt = f"""Hier bekommst du eine Liste von verschiedenen Sätzen ausgeschnitten von einem Text. Die Sätze werden embeded und in einer Vektor Datenbank gespeichert. Aber damit die einzelne Sätze Sinn machen, brauche ich für jeden Satz den Kontext dazu. 
                    Der ganze Text bekommst du auch und du solltest für jeden String (Satz) in der Liste ein oder zwei kurze Sätze zurückgeben, die den Kontext des Satzes ergeben.
                    Du musst dich ausschließlich auf den Text basieren um den Kontext zu ergeben.
                    Antworte mit einer Liste von String. Jedes String in der Liste enthalt ein oder zwei Sätze die den Kontext des entsprehenden Satzes ergibt. 
                    Falls du keinen Kontext für einen Satz findest, füge einfach ein leeres String zu der Liste hinzu.
                    Die Anzahl an Kontext Strings musst die Anzahl an gegebenen einzel Satze entsprechen.
                    Deine Antwort strukturiest du in einer JSON Format und du musst ausschließlich mit dieser JSON Datei Antworten.
                    Hier ist die JSON Struktur:
                    {{
                        "contexts":[],
        
                    }}
                    
                    Der ganze Text : 
                    {whole_text}

                    Die verschiedene Sätze : 
                    {sentences}
                    """
        result = self.make_api_request(prompt)

        res = json.loads(result.split('json')[1].replace('\n', '').replace("```", ""))

        sentence_with_context = [sent + cont for sent, cont in zip(sentences, res["contexts"])]

        return sentence_with_context
    

    def make_api_request(self, text):
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.GEMINI_API_KEY}"

        headers = {
            "Content-Type": "application/json"
        }

        data = {
            "contents": [{
                "parts": [{"text": text}]
            }]
        }

        response_json = requests.post(url, headers=headers, data=json.dumps(data))

        try:
            response = response_json.json()['candidates'][0]['content']['parts'][0]['text']
            return response
        except KeyError as e:
            return "Error"

    def load_key(self):
        load_dotenv()
        GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
        return GEMINI_API_KEY