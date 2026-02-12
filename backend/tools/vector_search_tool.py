"""
Vector Search Tool for semantic search over PartSelect knowledge base
Searches blogs, repair guides, and policies using FAISS vector database
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from langchain.tools import tool
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS


# Paths
SCRIPT_DIR = Path(__file__).parent
BACKEND_DIR = SCRIPT_DIR.parent
VECTOR_DB_DIR = BACKEND_DIR / "vectordb" / "faiss_index"


# Global cache for vector store (singleton pattern)
_vector_store_cache = None


# Tool description
TOOL_DESCRIPTION = """
Search the PartSelect knowledge base using semantic search. This tool performs natural language search over 366 documents including blog articles, repair guides, and company policies to find relevant information about appliance troubleshooting, repair instructions, and policies.

**Database Content:**
- 180 blog article chunks (dishwasher & refrigerator troubleshooting and repair advice)
- 178 repair guide chunks (part-specific repair instructions with symptoms)
- 8 policy chunks (returns, warranties, shipping, etc.)

**When to Use This Tool:**
- User asks troubleshooting questions (e.g., "Why is my ice maker not working?")
- User needs repair/how-to instructions (e.g., "How do I replace a door seal?")
- User asks about company policies (e.g., "What's your return policy?")
- User needs general appliance maintenance advice
- User describes symptoms and needs solutions

**When NOT to Use This Tool (use SQL tool instead):**
- User needs specific part details (price, part number, availability)
- User wants to browse parts by category
- User asks about model compatibility
- User needs exact product specifications

**Search Behavior:**
- Uses semantic/similarity search (finds conceptually similar content, not just keyword matches)
- Returns most relevant chunks ranked by similarity
- Can filter by document type (blog, repair, policy) or appliance type (refrigerator, dishwasher)
- Content is chunked (1000 chars with 200 char overlap), so related info may span multiple results

**Best Practices:**
- Use natural, conversational queries (e.g., "refrigerator is leaking water" not "leak refrigerator")
- Be specific to get better results (e.g., "ice maker not making ice" vs "ice maker problem")
- Use filters when you know the document or appliance type to narrow results
- Request k=5-10 for most queries (higher for exploratory, lower for specific questions)
- Check multiple results as similar information may appear in different documents

**Examples:**

| User Query | Tool Input | Rationale |
|------------|-----------|-----------|
| "My ice maker stopped working" | query="ice maker not working", k=5 | General troubleshooting query |
| "How do I replace a dishwasher door seal?" | query="replace door seal", appliance_type="dishwasher", k=5 | Specific repair instruction |
| "What's your return policy?" | query="return policy", document_type="policy", k=3 | Policy question |
| "Refrigerator is making noise" | query="refrigerator making noise", document_type="blog", k=7 | Troubleshooting from blogs |
| "Dishwasher won't drain water" | query="dishwasher not draining water", k=5 | Symptom-based search |
"""


class VectorSearchInput(BaseModel):
    """Input schema for vector search tool."""

    query: str = Field(
        description=(
            "Natural language search query. Use conversational language describing the problem, "
            "question, or topic. Examples: 'ice maker not working', 'how to replace door seal', "
            "'return policy'. Be specific for better results. Min 3 characters, max 500 characters."
        )
    )

    k: int = Field(
        default=5,
        description=(
            "Number of results to return. Range: 1-20. Default: 5. "
            "Use 3-5 for specific questions, 7-10 for exploratory searches, 15-20 for comprehensive research."
        )
    )

    document_type: str = Field(
        default="all",
        description=(
            "Filter results by document type. Options: 'all' (no filter), 'blog' (troubleshooting articles), "
            "'repair' (part-specific repair guides), 'policy' (company policies like returns/warranties). "
            "Default: 'all'. Use filters when you know what type of information you need."
        )
    )

    appliance_type: str = Field(
        default="all",
        description=(
            "Filter results by appliance type. Options: 'all' (no filter), 'refrigerator', 'dishwasher'. "
            "Default: 'all'. Use when the query is specific to one appliance type."
        )
    )

    include_score: bool = Field(
        default=False,
        description=(
            "Include relevance score in results (lower score = more relevant). "
            "Default: False. Set to True for debugging or to assess result quality."
        )
    )

    @field_validator('query')
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Validate query parameter."""
        if not v or not isinstance(v, str):
            raise ValueError("query must be a non-empty string")

        v = v.strip()
        if len(v) < 3:
            raise ValueError("query must be at least 3 characters long")
        if len(v) > 500:
            raise ValueError("query exceeds maximum length of 500 characters")

        return v

    @field_validator('k')
    @classmethod
    def validate_k(cls, v: int) -> int:
        """Validate k parameter."""
        if not isinstance(v, int) or v < 1 or v > 20:
            raise ValueError("k must be an integer between 1 and 20")
        return v

    @field_validator('document_type')
    @classmethod
    def validate_document_type(cls, v: str) -> str:
        """Validate document_type parameter."""
        valid_types = ["all", "blog", "repair", "policy"]
        v_lower = v.lower()
        if v_lower not in valid_types:
            raise ValueError(f"document_type must be one of: {', '.join(valid_types)}")
        return v_lower

    @field_validator('appliance_type')
    @classmethod
    def validate_appliance_type(cls, v: str) -> str:
        """Validate appliance_type parameter."""
        valid_types = ["all", "refrigerator", "dishwasher"]
        v_lower = v.lower()
        if v_lower not in valid_types:
            raise ValueError(f"appliance_type must be one of: {', '.join(valid_types)}")
        return v_lower


