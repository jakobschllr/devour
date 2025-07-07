
from django_backend.vector_database.database import Database
from pdf_extractor import PDFExtractor
from django_backend.vector_database.reranker import Reranker
import logging

logging.basicConfig(filename='/home/jakobschiller/devour/backend_log/pdflog.log', level=logging.INFO, 
                    format='%(asctime)s %(levelname)s %(message)s')

db_path = "/home/jakobschiller/devour/dbs/ndb/rechner"
pdf_path = "/home/jakobschiller/devour/data_extraction/docs/DatenblattLaunchPad.pdf"
col_name = "datenblatt1"
my_db = Database(path_to_db=db_path, collection_name=col_name)

logging.info("Database Created")

# pdf_extractor = PDFExtractor(my_db, document_title="Tiwa Launchpad")

logging.info("Extractor created")

# response = pdf_extractor.partition_pdf(pdf_path, export_json=True, json_path="/home/jakobschiller/devour/data_extraction/docs/blatt1.json")

# logging.info(f"Extraction Completed. \n {response}")

logging.info(f"Database Count : {my_db.collection.count()}")

results = my_db.query_database("What toolchains and IDEs are supported for developing applications with this LaunchPad ?")



# reranker= Reranker("Qwen/Qwen3-Embedding-0.6B")

# print(reranker.proces_inputs([result.page_content for result in results]))

for r in results:
    logging.info(str(r))
    print()