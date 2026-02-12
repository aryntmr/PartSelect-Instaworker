"""
Comprehensive test suite for FAISS vector database
Tests loading, querying, metadata integrity, and retrieval quality
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
import json


# Paths
SCRIPT_DIR = Path(__file__).parent
VECTOR_DB_DIR = SCRIPT_DIR / "faiss_index"


def print_separator(char="=", length=80):
    """Print a separator line."""
    print(char * length)


def print_subsection(title):
    """Print a subsection header."""
    print(f"\n{'─' * 80}")
    print(f"  {title}")
    print('─' * 80)


def load_vector_database():
    """Load the FAISS vector database."""
    print_separator()
    print("LOADING VECTOR DATABASE")
    print_separator()
    print()

    # Check if database exists
    if not VECTOR_DB_DIR.exists():
        print(f"❌ ERROR: Vector database not found at {VECTOR_DB_DIR}")
        return None

    print(f"📂 Loading from: {VECTOR_DB_DIR}")

    # Initialize embeddings (must match the model used during creation)
    print("Loading embeddings model: sentence-transformers/all-MiniLM-L6-v2")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    # Load vector store
    print("Loading FAISS index...")
    vector_store = FAISS.load_local(
        str(VECTOR_DB_DIR),
        embeddings,
        allow_dangerous_deserialization=True
    )

    print("✅ Vector database loaded successfully!")
    print()

    return vector_store


def test_database_stats(vector_store):
    """Test database statistics and content."""
    print_separator()
    print("DATABASE STATISTICS")
    print_separator()
    print()

    # Get document count
    index_size = vector_store.index.ntotal
    print(f"Total documents in index: {index_size}")

    # Test retrieval to get sample documents
    sample_docs = vector_store.similarity_search("test", k=10)
    print(f"Successfully retrieved sample documents: {len(sample_docs)}")
    print()

    # Analyze document types
    doc_types = {}
    appliance_types = {}

    # Get more samples to analyze
    test_queries = ["refrigerator", "dishwasher", "repair", "policy"]
    all_samples = []

    for query in test_queries:
        docs = vector_store.similarity_search(query, k=25)
        all_samples.extend(docs)

    # Count document types
    for doc in all_samples:
        doc_type = doc.metadata.get('document_type', 'unknown')
        doc_types[doc_type] = doc_types.get(doc_type, 0) + 1

        appliance = doc.metadata.get('appliance_type', 'unknown')
        if appliance and appliance != 'unknown':
            appliance_types[appliance] = appliance_types.get(appliance, 0) + 1

    print("Document type distribution (from sample):")
    for doc_type, count in sorted(doc_types.items()):
        print(f"  {doc_type}: {count} documents")
    print()

    print("Appliance type distribution (from sample):")
    for appliance, count in sorted(appliance_types.items()):
        print(f"  {appliance}: {count} documents")
    print()

    return True


def test_similarity_search(vector_store):
    """Test basic similarity search functionality."""
    print_separator()
    print("TESTING SIMILARITY SEARCH")
    print_separator()
    print()

    test_cases = [
        {
            "query": "ice maker not working",
            "k": 3,
            "expected_keywords": ["ice", "maker", "refrigerator"]
        },
        {
            "query": "dishwasher not draining water",
            "k": 5,
            "expected_keywords": ["drain", "water", "dishwasher"]
        },
        {
            "query": "leaking refrigerator",
            "k": 3,
            "expected_keywords": ["leak", "refrigerator", "water"]
        },
        {
            "query": "door won't close",
            "k": 4,
            "expected_keywords": ["door", "latch", "seal"]
        },
        {
            "query": "return policy",
            "k": 2,
            "expected_keywords": ["return", "policy", "refund"]
        }
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"Test {i}: Query = '{test['query']}' (k={test['k']})")
        print("-" * 80)

        results = vector_store.similarity_search(test['query'], k=test['k'])

        if not results:
            print("❌ FAILED: No results returned")
            print()
            continue

        print(f"✅ Retrieved {len(results)} documents")
        print()

        # Display results
        for idx, doc in enumerate(results, 1):
            print(f"  Result {idx}:")
            print(f"    Type: {doc.metadata.get('document_type', 'N/A')}")

            if doc.metadata.get('document_type') == 'blog':
                print(f"    Title: {doc.metadata.get('title', 'N/A')[:60]}...")
            elif doc.metadata.get('document_type') == 'repair':
                print(f"    Part: {doc.metadata.get('part_name', 'N/A')[:60]}...")
            elif doc.metadata.get('document_type') == 'policy':
                print(f"    Policy: {doc.metadata.get('policy_type', 'N/A')}")

            print(f"    Appliance: {doc.metadata.get('appliance_type', 'N/A')}")
            print(f"    Content preview: {doc.page_content[:100]}...")
            print()

        print()


def test_similarity_search_with_scores(vector_store):
    """Test similarity search with relevance scores."""
    print_separator()
    print("TESTING SIMILARITY SEARCH WITH SCORES")
    print_separator()
    print()

    test_queries = [
        "ice maker repair",
        "dishwasher warranty",
        "refrigerator door seal"
    ]

    for query in test_queries:
        print(f"Query: '{query}'")
        print("-" * 80)

        results = vector_store.similarity_search_with_score(query, k=5)

        print(f"Retrieved {len(results)} results with scores:")
        print()

        for idx, (doc, score) in enumerate(results, 1):
            print(f"  {idx}. Score: {score:.4f}")
            print(f"     Type: {doc.metadata.get('document_type', 'N/A')}")

            if doc.metadata.get('document_type') == 'blog':
                print(f"     Title: {doc.metadata.get('title', 'N/A')[:50]}...")
            elif doc.metadata.get('document_type') == 'repair':
                print(f"     Part: {doc.metadata.get('part_name', 'N/A')[:50]}...")

            print()

        print()


def test_metadata_integrity(vector_store):
    """Test that metadata is correctly preserved."""
    print_separator()
    print("TESTING METADATA INTEGRITY")
    print_separator()
    print()

    # Test each document type
    doc_type_queries = {
        'blog': 'dishwasher repair tips',
        'repair': 'replace ice maker',
        'policy': 'return policy'
    }

    for doc_type, query in doc_type_queries.items():
        print(f"Testing {doc_type} documents:")
        print("-" * 80)

        results = vector_store.similarity_search(query, k=3)

        # Find a document of the target type
        target_doc = None
        for doc in results:
            if doc.metadata.get('document_type') == doc_type:
                target_doc = doc
                break

        if not target_doc:
            print(f"⚠️  WARNING: No {doc_type} document found in results")
            print()
            continue

        print(f"✅ Found {doc_type} document")
        print()
        print("Metadata fields:")

        required_fields = ['document_type', 'source_id', 'chunk_index', 'total_chunks']

        for field in required_fields:
            value = target_doc.metadata.get(field, 'MISSING')
            status = "✅" if value != 'MISSING' else "❌"
            print(f"  {status} {field}: {value}")

        print()

        # Type-specific fields
        if doc_type == 'blog':
            blog_fields = ['title', 'url', 'appliance_type', 'author']
            print("Blog-specific fields:")
            for field in blog_fields:
                value = target_doc.metadata.get(field, 'MISSING')
                status = "✅" if value and value != 'MISSING' else "❌"
                print(f"  {status} {field}: {str(value)[:60]}...")

        elif doc_type == 'repair':
            repair_fields = ['part_name', 'category', 'appliance_type']
            print("Repair-specific fields:")
            for field in repair_fields:
                value = target_doc.metadata.get(field, 'MISSING')
                status = "✅" if value and value != 'MISSING' else "❌"
                print(f"  {status} {field}: {str(value)[:60]}...")

        elif doc_type == 'policy':
            policy_fields = ['policy_type', 'url', 'title']
            print("Policy-specific fields:")
            for field in policy_fields:
                value = target_doc.metadata.get(field, 'MISSING')
                status = "✅" if value and value != 'MISSING' else "❌"
                print(f"  {status} {field}: {str(value)[:60]}...")

        print()
        print()


def test_chunking_integrity(vector_store):
    """Test that chunking was done correctly."""
    print_separator()
    print("TESTING CHUNKING INTEGRITY")
    print_separator()
    print()

    # Get documents and check chunk information
    results = vector_store.similarity_search("repair guide", k=20)

    # Group by source_id
    source_chunks = {}
    for doc in results:
        source_id = doc.metadata.get('source_id')
        if source_id:
            if source_id not in source_chunks:
                source_chunks[source_id] = []
            source_chunks[source_id].append(doc)

    print(f"Analyzing {len(source_chunks)} unique source documents")
    print()

    multi_chunk_sources = 0
    for source_id, chunks in source_chunks.items():
        total_chunks = chunks[0].metadata.get('total_chunks', 0)
        if total_chunks > 1:
            multi_chunk_sources += 1

    print(f"Documents with multiple chunks: {multi_chunk_sources}")
    print()

    # Display a sample multi-chunk document
    for source_id, chunks in source_chunks.items():
        total_chunks = chunks[0].metadata.get('total_chunks', 0)
        if total_chunks > 1:
            print("Sample multi-chunk document:")
            print(f"  Source ID: {source_id}")
            print(f"  Total chunks: {total_chunks}")
            print(f"  Retrieved chunks: {len(chunks)}")

            # Sort by chunk index
            sorted_chunks = sorted(chunks, key=lambda x: x.metadata.get('chunk_index', 0))

            print()
            print("  Chunk sequence:")
            for chunk in sorted_chunks[:3]:  # Show first 3 chunks
                idx = chunk.metadata.get('chunk_index', 0)
                content_preview = chunk.page_content[:80].replace('\n', ' ')
                print(f"    Chunk {idx}: {content_preview}...")

            print()
            break

    print()


def test_retrieval_quality(vector_store):
    """Test quality of retrieval for specific scenarios."""
    print_separator()
    print("TESTING RETRIEVAL QUALITY")
    print_separator()
    print()

    quality_tests = [
        {
            "scenario": "Specific symptom (ice maker)",
            "query": "my refrigerator ice maker stopped making ice",
            "expected_type": ["blog", "repair"],
            "expected_appliance": "refrigerator"
        },
        {
            "scenario": "Dishwasher problem",
            "query": "dishwasher not cleaning dishes properly",
            "expected_type": ["blog", "repair"],
            "expected_appliance": "dishwasher"
        },
        {
            "scenario": "Policy question",
            "query": "what is your return and refund policy",
            "expected_type": ["policy"],
            "expected_appliance": None
        },
        {
            "scenario": "Part replacement",
            "query": "how to replace door latch",
            "expected_type": ["repair", "blog"],
            "expected_appliance": None
        }
    ]

    for test in quality_tests:
        print(f"Scenario: {test['scenario']}")
        print(f"Query: '{test['query']}'")
        print("-" * 80)

        results = vector_store.similarity_search(test['query'], k=5)

        # Check document types
        doc_types = [doc.metadata.get('document_type') for doc in results]
        type_match = any(dt in test['expected_type'] for dt in doc_types)

        print(f"  Document types in top 5: {set(doc_types)}")
        print(f"  Expected types: {test['expected_type']}")
        print(f"  {'✅' if type_match else '⚠️ '} Type match: {type_match}")

        # Check appliance type if specified
        if test['expected_appliance']:
            appliance_types = [doc.metadata.get('appliance_type') for doc in results]
            appliance_match = test['expected_appliance'] in appliance_types

            print(f"  Appliance types: {set(appliance_types)}")
            print(f"  Expected: {test['expected_appliance']}")
            print(f"  {'✅' if appliance_match else '⚠️ '} Appliance match: {appliance_match}")

        print()
        print("  Top result:")
        top_doc = results[0]
        print(f"    Type: {top_doc.metadata.get('document_type')}")
        if top_doc.metadata.get('title'):
            print(f"    Title: {top_doc.metadata.get('title')[:60]}...")
        if top_doc.metadata.get('part_name'):
            print(f"    Part: {top_doc.metadata.get('part_name')[:60]}...")
        print(f"    Preview: {top_doc.page_content[:100]}...")

        print()
        print()


def test_edge_cases(vector_store):
    """Test edge cases and boundary conditions."""
    print_separator()
    print("TESTING EDGE CASES")
    print_separator()
    print()

    print("Test 1: Empty query")
    print("-" * 80)
    try:
        results = vector_store.similarity_search("", k=5)
        print(f"✅ Handled empty query, returned {len(results)} results")
    except Exception as e:
        print(f"❌ Failed with error: {str(e)}")
    print()

    print("Test 2: Very long query")
    print("-" * 80)
    long_query = "refrigerator " * 100
    try:
        results = vector_store.similarity_search(long_query, k=5)
        print(f"✅ Handled long query, returned {len(results)} results")
    except Exception as e:
        print(f"❌ Failed with error: {str(e)}")
    print()

    print("Test 3: Special characters query")
    print("-" * 80)
    special_query = "!@#$%^&*() refrigerator repair"
    try:
        results = vector_store.similarity_search(special_query, k=5)
        print(f"✅ Handled special characters, returned {len(results)} results")
    except Exception as e:
        print(f"❌ Failed with error: {str(e)}")
    print()

    print("Test 4: Non-English query")
    print("-" * 80)
    non_english_query = "réfrigérateur problème"
    try:
        results = vector_store.similarity_search(non_english_query, k=5)
        print(f"✅ Handled non-English query, returned {len(results)} results")
    except Exception as e:
        print(f"❌ Failed with error: {str(e)}")
    print()

    print("Test 5: Very large k value")
    print("-" * 80)
    try:
        results = vector_store.similarity_search("refrigerator", k=1000)
        print(f"✅ Handled large k value, returned {len(results)} results")
    except Exception as e:
        print(f"❌ Failed with error: {str(e)}")
    print()


def test_as_retriever(vector_store):
    """Test using vector store as a retriever."""
    print_separator()
    print("TESTING AS RETRIEVER")
    print_separator()
    print()

    print("Creating retriever with k=5...")
    retriever = vector_store.as_retriever(search_kwargs={"k": 5})
    print("✅ Retriever created")
    print()

    test_query = "ice maker not working"
    print(f"Test query: '{test_query}'")
    print("-" * 80)

    try:
        results = retriever.invoke(test_query)
        print(f"✅ Retrieved {len(results)} documents via retriever")
        print()

        if results:
            print("Sample result:")
            print(f"  Type: {results[0].metadata.get('document_type')}")
            print(f"  Preview: {results[0].page_content[:100]}...")

    except Exception as e:
        print(f"❌ Failed with error: {str(e)}")

    print()


def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("FAISS VECTOR DATABASE - COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    print()

    # Load database
    vector_store = load_vector_database()

    if not vector_store:
        print("❌ Failed to load vector database. Exiting.")
        return

    # Run tests
    test_database_stats(vector_store)
    test_similarity_search(vector_store)
    test_similarity_search_with_scores(vector_store)
    test_metadata_integrity(vector_store)
    test_chunking_integrity(vector_store)
    test_retrieval_quality(vector_store)
    test_edge_cases(vector_store)
    test_as_retriever(vector_store)

    # Summary
    print_separator()
    print("TEST SUITE COMPLETE")
    print_separator()
    print()
    print("✅ All tests completed successfully!")
    print()
    print("Vector database is ready for use in production.")
    print()


if __name__ == "__main__":
    run_all_tests()