def get_vector_store() -> FAISS:
    """
    Load vector store with singleton pattern.
    Loads once and caches for subsequent calls.

    Returns:
        FAISS vector store instance

    Raises:
        Exception: If vector store cannot be loaded
    """
    global _vector_store_cache

    if _vector_store_cache is None:
        try:
            # Initialize embeddings model
            embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )

            # Load FAISS index
            _vector_store_cache = FAISS.load_local(
                str(VECTOR_DB_DIR),
                embeddings,
                allow_dangerous_deserialization=True
            )
        except Exception as e:
            raise Exception(f"Failed to load vector database: {str(e)}")

    return _vector_store_cache


def apply_filters(
    results: List[tuple],
    document_type: str,
    appliance_type: str
) -> List[tuple]:
    """
    Apply document_type and appliance_type filters to search results.

    Args:
        results: List of (Document, score) tuples
        document_type: Filter by document type
        appliance_type: Filter by appliance type

    Returns:
        Filtered list of results
    """
    filtered = []

    for result in results:
        # Results are always (doc, score) tuples
        doc = result[0]

        # Filter by document_type
        if document_type != "all":
            if doc.metadata.get("document_type") != document_type:
                continue

        # Filter by appliance_type (skip if policy, which doesn't have appliance_type)
        if appliance_type != "all":
            doc_appliance = doc.metadata.get("appliance_type")
            if doc_appliance and doc_appliance != appliance_type:
                continue

        filtered.append(result)

    return filtered


def format_result(doc: Any, rank: int, score: Optional[float] = None) -> Dict[str, Any]:
    """
    Format a single search result into structured dictionary.

    Args:
        doc: Document object
        rank: Result rank (1-indexed)
        score: Optional relevance score

    Returns:
        Formatted result dictionary
    """
    result_dict = {
        "rank": rank,
        "content": doc.page_content,
        "document_type": doc.metadata.get("document_type"),
        "appliance_type": doc.metadata.get("appliance_type"),
        "chunk_index": doc.metadata.get("chunk_index", 0),
        "total_chunks": doc.metadata.get("total_chunks", 1),
    }

    # Add type-specific metadata
    doc_type = doc.metadata.get("document_type")

    if doc_type == "blog":
        result_dict.update({
            "title": doc.metadata.get("title"),
            "url": doc.metadata.get("url"),
            "author": doc.metadata.get("author"),
            "excerpt": doc.metadata.get("excerpt"),
        })

    elif doc_type == "repair":
        result_dict.update({
            "part_name": doc.metadata.get("part_name"),
            "category": doc.metadata.get("category"),
            "part_url": doc.metadata.get("part_url"),
            "symptom_url": doc.metadata.get("symptom_url"),
        })

    elif doc_type == "policy":
        result_dict.update({
            "policy_type": doc.metadata.get("policy_type"),
            "title": doc.metadata.get("title"),
            "url": doc.metadata.get("url"),
        })

    # Add score if included
    if score is not None:
        result_dict["relevance_score"] = float(score)

    return result_dict


@tool(args_schema=VectorSearchInput)
def vector_search_tool(
    query: str,
    k: int = 5,
    document_type: str = "all",
    appliance_type: str = "all",
    include_score: bool = False
) -> List[Dict[str, Any]]:
    """
    Search PartSelect knowledge base using semantic vector search.

    Performs similarity search over 366 document chunks including blogs, repair guides,
    and policies to find relevant information for appliance troubleshooting and repair.

    Args:
        query: Natural language search query
        k: Number of results to return (1-20, default 5)
        document_type: Filter by document type - "all", "blog", "repair", or "policy"
        appliance_type: Filter by appliance - "all", "refrigerator", or "dishwasher"
        include_score: Include relevance score in results (default False)

    Returns:
        List of search results with content and metadata

    Example:
        >>> vector_search_tool(query="ice maker not working", k=3)
        [
            {
                "rank": 1,
                "content": "Disconnect your appliance from both the power source...",
                "document_type": "repair",
                "appliance_type": "refrigerator",
                "part_name": "Ice Maker Assembly",
                ...
            }
        ]
    """
    try:
        # Load vector store
        vector_store = get_vector_store()

        # Perform search (get more results than needed for filtering)
        search_k = min(k * 3, 50)  # Get 3x results for filtering, max 50

        if include_score:
            results = vector_store.similarity_search_with_score(query, k=search_k)
        else:
            results = vector_store.similarity_search(query, k=search_k)
            # Convert to tuple format for consistent handling
            results = [(doc, None) for doc in results]

        # Apply filters
        filtered_results = apply_filters(results, document_type, appliance_type)

        # Limit to requested k
        filtered_results = filtered_results[:k]

        # Format results
        formatted_results = []
        for i, result in enumerate(filtered_results, 1):
            doc = result[0]
            score = result[1] if include_score else None
            formatted_results.append(format_result(doc, i, score))

        return formatted_results

    except ValueError as e:
        # Validation error
        return [{"error": str(e), "error_type": "ValidationError", "query": query}]

    except Exception as e:
        # Unexpected error
        error_msg = str(e)
        if "vector database" in error_msg.lower():
            error_type = "VectorStoreError"
        else:
            error_type = "SearchError"

        return [{
            "error": f"Search failed: {error_msg}",
            "error_type": error_type,
            "query": query
        }]


# Update tool description
vector_search_tool.description = TOOL_DESCRIPTION
