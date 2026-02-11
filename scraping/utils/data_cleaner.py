"""Data cleaning and validation utilities."""

import re
from typing import Any, Optional
from decimal import Decimal, InvalidOperation


class DataCleaner:
    """Utilities for cleaning and validating scraped data."""

    @staticmethod
    def clean_price(price_text: str) -> Optional[float]:
        """
        Extract and clean price from text.

        Args:
            price_text: Raw price string (e.g., "$44.95", "44.95", "$44")

        Returns:
            Cleaned price as float, or None if invalid
        """
        if not price_text:
            return None

        # Remove currency symbols, commas, and whitespace
        cleaned = re.sub(r'[$,\s]', '', str(price_text))

        try:
            return float(cleaned)
        except (ValueError, InvalidOperation):
            return None

    @staticmethod
    def clean_rating(rating_text: str) -> Optional[float]:
        """
        Extract rating from text.

        Args:
            rating_text: Raw rating string (e.g., "4.9 out of 5", "4.9")

        Returns:
            Rating as float (0-5), or None if invalid
        """
        if not rating_text:
            return None

        # Extract first number that looks like a rating
        match = re.search(r'(\d+\.?\d*)', str(rating_text))
        if match:
            try:
                rating = float(match.group(1))
                return rating if 0 <= rating <= 5 else None
            except ValueError:
                return None
        return None

    @staticmethod
    def clean_review_count(review_text: str) -> int:
        """
        Extract review count from text.

        Args:
            review_text: Raw review text (e.g., "127 reviews", "(45)")

        Returns:
            Review count as integer, or 0 if invalid
        """
        if not review_text:
            return 0

        # Extract number from text
        match = re.search(r'(\d+)', str(review_text))
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                return 0
        return 0

    @staticmethod
    def clean_part_number(part_number: str) -> Optional[str]:
        """
        Clean and validate part number.

        Args:
            part_number: Raw part number

        Returns:
            Cleaned part number or None
        """
        if not part_number:
            return None

        # Remove extra whitespace and convert to uppercase
        cleaned = str(part_number).strip().upper()
        return cleaned if cleaned else None

    @staticmethod
    def clean_text(text: str) -> str:
        """
        Clean general text content.

        Args:
            text: Raw text

        Returns:
            Cleaned text
        """
        if not text:
            return ""

        # Remove extra whitespace and newlines
        cleaned = re.sub(r'\s+', ' ', str(text))
        return cleaned.strip()

    @staticmethod
    def extract_model_number(text: str) -> Optional[str]:
        """
        Extract model number from text.

        Args:
            text: Text containing model number

        Returns:
            Model number or None
        """
        if not text:
            return None

        # Model numbers typically have letters and numbers
        # Examples: WDT780SAEM1, RF28R7351SR, GNE27JSMSS
        match = re.search(r'[A-Z]{2,}[\w\d-]+', str(text).upper())
        if match:
            return match.group(0)
        return None

    @staticmethod
    def is_valid_url(url: str) -> bool:
        """
        Check if URL is valid.

        Args:
            url: URL to validate

        Returns:
            True if valid, False otherwise
        """
        if not url:
            return False

        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or IP
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        return bool(url_pattern.match(url))

    @staticmethod
    def normalize_appliance_type(appliance_type: str) -> str:
        """
        Normalize appliance type to lowercase standard values.

        Args:
            appliance_type: Raw appliance type

        Returns:
            'refrigerator' or 'dishwasher'
        """
        if not appliance_type:
            return "unknown"

        normalized = str(appliance_type).lower().strip()

        if 'refrig' in normalized or 'fridge' in normalized:
            return 'refrigerator'
        elif 'dishwash' in normalized:
            return 'dishwasher'
        else:
            return normalized

    @staticmethod
    def detect_discount(original_price: Optional[float], current_price: Optional[float]) -> bool:
        """
        Detect if product has a discount.

        Args:
            original_price: Original price
            current_price: Current price

        Returns:
            True if discounted, False otherwise
        """
        if original_price is None or current_price is None:
            return False

        return original_price > current_price
