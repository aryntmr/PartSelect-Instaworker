"""
Scrape repair guides by extracting individual PART SECTIONS from symptom pages.
Each part section (identified by anchor links like #Pump) becomes an independent document.

Flow:
1. Scrape symptom pages (e.g., /Repair/Dishwasher/Noisy/)
2. Find all part sections (marked by <h2> with IDs like id="Pump")
3. Extract content ONLY for that specific part section
4. Create independent part documents

Sources:
- https://www.partselect.com/Repair/Refrigerator/ (symptom categories)
- https://www.partselect.com/Repair/Dishwasher/ (symptom categories)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

print("🔧 Scraping repair part sections for refrigerators and dishwashers...\n")

# Configuration
REPAIR_CATEGORIES = {
    'refrigerator': 'https://www.partselect.com/Repair/Refrigerator/',
    'dishwasher': 'https://www.partselect.com/Repair/Dishwasher/'
}

def create_driver():
    """Create Selenium WebDriver with anti-detection."""
    chrome_options = Options()
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--no-sandbox')
    # chrome_options.add_argument('--headless')  # Uncomment for headless mode

    return webdriver.Chrome(options=chrome_options)

def scrape_symptom_urls(appliance_type, base_url):
    """
    Scrape all symptom URLs from the main repair category page.
    Example: Get all symptom links from /Repair/Refrigerator/
    """
    print(f"\n📋 Scraping symptom URLs for {appliance_type}...")
    driver = create_driver()
    symptom_urls = []

    try:
        driver.get(base_url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(2)

        soup = BeautifulSoup(driver.page_source, 'lxml')

        # Find all symptom/repair links
        symptom_links = soup.select('a[href*="/Repair/"]')

        for link in symptom_links:
            href = link.get('href', '')
            if href and f'/Repair/{appliance_type.capitalize()}/' in href and href not in [s['url'] for s in symptom_urls]:
                # Build full URL
                full_url = href if href.startswith('http') else 'https://www.partselect.com' + href

                # Get symptom title
                symptom_title = link.get_text().strip()

                if symptom_title and full_url != base_url:  # Avoid duplicates
                    symptom_urls.append({
                        'url': full_url,
                        'symptom': symptom_title,
                        'appliance_type': appliance_type
                    })

        print(f"   ✓ Found {len(symptom_urls)} symptom categories for {appliance_type}")

    except Exception as e:
        print(f"   ❌ Error scraping symptom URLs: {e}")
    finally:
        driver.quit()

    return symptom_urls

def extract_section_content(section_elem, next_section_elem):
    """
    Extract all content between current section and next section.
    Returns the text content specific to this part section only.
    """
    content_parts = []

    # Get all siblings between current section and next section
    current = section_elem.find_next_sibling()

    while current and current != next_section_elem:
        # Extract text from this element
        text = current.get_text().strip()
        if text and len(text) > 10:  # Meaningful content
            content_parts.append(text)
        current = current.find_next_sibling()

    return '\n\n'.join(content_parts)

def scrape_part_sections(symptom_info):
    """
    Scrape individual part sections from a symptom page.
    Each part section (marked by <h2 id="PartName">) becomes a separate document.
    """
    driver = create_driver()
    url = symptom_info['url']
    part_documents = []

    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(2)

        soup = BeautifulSoup(driver.page_source, 'lxml')

        # Extract page-level metadata
        symptom = symptom_info['symptom']
        title_elem = soup.select_one('h1, .page-title')
        if title_elem:
            symptom = title_elem.get_text().strip()

        # Extract page-level difficulty (if exists)
        page_difficulty = ''
        difficulty_elem = soup.select_one('.difficulty, [class*="difficulty"]')
        if difficulty_elem:
            page_difficulty = difficulty_elem.get_text().strip()

        # Extract repair time
        repair_time = ''
        time_elem = soup.select_one('.repair-time, [class*="time-estimate"]')
        if time_elem:
            repair_time = time_elem.get_text().strip()

        # Extract videos (page-level)
        videos = []
        yt_iframes = soup.select('iframe[src*="youtube"], iframe[src*="youtu.be"]')
        for iframe in yt_iframes[:3]:
            video_url = iframe.get('src', '')
            if video_url:
                videos.append(video_url)

        # Find all part sections (h2 elements with IDs)
        part_sections = soup.select('h2[id]')

        # Filter out generic/non-part IDs
        excluded_ids = [
            'ShopByDepartment', 'hTopApplianceBrands', 'hTopLawnEquipmentBrands', 'SampleTags',
            'hj-survey-lbl-1', 'survey'  # Survey sections
        ]
        excluded_keywords = ['survey', 'rate', 'feedback', 'experience']

        part_sections = [
            section for section in part_sections
            if section.get('id') and
            section.get('id') not in excluded_ids and
            not any(keyword in section.get_text().lower() for keyword in excluded_keywords)
        ]

        print(f"   Found {len(part_sections)} part sections in {symptom}")

        # Extract content for each part section
        for idx, section in enumerate(part_sections):
            part_id = section.get('id', '')
            part_name = section.get_text().strip()

            # Get next section to know where this section ends
            next_section = part_sections[idx + 1] if idx + 1 < len(part_sections) else None

            # Extract content specific to this part section
            part_content = extract_section_content(section, next_section)

            # Skip sections with insufficient content
            if len(part_content) < 200:
                continue

            # Extract difficulty specific to this part (if exists within section)
            part_difficulty = page_difficulty  # Default to page-level

            # Look for difficulty within this part section
            if part_content:
                difficulty_markers = ['REALLY EASY', 'EASY', 'MODERATE', 'DIFFICULT', 'REALLY DIFFICULT']
                for marker in difficulty_markers:
                    if marker in part_content.upper():
                        part_difficulty = marker
                        break

            # Create part document
            part_doc = {
                'document_type': 'repair_part',
                'appliance_type': symptom_info['appliance_type'],
                'category': symptom_info['symptom'],  # Category/symptom (e.g., "Noisy")
                'title': symptom,  # Full title (e.g., "How To Fix A Noisy Dishwasher")
                'part_name': part_name,
                'part_id': part_id,  # Anchor ID (e.g., "Pump")
                'difficulty': part_difficulty,
                'repair_time': repair_time,
                'content': part_content,
                'content_length': len(part_content),
                'has_video': len(videos) > 0,
                'video_urls': ' | '.join(videos) if videos else '',
                'video_count': len(videos),
                'symptom_url': url,
                'part_url': f"{url}#{part_id}",  # Direct link to this section
                'scraped_at': pd.Timestamp.now().isoformat()
            }

            part_documents.append(part_doc)

        driver.quit()
        return part_documents

    except Exception as e:
        print(f"   ⚠️  Error scraping {url}: {e}")
        driver.quit()
        return []

# Step 1: Get all symptom URLs
all_symptom_urls = []
for appliance_type, base_url in REPAIR_CATEGORIES.items():
    urls = scrape_symptom_urls(appliance_type, base_url)
    all_symptom_urls.extend(urls)

print(f"\n📊 Total symptom pages to scrape: {len(all_symptom_urls)}")
print(f"   - Refrigerator: {len([u for u in all_symptom_urls if u['appliance_type'] == 'refrigerator'])}")
print(f"   - Dishwasher: {len([u for u in all_symptom_urls if u['appliance_type'] == 'dishwasher'])}")

# Step 2: Scrape each symptom page and extract part sections
print(f"\n⚡ Scraping part sections from each symptom page...")
all_part_documents = []

with ThreadPoolExecutor(max_workers=3) as executor:
    futures = {
        executor.submit(scrape_part_sections, symptom_info): symptom_info
        for symptom_info in all_symptom_urls
    }

    for future in tqdm(as_completed(futures), total=len(futures), desc="Scraping parts"):
        part_docs = future.result()
        if part_docs:
            all_part_documents.extend(part_docs)

print(f"\n   ✓ Extracted {len(all_part_documents)} part documents")

# Step 3: Separate by appliance type and save
print(f"\n💾 Saving part documents...")

output_dir = Path('data/rag_documents')
output_dir.mkdir(parents=True, exist_ok=True)

refrigerator_parts = [p for p in all_part_documents if p['appliance_type'] == 'refrigerator']
dishwasher_parts = [p for p in all_part_documents if p['appliance_type'] == 'dishwasher']

with open(output_dir / 'refrigerator_parts.json', 'w', encoding='utf-8') as f:
    json.dump(refrigerator_parts, f, indent=2, ensure_ascii=False)

with open(output_dir / 'dishwasher_parts.json', 'w', encoding='utf-8') as f:
    json.dump(dishwasher_parts, f, indent=2, ensure_ascii=False)

print(f"\n{'='*60}")
print(f"✅ REPAIR PART SECTIONS SCRAPING COMPLETE!")
print(f"{'='*60}")
print(f"   Total parts scraped: {len(all_part_documents)}")
print(f"   - Refrigerator parts: {len(refrigerator_parts)}")
print(f"   - Dishwasher parts: {len(dishwasher_parts)}")
print(f"\n   Saved to: data/rag_documents/")
print(f"   - {output_dir / 'refrigerator_parts.json'}")
print(f"   - {output_dir / 'dishwasher_parts.json'}")
print(f"\n   Each part document contains:")
print(f"   ✓ Part name & anchor ID")
print(f"   ✓ Appliance type & category")
print(f"   ✓ Title (symptom description)")
print(f"   ✓ Difficulty (part-specific)")
print(f"   ✓ Content (ONLY for this part section)")
print(f"   ✓ Video URLs")
print(f"   ✓ Direct part URL (with #anchor)")
print(f"\n   🎯 Ready for vector DB!")
print(f"{'='*60}")
