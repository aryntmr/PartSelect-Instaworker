"""
Scrape policy pages - extracts ONLY what actually exists on the pages.
No made-up metadata, only real content from the website.

Sources:
- https://www.partselect.com/365-Day-Returns.htm
- https://www.partselect.com/One-Year-Warranty.htm
- https://www.partselect.com/Fast-Shipping.htm
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import json
from pathlib import Path
from datetime import datetime

print("📜 Scraping policy pages...\n")

POLICY_PAGES = [
    {
        'url': 'https://www.partselect.com/365-Day-Returns.htm',
        'policy_type': 'returns'
    },
    {
        'url': 'https://www.partselect.com/One-Year-Warranty.htm',
        'policy_type': 'warranty'
    },
    {
        'url': 'https://www.partselect.com/Fast-Shipping.htm',
        'policy_type': 'shipping'
    }
]


def create_driver():
    chrome_options = Options()
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--no-sandbox')
    return webdriver.Chrome(options=chrome_options)


def scrape_policy_page(policy_info):
    """Scrape policy page - extract only what actually exists."""
    driver = create_driver()
    url = policy_info['url']

    try:
        print(f"  Scraping: {url}")

        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(3)

        soup = BeautifulSoup(driver.page_source, 'lxml')

        # Extract title (h1)
        title_elem = soup.select_one('h1')
        title = title_elem.get_text().strip() if title_elem else ''

        # Extract meta description
        meta_desc_elem = soup.select_one('meta[name="description"]')
        meta_description = meta_desc_elem.get('content', '') if meta_desc_elem else ''

        # Extract all h2 headings (sections)
        h2_headings = soup.select('h2')
        section_headings = [h2.get_text().strip() for h2 in h2_headings]

        # Extract all paragraphs
        paragraphs = soup.select('p')
        all_paragraphs = [p.get_text().strip() for p in paragraphs if p.get_text().strip()]

        # Extract ordered list items (steps/process)
        ol_items = soup.select('ol li')
        ordered_list_items = [li.get_text().strip() for li in ol_items if li.get_text().strip()]

        # Extract unordered list items
        ul_items = soup.select('ul li')
        # Filter out navigation items (likely have links or are very short)
        unordered_list_items = [
            li.get_text().strip()
            for li in ul_items
            if li.get_text().strip() and len(li.get_text().strip()) > 20
        ][:20]  # Limit to reasonable number

        # Get full content text
        # Try to find main content area, otherwise use body
        main_content = soup.select_one('main, article, .content, #main-content')
        if main_content:
            full_content = main_content.get_text(separator='\n', strip=True)
        else:
            # Fallback: get all paragraphs joined
            full_content = '\n\n'.join(all_paragraphs)

        # Build policy data with ONLY what exists
        policy_data = {
            'policy_type': policy_info['policy_type'],
            'url': url,
            'title': title,
            'meta_description': meta_description,
            'section_headings': section_headings,
            'paragraphs': all_paragraphs,
            'ordered_list_items': ordered_list_items,
            'unordered_list_items': unordered_list_items,
            'full_content': full_content,
            'content_length': len(full_content),
            'scraped_at': datetime.now().isoformat()
        }

        print(f"    ✓ Extracted: {len(all_paragraphs)} paragraphs, {len(ordered_list_items)} ordered items")

        driver.quit()
        return policy_data

    except Exception as e:
        print(f"    ❌ Error: {e}")
        driver.quit()
        return None


# Scrape all policy pages
policy_documents = []

for policy_info in POLICY_PAGES:
    result = scrape_policy_page(policy_info)
    if result:
        policy_documents.append(result)
    time.sleep(2)  # Polite delay

# Save results
print(f"\n💾 Saving {len(policy_documents)} policy documents...")

Path('data/processed').mkdir(parents=True, exist_ok=True)

output_file = 'data/processed/policies.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(policy_documents, f, indent=2, ensure_ascii=False)

print(f"\n{'='*60}")
print(f"✅ POLICY SCRAPING COMPLETE!")
print(f"{'='*60}")
print(f"   Total policies: {len(policy_documents)}")

for policy in policy_documents:
    print(f"\n   {policy['title']}:")
    print(f"     - Paragraphs: {len(policy['paragraphs'])}")
    print(f"     - Ordered list items: {len(policy['ordered_list_items'])}")
    print(f"     - Unordered list items: {len(policy['unordered_list_items'])}")
    print(f"     - Section headings: {len(policy['section_headings'])}")
    print(f"     - Content length: {policy['content_length']} chars")

print(f"\n   Saved to: {output_file}")
print(f"{'='*60}")
