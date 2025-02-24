from vectorise import create_new_collection_with_data
import chromadb

abteilungs_name = "purchasing_dept6"

client = chromadb.PersistentClient(path="./chroma_db")

print(client.list_collections())

# client.get_or_create_collection(abteilungs_name).add()

client = create_new_collection_with_data(client, abteilungs_name)
