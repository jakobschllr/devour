import asyncio
from collections import defaultdict
import os
from typing import List, Dict, Optional
from datetime import datetime
from tqdm import tqdm
from unstructured.partition.pdf import partition_pdf
from unstructured.documents.elements import Element
from unstructured.staging.base import elements_to_json
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from django_backend.vector_database.database import Database
from unstructured.chunking.title import chunk_by_title
import logging


class PDFExtractor:
    """
    Class for extracting content from PDFs, processing the elements,
    and storing them in a vector database.
    config = {
        chunk_size: int = 1500,
        chunk_overlap: int = 300,
        languages: List[str] = ["deu", "eng"],
        chunking_strategy: str = "", 
        max_characters: int = None,
        new_after_n_chars : int = None
        }
        config : dict = {
                            'chunk_size': 1500,
                            'chunk_overlap': 300,
                            'languages': ["deu", "eng"],
                            'chunking_strategy': "by_title", 
                            'max_characters':4000,
                            'max_partition':None,
                            'new_after_n_chars':3700,
                            'combine_text_under_n_chars':250,
                            'overlap':300,
                            'overlap_all':True,}
    """
    
    def __init__(self, db : Database, **kwaargs):
        
        """Initialize the PDF extractor with configurable parameters."""
        # TODO Test the different chunking startegies 
        self.vector_db = db
        self.config = kwaargs
        self.languages = self.config.get("languages", ['eng'])

        # Do not Use this Character Splitter use Unstructed Chunking module
        # self.text_splitter = RecursiveCharacterTextSplitter(  # TODO add max_chars, min_chars, new_after_n_n
        #     chunk_size=self.config.get("chunk_size"),
        #     chunk_overlap=self.config.get("chunk_overlap"),
        # )
    
    def partition_pdf(self, pdf_path: str, export_json: bool = False, json_path: Optional[str] = None) -> Dict:
        """
        Extract content from a PDF file, process it, and store in vector database.
        
        Args:
            pdf_path: Path to the PDF file
            export_json: Whether to export elements as JSON
            json_path: Path for JSON export (if None, uses the PDF filename)
            progress_callback: Optional callback to report progress
            
        Returns:
            Dictionary with processing statistics
        """
        try:

            logging.info("Partitioning the PDF")
            
            # Extract elements from PDF
            elements = partition_pdf(
                pdf_path,
                strategy='hi_res',
                infer_table_structure=True,
                hi_res_model_name='yolox',
                languages=self.languages,
                # chunking_strategy=self.config.get("chunking_strategy"), # Chunking is done under
                # max_characters=self.config.get("max_partition"),
            )

            logging.info(f"Extracted {len(elements)} Elements. Now Chunking Elements...")

            chunked_elem = chunk_by_title(elements, 
                        combine_text_under_n_chars=self.config.get('combine_text_under_n_chars', 250), 
                        max_characters=self.config.get('max_charracters', 1500),
                        new_after_n_chars=self.config.get('new_after_n_chars', 1000),
                        overlap=self.config.get('overlap', 250))
            

            if export_json:
                    if json_path is None:
                        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
                        json_path = f"/home/jakobschiller/devour/data_extraction/docs/{base_name}.json"
                    elements_to_json(chunked_elem, filename=json_path)
            
            # Notify progress
            
            
            # Group and process elements
            documents = self._process_elements(chunked_elem, pdf_path)

            logging.info(f"Processed {len(documents)}")
            
            # Store in vector database
            # TODO Store vector in new datatbase with meta data
            self.vector_db.embed_documents(documents)
            
            # Export to JSON if requested
            
            
            return {
                "status": "success",
                "statistics": {
                    "total_elements": len(elements),
                    "documents": len(documents),
                }
            }
            
        except Exception as e:
            logging.error(e)
            return {
                "status": "error",
                "error": str(e)
            }
    
    def extract_from_scanned_pdf(self, pdf_path: str):
        """Handle scanned PDFs that might need OCR."""
        # Configure partition_pdf with OCR settings
        # ...

    def _process_elements(self, chunked_elem: List[Element], pdf_path: str) -> list[Document]:

        # element_by_id = self._catalog_elements(chunked_elem)
        # grouped, ungrouped = self._group_elements(chunked_elem)
        documents = self._create_documents(chunked_elem, pdf_path)
        
        return documents

    def _catalog_elements(self, elements: List[Element]) -> Dict[str, Element]:
        """Catalog elements by their ID."""
        element_by_id = {}
        logging.info("Cataloging Elements")
        for element in tqdm(elements):
            element_id = getattr(element, "id", str(id(element)))
            element_by_id[element_id] = element
        return element_by_id

    def _group_elements(self, elements: List[Element]) -> tuple[dict, list]:
        """Group elements by their parent ID."""
        logging.info("Grouping Elements")
        grouped = defaultdict(list)
        ungrouped = []
        for element in tqdm(elements):
            parent_id = element.metadata.parent_id
            if parent_id is not None:
                grouped[parent_id].append(element)
            else:
                ungrouped.append(element)
        return grouped, ungrouped

    def _create_documents(self, element_list: List[Element], pdf_path: str) -> List[Document]:
        """Create LangChain documents from grouped and ungrouped elements."""
        logging.info("Creating Documents")
        documents = []
        doc_title = self.config.get('document_title', os.path.basename(pdf_path))
            
            # Process each element in the group
        for elem in element_list:
            if elem.metadata.text_as_html is not None:
                text = elem.metadata.text_as_html
            else:
                text = elem.text

            formalised_text = f"Section from {doc_title} : {text}"
        
            # Create metadata
            metadata = {
                "filename": doc_title,
                "full_path": pdf_path,
                "extraction_date": datetime.now().isoformat(),
                # "page_number": elem.metadata.page_number,
                # "category_depth": elem.metadata.category_depth
            }
        
            # Create LangChain Document
            doc = Document(page_content=formalised_text, metadata=metadata)
            documents.append(doc)
        
        return documents

    def batch_extract(self, pdf_paths: List[str], export_json: bool = False) -> List[Dict]:
        """Process multiple PDFs and return results for each."""
        results = []
        for pdf_path in pdf_paths:
            result = self.partition_pdf(pdf_path, export_json)
            results.append(result)
        return results