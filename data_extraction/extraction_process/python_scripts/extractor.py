import json
import logging
import re
from langchain_text_splitters import Language
import requests
import os
from .shorten_transcript import shorten_transcript
from vector_database.database import Database # type: ignore
from nltk.tokenize import sent_tokenize
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma.vectorstores import cosine_similarity



class Extractor:
    def __init__(self, path_to_db : str, collection_name : str):
        self.vector_db = Database(path_to_db, collection_name)
        self.employee_list : list[str] = self.get_mitarbeiter()
        self.extracted_data : dict = None
        self.parsed_data : dict = None


    def get_sentences(text):

        text_splitter = RecursiveCharacterTextSplitter(separators=['.', '\n'], )
        sentences = text_splitter.split_text(text)

        return sentences


    def extract(self, transcript_text):
        summary = self.summarise_transcript(transcript_text) 
        self.parse_data(summary)

    def parse_data(self, transcript_data):
        try:
            logging.info("Parsing extracted ")
            self.extracted_data = json.loads(transcript_data.split('json')[1].replace('\n', '').replace("```", ""))
            data = self.extracted_data
            whole_text = ""
            separate_paragraphs = []

            for key, value in data.items():
                if key.lower() != 'meeting_subject' and key.lower() != 'meeting_info' and key.lower() != 'department_info' and key.lower() != 'participants_info':
                    whole_text += value
                    whole_text += " "

                    label = data['meeting_subject'] + " " + key.replace("_", " ")
                    text = value

                    paragraph = {
                        label: text
                    }

                    separate_paragraphs.append(paragraph)


            separate_sentences = self.get_sentences(whole_text)

            whole_text_with_label = {
                data['meeting_subject']: whole_text
            }

            data_for_vector_db = {
                "whole_text": whole_text_with_label,
                "paragraphs": separate_paragraphs,
                "sentences": separate_sentences,
                "persons_info": data["participants_info"],
                "meeting_data": data["meeting_info"]
            }

            self.parsed_data = data_for_vector_db

        except Exception as e:
            raise e.add_note("Could not parse the extracted data into a json")

    def summarise_transcript(self, transcript_text):
        try:
            logging.info("Extracting data from text")
            summary = shorten_transcript(transcript_text)
            return summary
        except Exception as e:
            raise e

    
    def add_to_db(self):
        self.embed_and_save()


    
    def add_employee(self, person_info: list[str]):
            for elem in person_info:
                match = re.match(r"([^:]+): ([^,]+), (.+)", elem)
                if(match):
                    mitarbeiter = "Mitarbeiter: " + " ".join([match.group(1).strip(), match.group(2).strip()]) 
                    if mitarbeiter not in self.employee_list:
                        self.vector_db.embed_text([mitarbeiter], meta_data= [{"role": "Mitarbeiter"}])
                        self.employee_list.append(mitarbeiter)


    def embed_and_save(self):
        data = self.parsed_data
        paragraphs, paragraph_meta, sentence_chunks = self.extract_data(data)
        meeting_data = data["meeting_data"]
        self.vector_db.embed_text([meeting_data["content"]], [{"date":meeting_data["date"]}])
        self.vector_db.embed_text(sentence_chunks)
        self.vector_db.embed_text(paragraphs, paragraph_meta)


    def semantic_chunking( self, initial_chunks: list[str], threshold=0.7) -> list[str]:
        """
        Joins similar chunks (sentences, paragraphs etc) together 
        """
    
        embeddings = self.vector_db.embed_documents(initial_chunks)
        
        semantic_chunks = []
        current_chunk = [initial_chunks[0]]
        
        for i in range(1, len(initial_chunks)):
            similarity = cosine_similarity(embeddings[i-1], embeddings[i])
            if similarity > threshold:  # Adjust threshold as needed
                current_chunk.append(initial_chunks[i])
            else:
                semantic_chunks.append(' '.join(current_chunk))
                current_chunk = [initial_chunks[i]]
        
        semantic_chunks.append(' '.join(current_chunk))

        return semantic_chunks



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


    def get_mitarbeiter(self) -> list[str]:
            mitarbeiter = self.vector_db.collection.get(where={"role":"Mitarbeiter"}, include=["documents"])
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
