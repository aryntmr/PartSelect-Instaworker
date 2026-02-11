"""Parts endpoint for direct part lookup."""

from fastapi import APIRouter, HTTPException
import uuid
from services.database import db_service


router = APIRouter()


@router.get(
    "/api/part/{part_id}",
    summary="Get Part Details",
    description="Retrieve detailed information about a specific part including compatible models.",
    tags=["Parts"],
    responses={
        200: {
            "description": "Part found successfully",
            "content": {
                "application/json": {
                    "example": {
                        "part_id": "f00c3ffe-158b-455c-87a7-fc085a9da4e6",
                        "part_name": "Ice Maker Assembly",
                        "current_price": 120.73,
                        "original_price": 130.00,
                        "has_discount": True,
                        "rating": 4.8,
                        "review_count": 145,
                        "brand": "Whirlpool",
                        "appliance_type": "refrigerator",
                        "availability": "In Stock",
                        "image_url": "https://example.com/image.jpg",
                        "product_url": "https://www.partselect.com/...",
                        "compatible_models": ["WDT780SAEM1", "RF263BEAEBC"]
                    }
                }
            }
        },
        404: {"description": "Part not found"},
        500: {"description": "Internal server error"}
    }
)
def get_part(part_id: str):
    """Get part details with compatible models."""
    try:
        # Validate UUID format
        try:
            uuid.UUID(part_id)
        except ValueError:
            raise HTTPException(status_code=404, detail="Part not found")
        
        # Get part details
        part = db_service.get_part_by_id(part_id)
        
        if not part:
            raise HTTPException(status_code=404, detail="Part not found")
        
        # Get compatible models
        compatible_models = db_service.get_compatible_models(part_id)
        
        # Return formatted response
        return {
            "part_id": str(part['part_id']),
            "part_name": part['part_name'],
            "current_price": float(part['current_price']),
            "original_price": float(part['original_price']),
            "has_discount": part.get('has_discount', False),
            "rating": float(part['rating']) if part.get('rating') else None,
            "review_count": part.get('review_count', 0),
            "brand": part.get('brand'),
            "appliance_type": part.get('appliance_type'),
            "availability": part.get('availability'),
            "image_url": part.get('image_url'),
            "product_url": part['product_url'],
            "compatible_models": compatible_models
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
