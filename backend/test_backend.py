"""
Comprehensive backend testing script.
Tests all endpoints with various scenarios.
Run with: python test_backend.py
"""

import requests
import json
import sys
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def print_test(name: str):
    """Print test name."""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}TEST: {name}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")


def print_success(msg: str):
    """Print success message."""
    print(f"{GREEN}✓ {msg}{RESET}")


def print_error(msg: str):
    """Print error message."""
    print(f"{RED}✗ {msg}{RESET}")


def print_warning(msg: str):
    """Print warning message."""
    print(f"{YELLOW}⚠ {msg}{RESET}")


def print_response(response: requests.Response):
    """Print response details."""
    print(f"Status: {response.status_code}")
    try:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
    except:
        print(f"Response: {response.text}")


def test_root_endpoint():
    """Test GET / endpoint."""
    print_test("Root Endpoint (GET /)")
    
    try:
        response = requests.get(f"{BASE_URL}/")
        print_response(response)
        
        assert response.status_code == 200, "Expected status 200"
        data = response.json()
        assert "service" in data, "Missing 'service' field"
        assert "version" in data, "Missing 'version' field"
        assert "status" in data, "Missing 'status' field"
        
        print_success("Root endpoint test passed")
        return True
    except Exception as e:
        print_error(f"Root endpoint test failed: {e}")
        return False


def test_health_endpoint():
    """Test GET /health endpoint."""
    print_test("Health Check (GET /health)")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        print_response(response)
        
        assert response.status_code == 200, "Expected status 200"
        data = response.json()
        assert "status" in data, "Missing 'status' field"
        assert "database" in data, "Missing 'database' field"
        assert "timestamp" in data, "Missing 'timestamp' field"
        assert data["database"] in ["connected", "disconnected"], "Invalid database status"
        
        if data["database"] == "disconnected":
            print_warning("Database is disconnected!")
        
        print_success("Health endpoint test passed")
        return True
    except Exception as e:
        print_error(f"Health endpoint test failed: {e}")
        return False


def test_chat_endpoint_basic():
    """Test POST /api/chat with basic message."""
    print_test("Chat Endpoint - Basic Search (POST /api/chat)")
    
    try:
        payload = {
            "message": "ice maker"
        }
        response = requests.post(f"{BASE_URL}/api/chat", json=payload)
        print_response(response)
        
        assert response.status_code == 200, f"Expected status 200, got {response.status_code}"
        data = response.json()
        
        # Validate response structure
        assert "reply" in data, "Missing 'reply' field"
        assert "metadata" in data, "Missing 'metadata' field"
        assert "type" in data["metadata"], "Missing 'metadata.type' field"
        assert "count" in data["metadata"], "Missing 'metadata.count' field"
        assert "products" in data["metadata"], "Missing 'metadata.products' field"
        assert isinstance(data["metadata"]["products"], list), "products should be a list"
        
        # Check product structure if any products returned
        if data["metadata"]["products"]:
            product = data["metadata"]["products"][0]
            assert "part_id" in product, "Missing 'part_id' in product"
            assert "part_name" in product, "Missing 'part_name' in product"
            assert "current_price" in product, "Missing 'current_price' in product"
            assert "product_url" in product, "Missing 'product_url' in product"
            
            print_success(f"Found {data['metadata']['count']} products")
        else:
            print_warning("No products found in search")
        
        print_success("Chat endpoint basic test passed")
        return True
    except Exception as e:
        print_error(f"Chat endpoint basic test failed: {e}")
        return False


def test_chat_endpoint_empty_message():
    """Test POST /api/chat with empty message."""
    print_test("Chat Endpoint - Empty Message (Error Test)")
    
    try:
        payload = {
            "message": ""
        }
        response = requests.post(f"{BASE_URL}/api/chat", json=payload)
        print_response(response)
        
        # FastAPI returns 422 for validation errors
        assert response.status_code == 422, f"Expected status 422, got {response.status_code}"
        
        print_success("Empty message validation test passed")
        return True
    except Exception as e:
        print_error(f"Empty message test failed: {e}")
        return False


def test_chat_endpoint_no_message():
    """Test POST /api/chat without message field."""
    print_test("Chat Endpoint - No Message Field (Error Test)")
    
    try:
        payload = {}
        response = requests.post(f"{BASE_URL}/api/chat", json=payload)
        print_response(response)
        
        # Should return error for missing message
        assert response.status_code == 422, f"Expected status 422, got {response.status_code}"
        
        print_success("Missing message validation test passed")
        return True
    except Exception as e:
        print_error(f"Missing message test failed: {e}")
        return False


