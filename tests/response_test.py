import os
from dotenv import load_dotenv
from chatbot.chatbot import Chat
from google import genai
from google.genai import types


load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

client = genai.Client(api_key=GEMINI_API_KEY, http_options=types.HttpOptions(api_version='v1alpha'))

path_to_scripts = "/home/jakobschiller/devour/data_extraction/transcripts/purchasing_departement/"

def upload_trankripts(path, num=5):
    for i in range(1, num+1):
        client.files.upload(path + str(i) + ".txt")


department= "Einkauf"
user_name= "Tom Weber"
user_role= "Sachbearbeiter Einkauf"
collection_name= "Einkaufsabteilung"

# Function to generate responses using your RAG system
def generate_test_response(queries : list[str]):
    chat = Chat(
    department= department,
    user_name= user_name,
    user_role= user_role,
    collection_name= collection_name,
    chroma_client= "../vector_database/database",
    chat_context_limit = 5
    )

    answers = chat.start_chat_test(queries)
    return answers

def ai_responses(queries : list[str]):
    
    for q in queries:
        prompt = f"""
            Du bist der KI-Assistent für {user_name} der als {user_role} in der Abteilung {department} arbeitet. Beantworte die Nutzer-Anfrage basierend auf den gegebenen Informationen. Lass den Nutzer aber nicht wissen
            das du im Hintergrund diese Informationen mit erhälst. Beachte außerdem:
            Den Kontext des Chats, und der 
            Neue Nutzer-Anfrage: {q}

            Antworte im folgenden JSON-Format. Speichere die Antwort auf die Nutzer-Anfrage unter Berücksichtigung der letzten Chats, der bereitgestellten Informationen und des Kontextes beim Key "answer" als String. Ergänze den bisherigen Chat-Kontext um einen weiteren 
            Satz, der wichtige neue Informationen aus dem Gespräch zusammenfasst und speichere ihn beim Key "context" als String. Fasse dich dabei sehr kurz. Sollten keine neuen Informationen dazugekommen sein, lass den String bei "context" bitte frei. Antworte ausschließlich mit der JSON-Datei.

            {{
                "answer": "",
                "context": "",
            }}

            """

# Function to evaluate response quality using an LLM
def evaluate_response(query, generated_response, expected_response):
    prompt = f"""
    You are evaluating the quality of a generated response for a query. 
    Query: {query}
    Expected Response: {expected_response}
    Generated Response: {generated_response}

    Rate the quality of the generated response on a scale of 1-10, where:
    - 1 = Completely incorrect or irrelevant
    - 10 = Perfectly correct and relevant

    Provide a brief explanation for your rating.
    """
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# Run response generation tests
for test_case in test_cases:
    query = test_case["query"]
    expected_response = test_case["expected_response"]
    generated_response = generate_response(query)
    evaluation = evaluate_response(query, generated_response, expected_response)
    print(f"Query: {query}")
    print(f"Generated Response: {generated_response}")
    print(f"Evaluation: {evaluation}")
    print("------")