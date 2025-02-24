import json
import nltk
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import chromadb
import numpy as np


CHUNK_ID = 0

# nltk.download('punkt_tab')

embedding_models  = [
     "all-MiniLM-L6-v2",
     "Linq-AI-Research/Linq-Embed-Mistral",
     "Alibaba-NLP/gte-Qwen2-7B-instruct",
     "intfloat/multilingual-e5-large-instruct",
     "NovaSearch/stella_en_1.5B_v5"
]

def preprocess_summary(sentences):
    
    # Initialize sentence transformer model
    model = SentenceTransformer("Linq-AI-Research/Linq-Embed-Mistral")
    
    # Compute embeddings for each sentence
    embeddings = np.array(model.encode(sentences))
    
    # Group related sentences (simple approach using cosine similarity)
    chunks = []
    current_chunk = [sentences[0]]
    for i in range(1, len(sentences)):
        similarity = cosine_similarity([embeddings[i-1]], [embeddings[i]])[0][0]
        if similarity > 0.8:  # Adjust threshold as needed; the higher number, the more similarities will be found.
            current_chunk.append(sentences[i])
        else:
            chunks.append(' '.join(current_chunk))
            current_chunk = [sentences[i]]
    chunks.append(' '.join(current_chunk))

    return chunks


def semantic_chunking(initial_chunks):
    model = SentenceTransformer(embedding_models[1])
    embeddings = model.encode(initial_chunks)
    
    semantic_chunks = []
    current_chunk = [initial_chunks[0]]
    
    for i in range(1, len(initial_chunks)):
        similarity = np.dot(embeddings[i-1], embeddings[i]) / (np.linalg.norm(embeddings[i-1]) * np.linalg.norm(embeddings[i]))
        if similarity > 0.7:  # Adjust threshold as needed
            current_chunk.append(initial_chunks[i])
        else:
            semantic_chunks.append(' '.join(current_chunk))
            current_chunk = [initial_chunks[i]]
    
    semantic_chunks.append(' '.join(current_chunk))
    return semantic_chunks



def create_and_save_vectors(client, chunks, collection_name):
    global CHUNK_ID
    collection = client.get_or_create_collection(collection_name)

    data = {
        "chunks": [],
        "embeddings": [],
        "ids": [],
    }

    for chunk in chunks:
        data["chunks"].append(chunk)
        data["ids"].append(CHUNK_ID)
        CHUNK_ID += 1

    print(data)

    collection.add(
        documents= [chunk for chunk in data["chunks"]],
        ids=["id" + str(id) for id in data["ids"]],
        embeddings
    )

    return client



def create_new_collection_with_data(client, collection_name):

    for i in range(1,6):
        
        with open(f"/home/jakobschiller/devour/data_extraction/vector-database/purchasing_departement/data_{i}.json", 'r') as file:
            sentences = json.load(file)["sentences"]

        chunks = preprocess_summary(sentences)
        client = create_and_save_vectors(client, chunks, collection_name)

    return client


def query_vector_database(client, collection_name, query):
    

    collection = client.get_collection(collection_name) # num_results is amount chunks that match to user query and will be outputted
    result = collection.query(query_texts=query, n_results=7)
    return result['documents']