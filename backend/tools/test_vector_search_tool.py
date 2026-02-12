"""
Comprehensive test suite for vector search tool
Tests validation, search functionality, filtering, and error handling
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.vector_search_tool import vector_search_tool


def print_separator(char="=", length=80):
    """Print a separator line."""
    print(char * length)


def print_subsection(title):
    """Print a subsection header."""
    print(f"\n{'─' * 80}")
    print(f"  {title}")
    print('─' * 80)


def test_basic_queries():
    """Test basic search queries without filters."""
    print_separator()
    print("TESTING BASIC QUERIES")
    print_separator()
    print()

    test_cases = [
        {
            "name": "Ice maker issue",
            "query": "ice maker not working",
            "k": 3
        },
        {
            "name": "Dishwasher draining",
            "query": "dishwasher not draining water",
            "k": 3
        },
        {
            "name": "Return policy",
            "query": "what is your return policy",
            "k": 2
        },
        {
            "name": "Door seal replacement",
            "query": "how to replace refrigerator door seal",
            "k": 3
        }
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"Test {i}: {test['name']}")
        print(f"Query: '{test['query']}' (k={test['k']})")
        print("-" * 80)

        result = vector_search_tool.invoke({
            "query": test['query'],
            "k": test['k']
        })

        if isinstance(result, list) and result and "error" in result[0]:
            print(f"❌ FAILED: {result[0]['error']}")
        else:
            print(f"✅ Retrieved {len(result)} results")

            # Show first result
            if result:
                first = result[0]
                print(f"\nTop Result:")
                print(f"  Rank: {first.get('rank')}")
                print(f"  Type: {first.get('document_type')}")
                print(f"  Appliance: {first.get('appliance_type')}")

                if first.get('title'):
                    print(f"  Title: {first.get('title')[:60]}...")
                if first.get('part_name'):
                    print(f"  Part: {first.get('part_name')[:60]}...")
                if first.get('policy_type'):
                    print(f"  Policy: {first.get('policy_type')}")

                print(f"  Content: {first.get('content')[:100]}...")

        print()


def test_with_filters():
    """Test queries with document and appliance type filters."""
    print_separator()
    print("TESTING WITH FILTERS")
    print_separator()
    print()

    test_cases = [
        {
            "name": "Blog articles only",
            "query": "ice maker problems",
            "document_type": "blog",
            "k": 3
        },
        {
            "name": "Repair guides only",
            "query": "door seal",
            "document_type": "repair",
            "k": 3
        },
        {
            "name": "Policies only",
            "query": "return",
            "document_type": "policy",
            "k": 2
        },
        {
            "name": "Refrigerator content only",
            "query": "leaking",
            "appliance_type": "refrigerator",
            "k": 3
        },
        {
            "name": "Dishwasher content only",
            "query": "not cleaning",
            "appliance_type": "dishwasher",
            "k": 3
        },
        {
            "name": "Combined filters",
            "query": "not working",
            "document_type": "repair",
            "appliance_type": "dishwasher",
            "k": 3
        }
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"Test {i}: {test['name']}")
        print(f"Query: '{test['query']}' (k={test['k']})")

        filters = []
        if test.get('document_type'):
            filters.append(f"document_type={test['document_type']}")
        if test.get('appliance_type'):
            filters.append(f"appliance_type={test['appliance_type']}")

        if filters:
            print(f"Filters: {', '.join(filters)}")

        print("-" * 80)

        result = vector_search_tool.invoke({
            "query": test['query'],
            "k": test['k'],
            "document_type": test.get('document_type', 'all'),
            "appliance_type": test.get('appliance_type', 'all')
        })

        if isinstance(result, list) and result and "error" in result[0]:
            print(f"❌ FAILED: {result[0]['error']}")
        else:
            print(f"✅ Retrieved {len(result)} results")

            # Verify filters worked
            if result:
                doc_types = set(r.get('document_type') for r in result)
                appliance_types = set(r.get('appliance_type') for r in result if r.get('appliance_type'))

                print(f"  Document types: {doc_types}")
                if appliance_types:
                    print(f"  Appliance types: {appliance_types}")

                # Check filter correctness
                if test.get('document_type') and test['document_type'] != 'all':
                    if len(doc_types) == 1 and test['document_type'] in doc_types:
                        print(f"  ✅ Document type filter working correctly")
                    else:
                        print(f"  ⚠️  Document type filter may not be working")

                if test.get('appliance_type') and test['appliance_type'] != 'all':
                    if appliance_types and test['appliance_type'] in appliance_types:
                        print(f"  ✅ Appliance type filter working correctly")

        print()


def test_with_scores():
    """Test queries with relevance scores."""
    print_separator()
    print("TESTING WITH RELEVANCE SCORES")
    print_separator()
    print()

    queries = [
        "ice maker repair",
        "dishwasher door seal",
        "warranty policy"
    ]

    for query in queries:
        print(f"Query: '{query}'")
        print("-" * 80)

        result = vector_search_tool.invoke({
            "query": query,
            "k": 3,
            "include_score": True
        })

        if isinstance(result, list) and result and "error" in result[0]:
            print(f"❌ FAILED: {result[0]['error']}")
        else:
            print(f"✅ Retrieved {len(result)} results with scores")

            for r in result:
                score = r.get('relevance_score', 'N/A')
                doc_type = r.get('document_type')
                title = r.get('title', r.get('part_name', r.get('policy_type', 'N/A')))

                score_str = f"{score:.4f}" if isinstance(score, float) else str(score)
                print(f"  Rank {r.get('rank')}: Score={score_str}, Type={doc_type}, Title={str(title)[:50]}...")

        print()


def test_different_k_values():
    """Test with different k values."""
    print_separator()
    print("TESTING DIFFERENT K VALUES")
    print_separator()
    print()

    query = "refrigerator repair"
    k_values = [1, 5, 10, 20]

    for k in k_values:
        print(f"Test: k={k}")
        print("-" * 80)

        result = vector_search_tool.invoke({
            "query": query,
            "k": k
        })

        if isinstance(result, list) and result and "error" in result[0]:
            print(f"❌ FAILED: {result[0]['error']}")
        else:
            print(f"✅ Retrieved {len(result)} results (requested: {k})")

            if len(result) != k:
                print(f"  ⚠️  Warning: Expected {k} results, got {len(result)}")

        print()


def test_input_validation():
    """Test input validation."""
    print_separator()
    print("TESTING INPUT VALIDATION")
    print_separator()
    print()

    test_cases = [
        {
            "name": "Empty query",
            "input": {"query": "", "k": 5},
            "should_fail": True
        },
        {
            "name": "Very short query",
            "input": {"query": "ab", "k": 5},
            "should_fail": True
        },
        {
            "name": "Very long query",
            "input": {"query": "a" * 501, "k": 5},
            "should_fail": True
        },
        {
            "name": "Invalid k (too small)",
            "input": {"query": "test", "k": 0},
            "should_fail": True
        },
        {
            "name": "Invalid k (too large)",
            "input": {"query": "test", "k": 21},
            "should_fail": True
        },
        {
            "name": "Invalid document_type",
            "input": {"query": "test", "k": 5, "document_type": "invalid"},
            "should_fail": True
        },
        {
            "name": "Invalid appliance_type",
            "input": {"query": "test", "k": 5, "appliance_type": "invalid"},
            "should_fail": True
        },
        {
            "name": "Valid minimal query",
            "input": {"query": "abc", "k": 5},
            "should_fail": False
        }
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"Test {i}: {test['name']}")
        print(f"Input: {test['input']}")
        print("-" * 80)

        try:
            result = vector_search_tool.invoke(test['input'])
            has_error = isinstance(result, list) and result and "error" in result[0]
            error_msg = result[0]['error'] if has_error else None
        except Exception as e:
            # Pydantic validation errors
            has_error = True
            error_msg = str(e)

        if test['should_fail']:
            if has_error:
                print(f"✅ PASSED: Correctly rejected with error: {error_msg[:80]}...")
            else:
                print(f"❌ FAILED: Should have been rejected but was accepted")
        else:
            if has_error:
                print(f"❌ FAILED: Should have been accepted but was rejected: {error_msg[:80]}...")
            else:
                print(f"✅ PASSED: Correctly accepted, returned {len(result)} results")

        print()


def test_edge_cases():
    """Test edge cases."""
    print_separator()
    print("TESTING EDGE CASES")
    print_separator()
    print()

    test_cases = [
        {
            "name": "Query with special characters",
            "query": "!@#$%^&*() refrigerator",
            "k": 3
        },
        {
            "name": "Query with numbers",
            "query": "error code E15",
            "k": 3
        },
        {
            "name": "Very specific query",
            "query": "Bosch dishwasher model SHE3AR75UC/21 ice maker assembly replacement",
            "k": 3
        },
        {
            "name": "Single word query",
            "query": "leak",
            "k": 3
        },
        {
            "name": "Question format",
            "query": "Why is my refrigerator not cooling?",
            "k": 3
        }
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"Test {i}: {test['name']}")
        print(f"Query: '{test['query']}'")
        print("-" * 80)

        result = vector_search_tool.invoke({
            "query": test['query'],
            "k": test['k']
        })

        if isinstance(result, list) and result and "error" in result[0]:
            print(f"❌ FAILED: {result[0]['error']}")
        else:
            print(f"✅ Retrieved {len(result)} results")

        print()


def test_result_structure():
    """Test that result structure is correct."""
    print_separator()
    print("TESTING RESULT STRUCTURE")
    print_separator()
    print()

    print("Test: Verify result structure")
    print("-" * 80)

    result = vector_search_tool.invoke({
        "query": "ice maker",
        "k": 1,
        "include_score": True
    })

    if isinstance(result, list) and result and "error" in result[0]:
        print(f"❌ FAILED: {result[0]['error']}")
    else:
        print(f"✅ Retrieved {len(result)} result(s)")

        if result:
            first = result[0]

            # Check required fields
            required_fields = ["rank", "content", "document_type", "appliance_type",
                             "chunk_index", "total_chunks"]

            print("\nChecking required fields:")
            for field in required_fields:
                if field in first:
                    print(f"  ✅ {field}: {type(first[field]).__name__}")
                else:
                    print(f"  ❌ {field}: MISSING")

            # Check score (should be present with include_score=True)
            if "relevance_score" in first:
                print(f"  ✅ relevance_score: {first['relevance_score']}")
            else:
                print(f"  ❌ relevance_score: MISSING (include_score=True)")

            # Check type-specific fields
            doc_type = first.get('document_type')
            print(f"\nChecking {doc_type}-specific fields:")

            if doc_type == "blog":
                type_fields = ["title", "url", "author"]
            elif doc_type == "repair":
                type_fields = ["part_name", "category"]
            elif doc_type == "policy":
                type_fields = ["policy_type", "title", "url"]
            else:
                type_fields = []

            for field in type_fields:
                if field in first:
                    print(f"  ✅ {field}: present")
                else:
                    print(f"  ⚠️  {field}: not present")

    print()


def test_real_world_queries():
    """Test with real-world user queries."""
    print_separator()
    print("TESTING REAL-WORLD QUERIES")
    print_separator()
    print()

    queries = [
        "My refrigerator ice maker stopped making ice",
        "Dishwasher leaves spots on dishes",
        "How long does shipping take?",
        "Replace broken door handle",
        "Water leaking from bottom of refrigerator"
    ]

    for i, query in enumerate(queries, 1):
        print(f"Test {i}: '{query}'")
        print("-" * 80)

        result = vector_search_tool.invoke({
            "query": query,
            "k": 3
        })

        if isinstance(result, list) and result and "error" in result[0]:
            print(f"❌ FAILED: {result[0]['error']}")
        else:
            print(f"✅ Retrieved {len(result)} results")

            # Show document types
            if result:
                doc_types = [r.get('document_type') for r in result]
                print(f"  Document types: {doc_types}")

                # Show top result title/part
                first = result[0]
                if first.get('title'):
                    print(f"  Top result: {first.get('title')[:70]}")
                elif first.get('part_name'):
                    print(f"  Top result: {first.get('part_name')[:70]}")

        print()


def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("VECTOR SEARCH TOOL - COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    print()

    test_basic_queries()
    test_with_filters()
    test_with_scores()
    test_different_k_values()
    test_input_validation()
    test_edge_cases()
    test_result_structure()
    test_real_world_queries()

    print_separator()
    print("TEST SUITE COMPLETE")
    print_separator()
    print()
    print("✅ All tests completed!")
    print()


if __name__ == "__main__":
    run_all_tests()
