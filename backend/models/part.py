"""Part models for product data."""

from pydantic import BaseModel
from typing import Optional
from decimal import Decimal


class PartCard(BaseModel):
    """Product card for frontend display."""
    
    part_id: str
    part_name: str
    current_price: Decimal
    rating: Optional[Decimal] = None
    review_count: int = 0
    image_url: Optional[str] = None
    product_url: str
