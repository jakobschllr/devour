from collections import defaultdict
import os
from unstructured.partition.pdf import partition_pdf
from unstructured.staging.base import elements_to_json
import json
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from django_backend.vector_database.database import Database

filename = "/home/jakobschiller/devour/data_extraction/docs/stratigicManagement.pdf"
file_path = "/home/jakobschiller/devour/data_extraction/docs/"

vector_db = Database(path_to_db="/home/jakobschiller/devour/dbs/docs_db", collection_name="adidas")


elements = partition_pdf(filename,
                         strategy='hi_res',
                         infer_table_structure=True,
                         model_name='yolox',
                        #  max_characters=4000,
                        #  new_after_n_chars=3700,
                        #  combine_text_under_n_chars=2000,
                        #  overlap=300,
                        #  overlap_all=True,
                         languages=['eng'])

documents = []
grouped = defaultdict(list)
ungrouped = []

element_by_id = {}  # Store elements by their ID for easy lookup

# First pass: catalog elements by their ID
for element in elements:
    # Use element.id if it exists, otherwise create a unique identifier
    element_id = getattr(element, "id", str(id(element)))
    element_by_id[element_id] = element

    parent_id = element.metadata.parent_id
    if parent_id is not None:
        grouped[parent_id].append(element)
    else : 
        ungrouped.append(element)


print(f"Processed {len(elements)} elements into {len(grouped.keys())} groups")

print(f"Ungrouped Elements: {len(ungrouped)}")


for parent_id, elements_list in grouped.items():

    parent_element = element_by_id[parent_id]
    text_elements = []

    for elem in elements_list:
        if elem.category == "Table":
            text_elements.append(elem.metadata.text_as_html)
        else:
            text_elements.append(str(elem))

    text_elements.insert(0, str(parent_element))

    combined_text = "\n".join(text_elements)

    # Create metadata
    metadata = {
        "parent_id": parent_id,
        "filename": os.path.basename(filename),
        "element_count": len(elements_list),
        "category_depth": getattr(parent_element, "category_depth", None),
        "Title": getattr(parent_element, "text", None)

    }
    
    # Create LangChain Document
    doc = Document(page_content=combined_text, metadata=metadata)
    documents.append(doc)

# Split into chunks
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1500,
    chunk_overlap=300
)
chunks = text_splitter.split_documents(documents)

for c in chunks:
    print(c)
    print()

print(f"Processed {len(documents)} documents into {len(chunks)} chunks")

vector_db.save_embedding(vector_db.embed([ chunk.page_content for chunk in chunks]))

elements_to_json(elements, filename='/home/jakobschiller/devour/data_extraction/docs/Addidas.json')
# elements_to_json(ungrouped, filename='/home/jakobschiller/devour/data_extraction/docs/DatenblattLaunchPadUngrouped.json')



