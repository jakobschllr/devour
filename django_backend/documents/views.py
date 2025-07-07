import logging
import os
import uuid
import pypdf
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from pdf_extractor import PDFExtractor # type: ignore


# Create your views here.

logging.basicConfig(filename=os.getenv('LOG_FILE'), level=logging.INFO, 
                    format='%(asctime)s %(levelname)s %(message)s')

PATH_TO_PDF = os.getenv('PATH_TO_PDF_FILES')
PATH_TO_WORD = os.getenv('PATH_TO_WORD_FILES') 
os.makedirs(PATH_TO_PDF, exist_ok=True)

extractor_config = {"chunk_size": 1500,
                    "chunk_overlap": 300,
                    "languages": ["eng"]}

# Initialize the PDF extractor
pdf_extractor = PDFExtractor(
    collection_name="documents",  # Default collection name
    vector_db_path="/home/jakobschiller/devour/dbs/docs_db",
    config=extractor_config
)

@csrf_exempt
def upload_documents(request):
    """
    Endpoint to receive and manage PDF Files
    """

    #TODO Brauche noch Uset Infos, und Abteilungsinfo übergeben

    if request.method != 'POST':
        return JsonResponse({'status': 400, 'message': 'Request method Error'})
    
    try:
        file = request.FILES['document']

        if file.name.endswith('.pdf'):
            file_path = save_file(PATH_TO_PDF, file)
            
            # Extract and process the PDF
            result = pdf_extractor.partition_pdf(
                pdf_path=file_path,
            )
            
            if result["status"] == "success":
                return JsonResponse({
                    'status': 200, 
                    'message': "File uploaded and processed successfully", 
                    'data': {
                        'file_name': file.name,
                        'size': file.size,
                        'stats': result["statistics"]
                    }
                })
            else:
                return JsonResponse({
                    'status': 500, 
                    'message': "File uploaded but processing failed", 
                    'error': result["error"]
                })

    except Exception as e:
        return JsonResponse({'status': 400, 'message': "Could not save document", 'cause': str(e)})



def save_file(upload_dir, file):
    try:
        unique_filename = f"{uuid.uuid4()}_{file.name}"
        file_path = os.path.join(upload_dir, unique_filename)
        with open(file_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        if file_path is None:
            raise Exception("File Path is None")
        return file_path
    except Exception as e:
        logging.error(f"Error extracting text from PDF: {str(e)}")
        raise e