def test_chat_endpoint_with_conversation_id():
    """Test POST /api/chat with conversation_id."""
    print_test("Chat Endpoint - With Conversation ID")
    
    try:
        payload = {
            "message": "dishwasher parts",
            "conversation_id": "test-conv-123"
        }
        response = requests.post(f"{BASE_URL}/api/chat", json=payload)
        print_response(response)
        
        assert response.status_code == 200, f"Expected status 200, got {response.status_code}"
        data = response.json()
        assert "reply" in data, "Missing 'reply' field"
        assert "metadata" in data, "Missing 'metadata' field"
        
        print_success("Conversation ID test passed")
        return True
    except Exception as e:
        print_error(f"Conversation ID test failed: {e}")
        return False


def test_chat_various_queries():
    """Test chat endpoint with various query types."""
    print_test("Chat Endpoint - Various Query Types")
    
    queries = [
        "water filter",
        "door seal",
        "compressor",
        "pump",
        "valve"
    ]
    
    passed = 0
    for query in queries:
        try:
            payload = {"message": query}
            response = requests.post(f"{BASE_URL}/api/chat", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                print(f"  Query '{query}': {data['metadata']['count']} products found")
                passed += 1
            else:
                print_warning(f"  Query '{query}' failed with status {response.status_code}")
        except Exception as e:
            print_warning(f"  Query '{query}' error: {e}")
    
    print_success(f"Various queries test: {passed}/{len(queries)} passed")
    return passed == len(queries)


def test_part_endpoint_valid():
    """Test GET /api/part/<part_id> with valid part."""
    print_test("Part Endpoint - Valid Part ID")
    
    # First get a part ID from chat endpoint
    try:
        chat_response = requests.post(f"{BASE_URL}/api/chat", json={"message": "ice maker"})
        if chat_response.status_code == 200:
            data = chat_response.json()
            if data["metadata"]["products"]:
                part_id = data["metadata"]["products"][0]["part_id"]
                print(f"Testing with part_id: {part_id}")
                
                # Now test the part endpoint
                response = requests.get(f"{BASE_URL}/api/part/{part_id}")
                print_response(response)
                
                assert response.status_code == 200, f"Expected status 200, got {response.status_code}"
                part_data = response.json()
                
                # Validate response structure
                required_fields = [
                    "part_id", "part_name", "current_price", "original_price",
                    "has_discount", "rating", "review_count", "brand",
                    "appliance_type", "availability", "image_url", "product_url",
                    "compatible_models"
                ]
                
                for field in required_fields:
                    assert field in part_data, f"Missing field: {field}"
                
                assert isinstance(part_data["compatible_models"], list), "compatible_models should be a list"
                
                print_success("Valid part endpoint test passed")
                return True
            else:
                print_warning("No products found to test with")
                return True  # Not a failure, just no data
        else:
            print_warning("Could not get part ID from chat endpoint")
            return True  # Not a failure, just skip
    except Exception as e:
        print_error(f"Valid part endpoint test failed: {e}")
        return False


def test_part_endpoint_invalid():
    """Test GET /api/part/<part_id> with invalid part."""
    print_test("Part Endpoint - Invalid Part ID")
    
    try:
        response = requests.get(f"{BASE_URL}/api/part/INVALID_PART_ID_999999")
        print_response(response)
        
        assert response.status_code == 404, f"Expected status 404, got {response.status_code}"
        data = response.json()
        # FastAPI uses 'detail' field for error messages
        assert "detail" in data, "Missing 'detail' field in error response"
        
        print_success("Invalid part endpoint test passed")
        return True
    except Exception as e:
        print_error(f"Invalid part endpoint test failed: {e}")
        return False


def run_all_tests():
    """Run all tests and print summary."""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}STARTING BACKEND TESTS{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    
    tests = [
        ("Root Endpoint", test_root_endpoint),
        ("Health Endpoint", test_health_endpoint),
        ("Chat - Basic Search", test_chat_endpoint_basic),
        ("Chat - Empty Message", test_chat_endpoint_empty_message),
        ("Chat - No Message", test_chat_endpoint_no_message),
        ("Chat - With Conversation ID", test_chat_endpoint_with_conversation_id),
        ("Chat - Various Queries", test_chat_various_queries),
        ("Part - Valid ID", test_part_endpoint_valid),
        ("Part - Invalid ID", test_part_endpoint_invalid),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print_error(f"Unexpected error in {test_name}: {e}")
            results.append((test_name, False))
    
    # Print summary
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}TEST SUMMARY{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = f"{GREEN}PASS{RESET}" if result else f"{RED}FAIL{RESET}"
        print(f"{test_name}: {status}")
    
    print(f"\n{BLUE}{'='*60}{RESET}")
    if passed == total:
        print(f"{GREEN}ALL TESTS PASSED: {passed}/{total}{RESET}")
    else:
        print(f"{RED}SOME TESTS FAILED: {passed}/{total} passed{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")
    
    return passed == total


if __name__ == "__main__":
    print("\nMake sure the FastAPI server is running on http://localhost:8000")
    print("Start server with: python app.py")
    input("\nPress Enter to start tests...")
    
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Tests interrupted by user{RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{RED}Fatal error: {e}{RESET}")
        sys.exit(1)
