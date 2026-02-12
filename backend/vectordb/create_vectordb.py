"""
Create FAISS vector database from scraped data
Processes blogs, repair guides, and policy documents with paragraph chunking
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any
import uuid
import pickle

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document


# Paths configuration
SCRIPT_DIR = Path(__file__).parent
BACKEND_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent
PROCESSED_DATA_DIR = PROJECT_ROOT / "scraping" / "data" / "processed"
VECTOR_DB_DIR = BACKEND_DIR / "vectordb" / "faiss_index"

# File paths
BLOG_FILES = [
    PROCESSED_DATA_DIR / "dishwasher_blogs.json",
    PROCESSED_DATA_DIR / "refrigerator_blogs.json"
]

REPAIR_FILES = [
    PROCESSED_DATA_DIR / "dishwasher_parts.json",
    PROCESSED_DATA_DIR / "refrigerator_parts.json"
]

POLICY_FILE = PROCESSED_DATA_DIR / "policies.json"

# Chunking configuration
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
CHUNK_SEPARATORS = ["\n\n", "\n", " ", ""]


def create_text_splitter():
    """Create RecursiveCharacterTextSplitter for paragraph chunking."""
    return RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=CHUNK_SEPARATORS,
        length_function=len,
    )


def load_json_file(file_path: Path) -> List[Dict]:
    """Load JSON file and return parsed data."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def chunk_document(text: str, text_splitter) -> List[str]:
    """Chunk a document using the text splitter."""
    if not text or not text.strip():
        return []
    return text_splitter.split_text(text)


def process_blogs(text_splitter) -> List[Document]:
    """
    Process blog documents with chunking.

    Returns:
        List of LangChain Document objects
    """
    documents = []

    for blog_file in BLOG_FILES:
        print(f"Processing {blog_file.name}...")
        blogs = load_json_file(blog_file)

        for blog in blogs:
            # Extract content and chunk it
            content = blog.get('content', '')
            chunks = chunk_document(content, text_splitter)

            # Generate source ID for this blog
            source_id = str(uuid.uuid4())

            # Create Document for each chunk
            for chunk_idx, chunk_text in enumerate(chunks):
                # Create metadata (exclude content field since it's embedded)
                metadata = {
                    'document_type': 'blog',
                    'source_id': source_id,
                    'chunk_index': chunk_idx,
                    'total_chunks': len(chunks),
                    'appliance_type': blog.get('appliance_type', ''),
                    'title': blog.get('title', ''),
                    'url': blog.get('url', ''),
                    'author': blog.get('author', ''),
                    'meta_description': blog.get('meta_description', ''),
                    'excerpt': blog.get('excerpt', ''),
                    'content_length': blog.get('content_length', 0),
                    'topic_source': blog.get('topic_source', ''),
                    'topic': blog.get('topic', '')
                }

                # Create Document
                doc = Document(page_content=chunk_text, metadata=metadata)
                documents.append(doc)

    return documents


def process_repairs(text_splitter) -> List[Document]:
    """
    Process repair/parts documents with chunking.

    Returns:
        List of LangChain Document objects
    """
    documents = []

    for repair_file in REPAIR_FILES:
        print(f"Processing {repair_file.name}...")
        repairs = load_json_file(repair_file)

        for repair in repairs:
            # Extract content and chunk it
            content = repair.get('content', '')
            chunks = chunk_document(content, text_splitter)

            # Generate source ID for this repair guide
            source_id = str(uuid.uuid4())

            # Create Document for each chunk
            for chunk_idx, chunk_text in enumerate(chunks):
                # Create metadata (exclude content field since it's embedded)
                metadata = {
                    'document_type': 'repair',
                    'source_id': source_id,
                    'chunk_index': chunk_idx,
                    'total_chunks': len(chunks),
                    'appliance_type': repair.get('appliance_type', ''),
                    'category': repair.get('category', ''),
                    'title': repair.get('title', ''),
                    'part_name': repair.get('part_name', ''),
                    'content_length': repair.get('content_length', 0),
                    'symptom_url': repair.get('symptom_url', ''),
                    'part_url': repair.get('part_url', '')
                }

                # Create Document
                doc = Document(page_content=chunk_text, metadata=metadata)
                documents.append(doc)

    return documents


