import ollama
import requests
#from vectorise import query_vector_database
import chromadb
import re
import json
import os
from dotenv import load_dotenv

import importlib.util

module_name = "../data_extraction.vector-database.vectorise"
module_path = "../data_extraction/vector-database/vectorise.py"

spec = importlib.util.spec_from_file_location(module_name, module_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

query_vector_database = module.query_vector_database


class Chat:
    def __init__(self, departement, user_name, user_role, collection_name, chroma_client, chat_context_limit):
        self.chat_history = []
        self.chat_context = ""
        self.departement = departement
        self.user_name = user_name
        self.user_role = user_role
        self.collection_name = collection_name
        self.chroma_client = chromadb.PersistentClient(chroma_client)
        self.collection = self.chroma_client.get_collection(collection_name)

        load_dotenv()
        self.GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
        self.chat_context_limit = chat_context_limit # amount of last exchanges of user and LLM that are passed in each prompt

    def load_recent_chat_history(self):
        last_chats = ""

        if len(self.chat_history) <= self.chat_context_limit:
            start_index = 0
        else:
            start_index = len(self.chat_history) - self.chat_context_limit

        for i in range(start_index, len(self.chat_history)):
            text = f"Prompt: {self.chat_history[i]['prompt']}\nAnswer: {self.chat_history[i]['answer']}\n"
            last_chats += text

        return last_chats

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
            return "Dazu kann ich leider nichts sagen."
        
    def get_db_query(self, input, conversation_until_now):

        prompt = f"""
        Erstelle aus der gegebenen Eingabe und den Kontextinformationen Eingabe aus wenigen prägnanten Schlüsselwörtern, der als Input in eine Vektor-Datenbank gegeben werden kann, sodass die relevanten
        Informationen abgerufen werden können, die der Nutzer mit seiner Eingabe vermutlich haben wollte.
        Eingabe:
        {input}
        Kontextinformationen:
        {self.chat_context}
        """

        query = self.make_api_request(prompt).lower()
        print(query)

        return query

    def start_chat(self):
        while True:
            prompt, answer = self.get_answer()
            exchange = {
                'prompt': prompt,
                'answer': answer
            }
            self.chat_history.append(exchange)
            print(answer)
            print("Chat-Context: ", self.chat_context)
            print('\n')

    def get_answer(self):

        # load last five chats
        last_chats = self.load_recent_chat_history()

        print("Prompt: ")

        user_input = input()
        database_query = self.get_db_query(user_input, last_chats)

        chunks = query_vector_database(self.collection, database_query)

        prompt = f"""
        Du bist der KI-Assistent für {self.user_name} der als {self.user_role} in der Abteilung {self.departement} arbeitet. Beantworte die Nutzer-Anfrage basierend auf den gegebenen Informationen. Lass den Nutzer aber nicht wissen
        das du im Hintergrund diese Informationen mit erhälst. Beachte außerdem:
        Bisheriger Kontext zum Chat:
        {self.chat_context} 
        Bisheriger Gesprächsverlauf:
        {last_chats}
        Neue bereitgestellte Informationen: {chunks}
        Neue Nutzer-Anfrage: {user_input}

        Antworte im folgenden JSON-Format. Speichere die Antwort auf die Nutzer-Anfrage unter Berücksichtigung der letzten Chats, der bereitgestellten Informationen und des Kontextes beim Key "answer" als String. Ergänze den bisherigen Chat-Kontext um einen weiteren 
        Satz, der wichtige neue Informationen aus dem Gespräch zusammenfasst und speichere ihn beim Key "context" als String. Fasse dich dabei sehr kurz. Sollten keine neuen Informationen dazugekommen sein, lass den String bei "context" bitte frei. Antworte ausschließlich mit der JSON-Datei.

        {{
            "answer": "",
            "context": "",
        }}

        """

        output = self.make_api_request(prompt)
        output_json = json.loads(output.split('json')[1].replace('\n', '').replace("```", ""))

        self.chat_context += output_json['context'] + " "
        return user_input, output_json['answer']

    def remove_stopwords(self, text):
        # put all words in a list
        word_list = []
        current_word = ""
        for char in text:
            if char != " ":
                current_word += char
            else:
                word_list.append(current_word)
                current_word = ""

        # load stop_words
        stop_words_file = open("./stopwords/german")
        stop_words = [re.sub('\n', '', word) for word in stop_words_file.readlines()]

        # filter out stop_words and return cleaned text
        filtered_words = [word for word in word_list if word not in stop_words]
        filtered_text = ""

        for word in filtered_words:
            filtered_text += word + " "

        return filtered_text

chat = Chat(
    departement= "Einkauf",
    user_name= "Tom Weber",
    user_role= "Sachbearbeiter Einkauf",
    collection_name= "purchasing_dept11",
    chroma_client= "../data_extraction/vector-database/chroma_db",
    chat_context_limit = 5
)

chat.start_chat()
