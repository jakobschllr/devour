import ollama
import requests
from vector_database.database import Database
import chromadb
import re
import json
import os
from dotenv import load_dotenv

 
class Chat:
    def __init__(self, chat_history, chat_context, department, user_name, user_role,
                 individual_prompt, tone, user_context, chat_context_limit, collection_name, db_path):
        self.chat_history = chat_history
        self.chat_context = chat_context #.decode('utf-8')
        self.department = department
        self.user_name = user_name
        self.user_role = user_role
        self.chat_context_limit = chat_context_limit # amount of last exchanges of user and LLM that are passed in each prompt
        self.individual_prompt = individual_prompt
        self.tone = tone
        self.user_context = user_context #.decode('utf-8')
        self.database = Database(db_path, collection_name)

        load_dotenv()
        self.GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

    def load_recent_chat_history(self):
        last_chats = ""

        if len(self.chat_history) <= self.chat_context_limit:
            start_index = 0
        else:
            start_index = len(self.chat_history) - self.chat_context_limit

        for i in range(start_index, len(self.chat_history)):
            text = f"Prompt: {self.chat_history[i]['user_prompt']}\nAnswer: {self.chat_history[i]['chatbot_response']}\n"
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
        Erstelle aus der gegebenen Eingabe und den Kontextinformationen einen Satz, der als Input in eine Vektor-Datenbank gegeben werden kann, sodass die relevanten
        Informationen abgerufen werden können, die der Nutzer mit seiner Eingabe vermutlich haben wollte.
        Eingabe:
        {input}
        Kontextinformationen:
        {self.chat_context}
        """

        query = self.make_api_request(prompt).lower()
        return query
    
    def rethink_vector_db_output(self, user_prompt, query_to_vector_db, vector_db_results):
        prompt = f"""
        Bewerte ob die Antwort aus der Vektordatenbank passend ist, bzw. ob der Query gut war und die nötigen Informationen
        gefunden wurden. Sollte dies nicht der Fall sein erstelle einen besseren Query mit dem die Vektordatenbank angesprochen werden kann.
        Ein Nutzer hat folgenden Prompt abgeschickt:
        {user_prompt}.
        Um eine passende Antwort in der Vektordatenbank zu finden wurde diese mit diesem Query angefragt:
        {query_to_vector_db}
        Das sind die Ergebnisse aus der Vektordatenbank:
        {vector_db_results}
        Das ist der Kontext aus dem Chat:
        {self.chat_context}

        Antworte ausschließlich mit dem angepassten Query und mit nichts anderem. Wenn du den Query und die Ergebnisse aus der Vektordatenbank
        gut findest, antworte einfach exakt wieder mitdemselben Query.
        """
        new_query = self.make_api_request(prompt).lower()
        return new_query


    def prompt_model(self, user_prompt, generate_auto_title):
        answer, auto_title = self.get_answer(user_prompt, generate_auto_title)
        return answer, auto_title


    def get_answer(self, user_prompt, generate_auto_title):

        # load last five chats
        last_chats = self.load_recent_chat_history()

        database_query_1 = self.get_db_query(user_prompt, last_chats)
        vector_db_output_1 = self.database.query_database(database_query_1)
        print("VectorDB Query 1: ", database_query_1)
        print("VectorDB Output 1: ", vector_db_output_1)

        # think again
        database_query_2 = self.rethink_vector_db_output(user_prompt, database_query_1, vector_db_output_1)
        vector_db_output_2 = self.database.query_database(database_query_2)

        print("VectorDB Query 2: ", database_query_2)
        print("VectorDB Output 2: ", vector_db_output_2)

        # Chatbot soll Titel vergeben für den Chat
        if generate_auto_title:
            prompt = f"""
            Du bist der KI-Assistent für {self.user_name} der als {self.user_role} in der Abteilung {self.department} arbeitet. Beantworte die Nutzer-Anfrage basierend auf den gegebenen Informationen. Lass den Nutzer aber nicht wissen
            das du im Hintergrund diese Informationen mit erhälst. Beachte außerdem:

            Neue bereitgestellte Informationen: {vector_db_output_2}
            Neue Nutzer-Anfrage: {user_prompt}

            Nutze diesen Ton: {self.tone}
            Individuelle Nutzer-Konfiguration: {self.individual_prompt}

            Antworte im folgenden JSON-Format. Speichere die Antwort auf die Nutzer-Anfrage unter Berücksichtigung der bereitgestellten Informationen und des Kontextes über
            den User als String-Value beim key "answer". Erstelle außerdem einen einfachen kurzen Titel für den Chat und speichere ihn als String
            beim Key "chat_title". Beachte auch den angegebenen Ton und die individuellen Nutzer-Konfigurationen.
            Antworte ausschließlich mit der JSON-Datei.

            {{
                "answer": "",
                "chat_title": "",
            }}

            """
        # Chat hat bereits einen Titel
        else:
            prompt = f"""
            Du bist der KI-Assistent für {self.user_name} der als {self.user_role} in der Abteilung {self.department} arbeitet. Beantworte die Nutzer-Anfrage basierend auf den gegebenen Informationen. Lass den Nutzer aber nicht wissen
            das du im Hintergrund diese Informationen mit erhälst. Beachte außerdem:

            Bisheriger Gesprächsverlauf:
            {last_chats}

            Kontext zum bisherigen Chat:
            {self.chat_context}
            
            Kontext zum User:
            {self.user_context}

            Nutze diesen Ton: {self.tone}
            Beachte diese individuellen Nutzer-Konfigurationen: {self.individual_prompt}

            Neue bereitgestellte Informationen: {vector_db_output_2}
            Neue Nutzer-Anfrage: {user_prompt}

            Antworte im folgenden JSON-Format. Speichere die Antwort auf die Nutzer-Anfrage unter Berücksichtigung des bisherigen Gesprächsverlaufs,
            des Kontextes aus diesem Chat, des Kontextes über den User und der bereitgestellten Informationen als String-Value beim key "answer". 
            Beachte auch den angegebenen Ton und die individuelle Nutzer-Konfiguration. Antworte ausschließlich mit der JSON-Datei.

            {{
                "answer": "",
            }}

            """

        output = self.make_api_request(prompt)
        output_json = json.loads(output.split('json')[1].replace('\n', '').replace("```", ""))

        # # update chat context
        # print("current chat context ", self.chat_context)
        # print("New chat context:", output_json['chat_context'])
        # self.chat_context += output_json['chat_context'] + " "

        # # update user context
        # print("User context ", self.user_context)
        # self.user_context += output_json['user_context'] + " "

        # if generate_auto_title:
        #     return output_json['answer'], self.chat_context, self.user_context, output_json["chat_title"]
        # else:
        #     return output_json['answer'], self.chat_context, self.user_context, None

        print("PROMPT: ", prompt)

        if generate_auto_title:
            return output_json['answer'], output_json["chat_title"]
        else:
            return output_json['answer'], None


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

    def test_chat(self, query) -> str:

        last_chats = self.load_recent_chat_history()
        database_query = self.get_db_query(query, last_chats)

        chunks = self.database.query_database(database_query)

        prompt = f"""
        Du bist der KI-Assistent für {self.user_name} der als {self.user_role} in der Abteilung {self.department} arbeitet. Beantworte die Nutzer-Anfrage basierend auf den gegebenen Informationen. Lass den Nutzer aber nicht wissen
        das du im Hintergrund diese Informationen mit erhälst. Beachte außerdem:
        Bisheriger Kontext zum Chat:
        {self.chat_context} 
        Bisheriger Gesprächsverlauf:
        {last_chats}
        Neue bereitgestellte Informationen: {chunks}
        Neue Nutzer-Anfrage: {query}

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
        return output_json['answer']

    def start_chat_test(self, queries):
        answers = []
        for query in queries:
            answers.append(self.test_chat(query))
            exchange = {
                'prompt': query,
                'answer': answers[-1]
            }
            self.chat_history.append(exchange)

        return answers
