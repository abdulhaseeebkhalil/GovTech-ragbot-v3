import os
import sys
from dotenv import load_dotenv

# Load env variables from root or backend
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

sys.path.append(os.path.join(os.path.dirname(__file__), 'legal'))

from .legal.pdf_processor import AdvancedPDFProcessor
from .legal.vector_store import EnhancedQdrantVectorStore

def main():
    qdrant_url = os.getenv('QDRANT_URL')
    qdrant_api_key = os.getenv('QDRANT_API_KEY')
    collection_name = os.getenv('QDRANT_COLLECTION_NAME', 'kpk_local_govt_act_2013_st')

    print(f"Connecting to Qdrant at: {qdrant_url}")
    print(f"Collection name: {collection_name}")

    if not qdrant_url or not qdrant_api_key:
        print("ERROR: QDRANT_URL and QDRANT_API_KEY must be set in .env")
        sys.exit(1)

    pdf_path = os.path.join(os.path.dirname(__file__), "..", "docs", "THE_KHYBER_PAKHTUNKHWA_LOCAL_GOVERNMENT_ACT_2013.pdf")
    if not os.path.exists(pdf_path):
        print(f"ERROR: PDF file not found at: {pdf_path}")
        sys.exit(1)

    print(f"Found PDF file: {pdf_path}")
    print("Processing and chunking PDF...")
    processor = AdvancedPDFProcessor()
    chunks_with_metadata, structure = processor.process_pdf_section_scoped(pdf_path)
    print(f"Generated {len(chunks_with_metadata)} chunks.")

    print("Initializing Qdrant Vector Store...")
    vector_store = EnhancedQdrantVectorStore(
        url=qdrant_url,
        api_key=qdrant_api_key,
        collection_name=collection_name
    )

    print("Uploading and indexing chunks into Qdrant...")
    vector_store.add_documents_with_metadata(chunks_with_metadata)
    print("✅ Successfully uploaded and indexed legal PDF into Qdrant!")

if __name__ == "__main__":
    main()
