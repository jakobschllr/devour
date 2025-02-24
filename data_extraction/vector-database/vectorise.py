import json
import nltk
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import chromadb
import numpy as np


CHUNK_ID = 0 # Global variable to count the Chunks and set their IDs

embedding_models  = [
    "Alibaba-NLP/gte-Qwen2-1.5B-instruct",
     "all-MiniLM-L6-v2",
     "Linq-AI-Research/Linq-Embed-Mistral",
     "Alibaba-NLP/gte-Qwen2-7B-instruct",
     "intfloat/multilingual-e5-large-instruct",
     "NovaSearch/stella_en_1.5B_v5"
]

#The model to be used by encoding and querying
model = SentenceTransformer(embedding_models[0], trust_remote_code=True) 


def semantic_chunking(initial_chunks: list[str]) -> list[str]:
    """
    Joins similar chunks (sentences, paragraphs etc) together 
    """
    # model = SentenceTransformer(embedding_models[0])
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



def embed_and_save(collection : chromadb.Collection, chunks : list[str]) -> chromadb.Collection:
    """
    Encodes chunks and saves it in a collection (Vector database table)
    """

    global CHUNK_ID

    data = {
        "chunks": [],
        "embeddings": [],
        "ids": [],
    }

    for chunk in chunks:
        data["chunks"].append(chunk)
        data["ids"].append(CHUNK_ID)
        data["embeddings"].append(model.encode(chunk))
        CHUNK_ID += 1

    # print(data["chunks"], sep="\n")
    # print(data["ids"])

    collection.add(
        documents= [chunk for chunk in data["chunks"]],
        ids=["id" + str(id) for id in data["ids"]],
        embeddings=[embedding for embedding in data["embeddings"]]
    )

    return collection



def embed_and_save_data(collection : chromadb.Collection) -> chromadb.Collection:
    """
    Reads data from the 5 data_i.json JSON files and embeds each paragraph,
    chunks sentences together using semantic chunking, 
    embeds department infor and employee info,
    as well as meeting infos
    """

    for i in range(1,6):
        
        with open(f"/home/jakobschiller/devour/data_extraction/vector-database/purchasing_departement/data_{i}.json", 'r') as file:
            data = json.load(file)

        sentences = data['sentences']


        employee_info =[' '.join(list(elem.values())) for elem in data["employee_info"]]

        paragraphs = [elem.popitem()[1] for elem in data["paragraphs"]]

        sentence_chunks = semantic_chunking(sentences)
        # client = create_and_save_vectors(client, )
        collection = embed_and_save(collection, [data["departement_info"]])
        collection = embed_and_save(collection, employee_info)
        collection = embed_and_save(collection, sentence_chunks)
        collection = embed_and_save(collection, paragraphs)

    return collection


def query_vector_database(collection : chromadb.Collection, query_text : str) -> list[str]:
    # collection = client.get_collection(collection_name) # num_results is amount chunks that match to user query and will be outputted
    query_embedding = model.encode(query_text)
    result = collection.query(query_embeddings=query_embedding, n_results=8)
    # print(result["documents"], end="\n\n")
    return result['documents']


def rank_results(results: chromadb.QueryResult ) -> list[str]:
    
    return results