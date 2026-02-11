"""Chat endpoint for conversational interface."""

from fastapi import APIRouter, HTTPException
from models.chat import ChatRequest, ChatResponse
from services.chat_service import ChatService


router = APIRouter()
chat_service = ChatService()


@router.post(
    "/api/chat",
    response_model=ChatResponse,
    summary="Chat with AI Agent",
    description="Search for parts using natural language. Returns matching products with details.",
    tags=["Chat"],
    responses={
        200: {
            "description": "Successful response with products",
            "content": {
                "application/json": {
                    "example": {
                        "reply": "Here are the parts I found:",
                        "metadata": {
                            "type": "product_search",
                            "count": 2,
                            "products": [
                                {
                                    "part_id": "f00c3ffe-158b-455c-87a7-fc085a9da4e6",
                                    "part_name": "Ice Maker Assembly",
                                    "current_price": "120.73",
                                    "rating": "4.8",
                                    "review_count": 145,
                                    "image_url": "https://example.com/image.jpg",
                                    "product_url": "https://www.partselect.com/..."
                                }
                            ]
                        }
                    }
                }
            }
        },
        422: {"description": "Validation error - invalid request format"}
    }
)
def chat(request: ChatRequest):
    """Main chat endpoint."""
    try:
        # Process search
        response = chat_service.search(request.message)
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
