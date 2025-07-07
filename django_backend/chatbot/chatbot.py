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
        print(query)

        return query

    def prompt_model(self, user_prompt, generate_auto_title):
        answer, auto_title = self.get_answer(user_prompt, generate_auto_title)
        return answer, auto_title


    def get_answer(self, user_prompt, generate_auto_title):

        # load last five chats
        last_chats = self.load_recent_chat_history()

        database_query = self.get_db_query(user_prompt, last_chats)

        chunks = self.database.query_database(database_query)

        if generate_auto_title:
            prompt = f"""
            Du bist der KI-Assistent für {self.user_name} der als {self.user_role} in der Abteilung {self.department} arbeitet. Beantworte die Nutzer-Anfrage basierend auf den gegebenen Informationen. Lass den Nutzer aber nicht wissen
            das du im Hintergrund diese Informationen mit erhälst. Beachte außerdem:

            Neue bereitgestellte Informationen: {chunks}
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

            Neue bereitgestellte Informationen: {chunks}
            Neue Nutzer-Anfrage: {user_prompt}

            Antworte im folgenden JSON-Format. Speichere die Antwort auf die Nutzer-Anfrage unter Berücksichtigung des bisherigen Gesprächsverlaufs,
            des Kontextes aus diesem Chat, des Kontextes über den User und der bereitgestellten Informationen als String-Value beim key "answer". 
            Beachte auch den angegebenen Ton und die individuelle Nutzer-Konfiguration. Antworte ausschließlich mit der JSON-Datei.

            {{
                "answer": "",
            }}

            """

            # Antworte im folgenden JSON-Format. Speichere die Antwort auf die Nutzer-Anfrage unter Berücksichtigung des bisherigen Gesprächsverlaufs,
            # des Kontextes aus diesem Chat, des Kontextes über den User und der bereitgestellten Informationen als String-Value beim key "answer". Ergänze den bisherigen Chat-Kontext,
            # um einen weiteren Satz, der wichtige neue Informationen über das Gespräch zusammenfasst und speichere ihn beim Key "chat_context" als String.
            # Erängze den bisherigen User-Kontext, um einen weiteren Satz, der wichtige neue Informationen über den Nutzer enthält und speichere ihn beim Key "user_context"
            # als String. Fasse dich dabei sehr kurz. Sollten für chat_context und user_context keine wesentlichen neuen Informationen dazugekommen sein, lasse
            # die beiden Values in der JSON Datei einfach als leere Strings. Beachte auch den angegebenen Ton und die individuelle Nutzer-Konfiguration.
            # Antworte ausschließlich mit der JSON-Datei.

            # {{
            #     "answer": "",
            #     "chat_context": "",
            #     "user_context": "",
            # }}

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
