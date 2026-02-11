"""Enrich parts data with details from product pages."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
from utils.data_cleaner import DataCleaner
from tqdm import tqdm

print("🔄 Enriching parts data with product page details...\n")

# Load existing parts
df = pd.read_csv('data/processed/parts_latest.csv')
print(f"📊 Loaded {len(df)} parts")

# Test mode - set to True to test on small set first
TEST_MODE = False
TEST_SIZE = 20

if TEST_MODE:
    df = df.head(TEST_SIZE)
    print(f"🧪 TEST MODE: Processing only {TEST_SIZE} parts")

cleaner = DataCleaner()

def create_selenium_driver():
    """Create a Selenium WebDriver with appropriate options."""
    chrome_options = Options()
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--no-sandbox')
    # chrome_options.add_argument('--headless')  # Uncomment for headless mode

    driver = webdriver.Chrome(options=chrome_options)
    return driver

def enrich_part(idx, url):
    """Fetch and extract details from product page using Selenium."""
    driver = create_selenium_driver()
    try:
        driver.get(url)

        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Small delay to ensure JS renders
        time.sleep(2)

        # Get page source after JS execution
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'lxml')

        # Extract price - handle both current and original (if discount exists)
        current_price = 0.0
        original_price = 0.0

        # Get current price (always shown)
        price_elem = soup.select_one('.pd__price')
        if price_elem:
            current_price = cleaner.clean_price(price_elem.get_text())
            original_price = current_price  # Default: original = current

        # Check for strikethrough/original price (indicates discount)
        original_elem = soup.select_one('.pd__price--original, .price--was, del, strike, [class*="original-price"]')
        if original_elem:
            orig_price = cleaner.clean_price(original_elem.get_text())
            if orig_price and orig_price > current_price:
                original_price = orig_price

        # Extract rating - count stars since no numeric rating shown
        rating_elem = soup.select_one('.rating__stars, .rating')
        if rating_elem:
            star_text = rating_elem.get_text()
            filled_stars = star_text.count('★')
            rating = filled_stars / 2 if filled_stars > 0 else None
        else:
            rating = None

        # Extract reviews
        review_elem = soup.select_one('.reviews, [class*="review"]')
        reviews = cleaner.clean_review_count(review_elem.get_text() if review_elem else '')

        # Extract description
        desc_elem = soup.select_one('.description, .part-description, [class*="description"]')
        description = desc_elem.get_text().strip() if desc_elem else ''

        # Extract symptoms from Customer Repair Stories
        symptoms = []
        repair_story_titles = soup.select('.repair-story__title')
        for title_elem in repair_story_titles[:10]:
            symptom_text = title_elem.get_text().strip()
            if symptom_text and len(symptom_text) > 10:
                symptoms.append(symptom_text)

        # Extract installation difficulty and time (SEPARATED)
        install_difficulty = ''
        install_time = ''

        repair_container = soup.select_one('.pd__repair-rating__container')
        if repair_container:
            bold_elements = repair_container.find_all('p', class_='bold')
            for p_elem in bold_elements:
                text = p_elem.get_text().strip()
                if 'min' in text.lower() or 'hour' in text.lower():
                    install_time = text
                elif any(word in text.lower() for word in ['easy', 'moderate', 'difficult', 'hard']):
                    install_difficulty = text

        # Extract replacement part numbers
        replacement_parts = []
        replace_section = soup.find(string=lambda t: t and 'replaces these' in t.lower())
        if replace_section:
            parent_div = replace_section.find_parent('div')
            if parent_div:
                data_div = parent_div.find_next_sibling('div')
                if data_div:
                    parts_text = data_div.get_text().strip()
                    if parts_text:
                        replacement_parts = [p.strip() for p in parts_text.split(',') if p.strip()][:10]

        # Extract compatible model numbers
        compatible_models = []
        crossref_list = soup.select('.pd__crossref__list .row')
        for row in crossref_list[:100]:
            model_link = row.select_one('a[href*="/Models/"]')
            if model_link:
                model_number = model_link.get_text().strip()
                model_url = 'https://www.partselect.com' + model_link.get('href', '')
                if model_number:
                    compatible_models.append({
                        'model_number': model_number,
                        'model_url': model_url
                    })

        # Extract video URL
        video_url = ''
        yt_elem = soup.select_one('[data-yt-init]')
        if yt_elem:
            yt_id = yt_elem.get('data-yt-init', '')
            if yt_id:
                video_url = f'https://www.youtube.com/watch?v={yt_id}'

        if not video_url:
            video_iframes = soup.select('iframe[src*="youtube"], iframe[src*="vimeo"], iframe[src*="youtu.be"]')
            if video_iframes:
                video_url = video_iframes[0].get('src', '')

        result = {
            'current_price': current_price,
            'original_price': original_price,
            'rating': rating,
            'review_count': reviews,
            'description': description[:500] if description else '',
            'symptoms': ' | '.join(symptoms) if symptoms else '',
            'replacement_parts': ' | '.join(replacement_parts) if replacement_parts else '',
            'installation_difficulty': install_difficulty,
            'installation_time': install_time,
            'video_url': video_url,
            'compatible_models': compatible_models,
            'compatible_models_count': len(compatible_models),
        }

        driver.quit()
        return idx, result

    except Exception as e:
        print(f"  ⚠️  Error on {url}: {e}")
        driver.quit()
        return idx, {}

# Parallel enrichment with Selenium
print(f"\n⚡ Fetching {len(df)} product pages with Selenium + BeautifulSoup...")
updates = {}

with ThreadPoolExecutor(max_workers=3) as executor:
    futures = {
        executor.submit(enrich_part, idx, row['product_url']): idx
        for idx, row in df.iterrows()
        if pd.notna(row['product_url'])
    }

    for future in tqdm(as_completed(futures), total=len(futures), desc="Enriching"):
        idx, data = future.result()
        if data:
            updates[idx] = data

# Update dataframe
print(f"\n💾 Updating {len(updates)} parts...")
import json

string_cols = ['description', 'symptoms', 'replacement_parts', 'installation_difficulty', 'installation_time', 'video_url', 'compatible_models_json']
numeric_cols = ['current_price', 'original_price', 'rating', 'review_count', 'compatible_models_count']

for col in string_cols + numeric_cols:
    if col not in df.columns:
        if col in string_cols:
            df[col] = ''
        else:
            df[col] = 0

for col in string_cols:
    if col in df.columns:
        df[col] = df[col].astype('object')

for idx, data in updates.items():
    for key, value in data.items():
        if key == 'compatible_models':
            df.at[idx, 'compatible_models_json'] = json.dumps(value) if value else ''
        else:
            df.at[idx, key] = value

# Save
if TEST_MODE:
    test_output = f'data/processed/parts_test_{pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")}.csv'
    df.to_csv(test_output, index=False)
    print(f"\n💾 Test results saved to: {test_output}")
else:
    df.to_csv('data/processed/parts_latest.csv', index=False)
    df.to_csv(f'data/processed/parts_enriched_{pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")}.csv', index=False)

print("\n✅ Enrichment complete!")
print(f"   💰 Parts with price: {df['current_price'].notna().sum()}/{len(df)} ({(df['current_price'] > 0).sum()} non-zero)")
print(f"   ⭐ Parts with rating: {df['rating'].notna().sum()}/{len(df)}")
print(f"   💬 Parts with reviews: {(df['review_count'] > 0).sum()}/{len(df)}")
print(f"   📝 Parts with description: {df['description'].notna().sum()}/{len(df)}")
print(f"   🔧 Parts with symptoms: {(df['symptoms'].astype(str).str.len() > 0).sum()}/{len(df)}")
print(f"   🔄 Parts with replacements: {(df['replacement_parts'].astype(str).str.len() > 0).sum()}/{len(df)}")
print(f"   ⚙️  Install difficulty: {(df['installation_difficulty'].astype(str).str.len() > 5).sum()}/{len(df)}")
print(f"   ⏱️  Install time: {(df['installation_time'].astype(str).str.len() > 5).sum()}/{len(df)}")
print(f"   📹 Parts with video: {(df['video_url'].astype(str).str.len() > 0).sum()}/{len(df)}")
print(f"   🔗 Parts with models: {(df['compatible_models_count'] > 0).sum()}/{len(df)}")
if (df['compatible_models_count'] > 0).sum() > 0:
    print(f"   📊 Total compatible models: {df['compatible_models_count'].sum()} (avg: {df['compatible_models_count'].mean():.1f} per part)")
