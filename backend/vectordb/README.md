# Vector Database Setup

## Overview
FAISS-based vector database for semantic search over PartSelect content (blogs, repair guides, and policies).

## Database Stats
- **Total documents**: 366 chunks
- **Blog chunks**: 180 (dishwasher & refrigerator articles)
- **Repair chunks**: 178 (part-specific repair guides)
- **Policy chunks**: 8 (returns, warranties, etc.)
- **Embedding model**: sentence-transformers/all-MiniLM-L6-v2

## Files
- `create_vectordb.py` - Creates FAISS index from scraped data
- `test_vectordb.py` - Comprehensive test suite
- `faiss_index/` - Generated FAISS database (366 documents)

## Usage

### Create/Recreate Database
```bash
python create_vectordb.py
```

### Run Tests
```bash
python test_vectordb.py
```

### Use in Code
```python
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# Load database
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)
vector_store = FAISS.load_local(
    "faiss_index",
    embeddings,
    allow_dangerous_deserialization=True
)

# Search
results = vector_store.similarity_search("ice maker not working", k=3)
for doc in results:
    print(doc.page_content)
    print(doc.metadata)
```

## Data Sources
Located in `../../scraping/data/processed/`:
- `dishwasher_blogs.json`
- `refrigerator_blogs.json`
- `dishwasher_parts.json`
- `refrigerator_parts.json`
- `policies.json`

## Configuration
- **Chunk size**: 1000 characters
- **Chunk overlap**: 200 characters
- **Separators**: `\n\n`, `\n`, ` `

## Test Results
All tests passing ✅
- Similarity search
- Metadata integrity
- Chunking integrity
- Edge cases
- Retriever interface
