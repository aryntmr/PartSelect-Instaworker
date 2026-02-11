"""Chat service for handling search queries."""

from services.database import db_service
from models.chat import ChatResponse, ChatMetadata
from models.part import PartCard


class ChatService:
    """Simple search service - generic DB search."""
    
    def search(self, message: str) -> ChatResponse:
        """
        Simple generic search.
        Takes message, searches DB, returns results.
        Search logic to be implemented later.
        
        Args:
            message: User's search query
            
        Returns:
            ChatResponse with parts found
        """
        # Generic search on database
        parts_data = db_service.search_parts(message, limit=4)
        
        # Convert to PartCard models
        products = []
        for p in parts_data:
            try:
                products.append(PartCard(
                    part_id=str(p['part_id']),
                    part_name=p['part_name'],
                    current_price=float(p['current_price']),
                    rating=float(p['rating']) if p.get('rating') else None,
                    review_count=p.get('review_count', 0),
                    image_url=p.get('image_url'),
                    product_url=p['product_url']
                ))
            except (KeyError, TypeError, ValueError) as e:
                # Skip malformed parts
                continue
        
        # Generate appropriate reply based on results
        if len(products) == 0:
            reply = "I couldn't find any parts matching your search. Try searching by part name, PartSelect number (e.g., PS12364199), or keywords like 'ice maker', 'water filter', 'door seal'."
        elif len(products) == 1:
            reply = "I found 1 part that matches your search:"
        else:
            reply = f"I found {len(products)} parts that match your search:"
        
        return ChatResponse(
            reply=reply,
            metadata=ChatMetadata(
                type="product_search",
                count=len(products),
                products=products
            )
        )
