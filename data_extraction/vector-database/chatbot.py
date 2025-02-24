import ollama
import requests
from vectorise import query_vector_database
import chromadb
import re
import json
import os

def remove_stopwords(text):
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

def chatbot():
    print("Prompt: ")
    user_prompt = input()
    print('\n')

    collection_name = "purchasing_dept6"
    client = chromadb.PersistentClient("./chroma_db")

    chunks = query_vector_database(client, collection_name, user_prompt)

    print(chunks)

    prompt = f"""
    Beantworte die Nutzer-Anfrage basierend auf den gegebenen Informationen. 
    Informationene: {chunks}
    Nutzer-Anfrage: {user_prompt} 
    """

    models = [
        "mistral:7b",
        "zephyr:7b",
        "llama2",
        "deepseek-r1:7b", # if deepseek is used the thinking process in the answer must be filtered out
        "glm4:9b"
    ]

    # temperature = 0.9 # from 0.1 to 1.0; the higher the temperature the more creative but less prezise answers
    # max_tokens = 8192
    # top_p = 1.0 # only those next possible tokens are considered, whose cumulated probalities don't extend the top-p value 

    GEMINI_API_KEY = os.environ['GEMINI_API_KEY']

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

    headers = {
        "Content-Type": "application/json"
    }

    data = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))
    return response.json()['candidates'][0]['content']['parts'][0]['text']

    # try:
    #     response = ollama.chat(
    #         model=models[3],
    #         messages=[{"role": "user", "content": prompt}],
    #         options={
    #             "temperature": temperature,
    #             "top_p": top_p,
    #             "num_predict": max_tokens,
    #             "stream": False
    #             }
    #         )
        
    #     output = response["message"]["content"]
    #     return output
    
    # except Exception as e:
    #     print("Error: ", e)

answer = chatbot()
print(answer)