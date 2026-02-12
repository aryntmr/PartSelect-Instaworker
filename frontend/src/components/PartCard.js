import React from "react";
import "./PartCard.css";

function PartCard({ product }) {
  // Handle missing image with placeholder
  const handleImageError = (e) => {
    e.target.src = "https://via.placeholder.com/200x200?text=No+Image";
  };

  // Format price with error handling
  let price = "N/A";
  try {
    const priceValue = typeof product.current_price === 'string' 
      ? parseFloat(product.current_price) 
      : product.current_price;
    if (!isNaN(priceValue)) {
      price = priceValue.toFixed(2);
    }
  } catch (e) {
    console.error('Error parsing price:', e, product);
  }

  // Format rating with error handling
  let rating = "N/A";
  try {
    if (product.rating) {
      const ratingValue = typeof product.rating === 'string'
        ? parseFloat(product.rating)
        : product.rating;
      if (!isNaN(ratingValue)) {
        rating = ratingValue.toFixed(1);
      }
    }
  } catch (e) {
    console.error('Error parsing rating:', e, product);
  }

  return (
    <div className="part-card">
      <div className="part-card-image-container">
        <img
          src={product.image_url || "https://via.placeholder.com/200x200?text=No+Image"}
          alt={product.part_name}
          className="part-card-image"
          onError={handleImageError}
        />
      </div>
      
      <div className="part-card-content">
        <h3 className="part-card-name">{product.part_name}</h3>
        
        <div className="part-card-price">
          ${price}
        </div>
        
        <div className="part-card-rating">
          <span className="rating-star">⭐</span>
          <span className="rating-value">{rating}</span>
          <span className="review-count">({product.review_count} reviews)</span>
        </div>
        
        <a
          href={product.product_url}
          target="_blank"
          rel="noopener noreferrer"
          className="part-card-button"
        >
          View on PartSelect
        </a>
      </div>
    </div>
  );
}

export default PartCard;
