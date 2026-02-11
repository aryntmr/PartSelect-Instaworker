"""
Step 1: Initial Parts List Scraper
Quickly scrapes PartSelect category pages to get part URLs and basic info.
This is the FAST step - just gets the list of parts to process.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time

print("🔄 Scraping initial parts list from category pages...\n")

# Configuration - scrape from category listing pages
CATEGORIES = {
    'refrigerator': 'https://www.partselect.com/Refrigerator-Parts.htm',
    'dishwasher': 'https://www.partselect.com/Dishwasher-Parts.htm'
}
PARTS_PER_CATEGORY = 60  # Total: 120 parts (60 + 60)

def create_driver():
    """Create Selenium WebDriver."""
    chrome_options = Options()
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--no-sandbox')
    # chrome_options.add_argument('--headless')

    return webdriver.Chrome(options=chrome_options)

def scrape_category_listing(appliance_type, url, max_parts=60):
    """
    Scrape parts from category listing page.
    Only extracts basic info visible on the listing - NO individual page visits.
    """
    print(f"\n📦 Scraping {appliance_type} category: {url}")

    driver = create_driver()
    parts = []

    try:
        driver.get(url)
        time.sleep(3)  # Wait for page load

        # Parse the category listing page
        soup = BeautifulSoup(driver.page_source, 'lxml')

        # Find all part cards/tiles on the listing page
        # PartSelect shows parts in a grid - extract from each card
        part_cards = soup.select('.mega-m__part, .part-thumbnail, [class*="part"]')[:max_parts*2]

        print(f"   Found {len(part_cards)} potential parts on listing page")

        for card in part_cards:
            try:
                # Extract product URL
                link = card.select_one('a[href*="/PS"]')
                if not link:
                    continue

                product_url = link.get('href', '')
                if not product_url.startswith('http'):
                    product_url = 'https://www.partselect.com' + product_url

                # Extract part number from URL
                part_number = ''
                if '/PS' in product_url:
                    part_number = product_url.split('/PS')[1].split('-')[0]
                    part_number = 'PS' + part_number

                # Part name from listing
                name_elem = card.select_one('.mega-m__part__name, h3, h4, .part-name')
                part_name = name_elem.get_text().strip() if name_elem else part_number

                # Brand from listing (if available)
                brand_elem = card.select_one('.brand, [class*="brand"]')
                brand = brand_elem.get_text().strip() if brand_elem else ''

                # Image from listing
                image_elem = card.select_one('img')
                image_url = image_elem.get('src', '') if image_elem else ''
                if image_url and not image_url.startswith('http'):
                    image_url = 'https:' + image_url if image_url.startswith('//') else 'https://www.partselect.com' + image_url

                # Create basic part record
                # Most fields will be empty - enrich_parts.py will fill them in
                part_data = {
                    'part_id': part_number,
                    'part_name': part_name,
                    'part_number': part_number,
                    'manufacturer_part_number': part_number,  # Will be enriched later
                    'brand': brand,
                    'appliance_type': appliance_type,
                    'current_price': 0.0,  # Will be enriched
                    'original_price': 0.0,  # Will be enriched
                    'image_url': image_url,
                    'product_url': product_url,
                    # These fields will be filled by enrich_parts.py
                    'has_discount': False,
                    'rating': None,
                    'review_count': 0,
                    'description': '',
                    'symptoms': '',
                    'replacement_parts': '',
                    'installation_difficulty': '',
                    'installation_time': '',
                    'delivery_time': '',
                    'availability': '',
                    'video_url': ''
                }

                parts.append(part_data)
                print(f"   ✓ {len(parts)}: {part_name[:50]}")

                if len(parts) >= max_parts:
                    break

            except Exception as e:
                continue

    except Exception as e:
        print(f"   ❌ Error scraping category: {e}")

    finally:
        driver.quit()

    return parts

# Scrape all categories
all_parts = []

for appliance_type, url in CATEGORIES.items():
    parts = scrape_category_listing(appliance_type, url, PARTS_PER_CATEGORY)
    all_parts.extend(parts)
    print(f"   ✅ Scraped {len(parts)} {appliance_type} parts from listing")

# Create DataFrame
df = pd.DataFrame(all_parts)

# Remove duplicates by part_number
df = df.drop_duplicates(subset=['part_number'], keep='first')

# Save to CSV
output_path = 'data/processed/parts_latest.csv'
Path('data/processed').mkdir(parents=True, exist_ok=True)
df.to_csv(output_path, index=False)

print(f"\n{'='*60}")
print(f"✅ INITIAL SCRAPING COMPLETE!")
print(f"{'='*60}")
print(f"   Total parts scraped: {len(df)}")
print(f"   Refrigerator parts: {len(df[df['appliance_type'] == 'refrigerator'])}")
print(f"   Dishwasher parts: {len(df[df['appliance_type'] == 'dishwasher'])}")
print(f"   Saved to: {output_path}")
print(f"\n   ⚠️  Fields extracted: part_name, part_number, image_url, product_url")
print(f"   ⏭️  Next step: Run enrich_parts.py to add ALL detailed fields")
print(f"   (prices, ratings, symptoms, videos, compatible models, etc.)")
print(f"{'='*60}")