def process_policies(text_splitter) -> List[Document]:
    """
    Process policy documents with chunking from full_content.

    Returns:
        List of LangChain Document objects
    """
    documents = []

    print(f"Processing {POLICY_FILE.name}...")
    policies = load_json_file(POLICY_FILE)

    for policy in policies:
        # Extract full_content and chunk it
        full_content = policy.get('full_content', '')
        chunks = chunk_document(full_content, text_splitter)

        # Generate source ID for this policy
        source_id = str(uuid.uuid4())

        # Create Document for each chunk
        for chunk_idx, chunk_text in enumerate(chunks):
            # Create metadata
            # Exclude: paragraphs, full_content, ordered_list_items, scraped_at
            metadata = {
                'document_type': 'policy',
                'source_id': source_id,
                'chunk_index': chunk_idx,
                'total_chunks': len(chunks),
                'policy_type': policy.get('policy_type', ''),
                'url': policy.get('url', ''),
                'title': policy.get('title', ''),
                'meta_description': policy.get('meta_description', ''),
                'section_headings': str(policy.get('section_headings', [])),
                'unordered_list_items': str(policy.get('unordered_list_items', [])),
                'content_length': policy.get('content_length', 0)
            }

            # Create Document
            doc = Document(page_content=chunk_text, metadata=metadata)
            documents.append(doc)

    return documents


def create_vector_database():
    """Main function to create FAISS vector database."""
    print("=" * 80)
    print("CREATING PARTSELECT VECTOR DATABASE (FAISS)")
    print("=" * 80)
    print()

    # Initialize text splitter
    print("Initializing text splitter...")
    print(f"  Chunk size: {CHUNK_SIZE}")
    print(f"  Chunk overlap: {CHUNK_OVERLAP}")
    print(f"  Separators: {CHUNK_SEPARATORS}")
    print()

    text_splitter = create_text_splitter()

    # Process all documents
    print("Processing documents...")
    print()

    all_documents = []

    # Process blogs
    print("1. Processing blogs...")
    blog_docs = process_blogs(text_splitter)
    all_documents.extend(blog_docs)
    print(f"   ✓ Created {len(blog_docs)} blog chunks from {len(BLOG_FILES)} files")
    print()

    # Process repairs
    print("2. Processing repair guides...")
    repair_docs = process_repairs(text_splitter)
    all_documents.extend(repair_docs)
    print(f"   ✓ Created {len(repair_docs)} repair chunks from {len(REPAIR_FILES)} files")
    print()

    # Process policies
    print("3. Processing policies...")
    policy_docs = process_policies(text_splitter)
    all_documents.extend(policy_docs)
    print(f"   ✓ Created {len(policy_docs)} policy chunks from 1 file")
    print()

    # Summary
    print("=" * 80)
    print("DOCUMENT PROCESSING SUMMARY")
    print("=" * 80)
    print(f"Total chunks created: {len(all_documents)}")
    print(f"  - Blog chunks: {len(blog_docs)}")
    print(f"  - Repair chunks: {len(repair_docs)}")
    print(f"  - Policy chunks: {len(policy_docs)}")
    print()

    # Initialize embeddings model
    print("Initializing embeddings model...")
    print("  Using: sentence-transformers/all-MiniLM-L6-v2 (default)")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    print("  ✓ Embeddings model loaded")
    print()

    # Create FAISS vector store
    print("Creating FAISS vector store...")
    print(f"Database location: {VECTOR_DB_DIR}")
    print()

    # Create vector store from documents
    print("  Processing embeddings (this may take a few minutes)...")
    vector_store = FAISS.from_documents(all_documents, embeddings)
    print(f"  ✓ Created embeddings for {len(all_documents)} chunks")
    print()

    # Save vector store
    VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)
    vector_store.save_local(str(VECTOR_DB_DIR))
    print(f"  ✓ Saved vector store to {VECTOR_DB_DIR}")
    print()

    # Verify by testing a simple query
    print("Testing vector store with sample query...")
    test_results = vector_store.similarity_search("ice maker not working", k=3)
    print(f"  ✓ Test query returned {len(test_results)} results")
    if test_results:
        print(f"  Sample result: {test_results[0].metadata.get('title', 'N/A')[:60]}...")
    print()

    print("=" * 80)
    print("VECTOR DATABASE CREATION COMPLETE!")
    print("=" * 80)
    print(f"Total documents: {len(all_documents)}")
    print(f"Database path: {VECTOR_DB_DIR}")
    print()

    # Show sample metadata
    print("Sample document metadata:")
    if all_documents:
        print(json.dumps(all_documents[0].metadata, indent=2))
    print()

    print("✅ Vector database created successfully!")


if __name__ == "__main__":
    create_vector_database()
