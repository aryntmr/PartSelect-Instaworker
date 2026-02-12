"""
Scrape blog articles for refrigerators and dishwashers ONLY.
Carefully filters to stay within scope - only dishwasher and refrigerator blogs.

Sources:
- https://www.partselect.com/blog/topics/repair
- https://www.partselect.com/blog/topics/error-codes
- https://www.partselect.com/blog/topics/how-to-guides
- https://www.partselect.com/blog/topics/testing
- https://www.partselect.com/blog/topics/use-and-care

Filters: Only articles about dishwashers and refrigerators.
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
import re

print("📝 Scraping blog articles for refrigerators and dishwashers...\n")

# Configuration - Blog topic categories
BLOG_TOPICS = [
    'https://www.partselect.com/blog/topics/repair',
    'https://www.partselect.com/blog/topics/error-codes',
    'https://www.partselect.com/blog/topics/how-to-guides',
    'https://www.partselect.com/blog/topics/testing',
    'https://www.partselect.com/blog/topics/use-and-care'
]

# Keywords to filter for refrigerator and dishwasher content only
REFRIGERATOR_KEYWORDS = [
    'refrigerator', 'fridge', 'freezer', 'ice maker', 'icemaker',
    'water dispenser', 'refrigeration', 'cooler'
]

DISHWASHER_KEYWORDS = [
    'dishwasher', 'dish washer', 'dishwashing'
]

def create_driver():
    """Create Selenium WebDriver with anti-detection."""
    chrome_options = Options()
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--no-sandbox')
    # chrome_options.add_argument('--headless')  # Uncomment for headless mode

    return webdriver.Chrome(options=chrome_options)

def is_relevant_article(title, excerpt=''):
    """
    Check if article is about refrigerator or dishwasher.
    Returns: ('refrigerator', True), ('dishwasher', True), or (None, False)
    """
    combined_text = (title + ' ' + excerpt).lower()

    # Check for refrigerator
    for keyword in REFRIGERATOR_KEYWORDS:
        if keyword in combined_text:
            return 'refrigerator', True

    # Check for dishwasher
    for keyword in DISHWASHER_KEYWORDS:
        if keyword in combined_text:
            return 'dishwasher', True

    return None, False

def scrape_blog_topic_urls(topic_url):
    """
    Scrape all blog article URLs from a topic page.
    Only includes refrigerator and dishwasher articles.
    """
    print(f"\n📋 Scraping blog topic: {topic_url}")
    driver = create_driver()
    blog_urls = []

    try:
        driver.get(topic_url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(2)

        soup = BeautifulSoup(driver.page_source, 'lxml')

        # Find all blog article cards/links
        article_cards = soup.select('article, .blog-post, .post-card, [class*="article"]')

        if not article_cards:
            # Try alternative selectors
            article_cards = soup.select('a[href*="/blog/"]')

        for card in article_cards:
            # Get article link
            link_elem = card if card.name == 'a' else card.select_one('a[href*="/blog/"]')
            if not link_elem:
                continue

            article_url = link_elem.get('href', '')
            if not article_url or '/topics/' in article_url:  # Skip topic pages
                continue

            if not article_url.startswith('http'):
                article_url = 'https://www.partselect.com' + article_url

            # Get article title
            title_elem = card.select_one('h2, h3, h4, .title, .post-title, [class*="title"]')
            title = title_elem.get_text().strip() if title_elem else ''

            # Get article excerpt/description
            excerpt_elem = card.select_one('.excerpt, .description, p')
            excerpt = excerpt_elem.get_text().strip() if excerpt_elem else ''

            # Check if relevant (refrigerator or dishwasher)
            appliance_type, is_relevant = is_relevant_article(title, excerpt)

            if is_relevant:
                blog_urls.append({
                    'url': article_url,
                    'title': title,
                    'excerpt': excerpt[:200],
                    'appliance_type': appliance_type,
                    'topic_url': topic_url
                })

        # Handle pagination if exists
        next_page = soup.select_one('.next-page, .pagination .next, a[rel="next"]')
        if next_page and len(blog_urls) < 100:  # Limit to avoid infinite loop
            next_url = next_page.get('href', '')
            if next_url and next_url not in topic_url:
                if not next_url.startswith('http'):
                    next_url = 'https://www.partselect.com' + next_url
                # Recursively scrape next page (would need to handle this properly)
                pass

        print(f"   ✓ Found {len(blog_urls)} relevant articles")

    except Exception as e:
        print(f"   ❌ Error scraping blog topic: {e}")
    finally:
        driver.quit()

    return blog_urls

def scrape_blog_article(blog_info):
    """
    Scrape full blog article content with metadata from website only.
    Extracts: title, author, date, content, tags, images, etc.
    """
    driver = create_driver()
    url = blog_info['url']

    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(2)

        soup = BeautifulSoup(driver.page_source, 'lxml')

        # Extract title
        title = blog_info['title']
        title_elem = soup.select_one('h1, .article-title, .post-title')
        if title_elem:
            title = title_elem.get_text().strip()

        # Extract author
        author = ''
        author_elem = soup.select_one('.author, [class*="author"], [rel="author"]')
        if author_elem:
            author = author_elem.get_text().strip()

        # Extract published date
        published_date = ''
        date_elem = soup.select_one('time, .date, .published, [datetime]')
        if date_elem:
            published_date = date_elem.get('datetime') or date_elem.get_text().strip()

        # Extract category/tags
        categories = []
        category_elems = soup.select('.category, .tag, [rel="category"]')
        for cat in category_elems:
            categories.append(cat.get_text().strip())

        # Extract featured image
        featured_image = ''
        img_elem = soup.select_one('.featured-image img, article img, .post-image img')
        if img_elem:
            featured_image = img_elem.get('src', '')
            if featured_image and not featured_image.startswith('http'):
                featured_image = 'https:' + featured_image if featured_image.startswith('//') else 'https://www.partselect.com' + featured_image

        # Extract all images in article
        images = []
        img_elems = soup.select('article img, .content img, .post-content img')
        for img in img_elems[:10]:  # Limit to 10 images
            img_src = img.get('src', '')
            if img_src:
                if not img_src.startswith('http'):
                    img_src = 'https:' + img_src if img_src.startswith('//') else 'https://www.partselect.com' + img_src
                images.append(img_src)

        # Extract full article content
        content = ''
        content_elem = soup.select_one('article, .article-content, .post-content, .content, main')
        if content_elem:
            # Get all paragraphs
            paragraphs = content_elem.select('p')
            content = '\n\n'.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])

        # Extract reading time if available
        reading_time = ''
        time_elem = soup.select_one('.reading-time, [class*="read-time"]')
        if time_elem:
            reading_time = time_elem.get_text().strip()

        # Extract related parts mentioned in article
        related_parts = []
        part_links = soup.select('a[href*="/PS"]')
        for link in part_links[:5]:  # Limit to 5 parts
            part_text = link.get_text().strip()
            part_url = link.get('href', '')
            if part_text and 'PS' in part_url:
                related_parts.append({
                    'part_name': part_text,
                    'part_url': part_url if part_url.startswith('http') else 'https://www.partselect.com' + part_url
                })

        # Extract video embeds
        videos = []
        yt_iframes = soup.select('iframe[src*="youtube"], iframe[src*="youtu.be"]')
        for iframe in yt_iframes[:3]:
            video_url = iframe.get('src', '')
            if video_url:
                videos.append(video_url)

        # Extract meta description
        meta_desc = ''
        meta_elem = soup.select_one('meta[name="description"]')
        if meta_elem:
            meta_desc = meta_elem.get('content', '')

        # Build blog article data - only actual website metadata
        article_data = {
            'appliance_type': blog_info['appliance_type'],
            'title': title,
            'url': url,
            'author': author,
            'published_date': published_date,
            'reading_time': reading_time,
            'categories': ' | '.join(categories) if categories else '',
            'meta_description': meta_desc,
            'excerpt': blog_info['excerpt'],
            'content': content,
            'content_length': len(content),
            'featured_image': featured_image,
            'images': ' | '.join(images) if images else '',
            'image_count': len(images),
            'related_parts': json.dumps(related_parts) if related_parts else '',
            'related_parts_count': len(related_parts),
            'video_urls': ' | '.join(videos) if videos else '',
            'video_count': len(videos),
            'topic_source': blog_info['topic_url'],
            'scraped_at': pd.Timestamp.now().isoformat()
        }

        driver.quit()
        return article_data

    except Exception as e:
        print(f"   ⚠️  Error scraping {url}: {e}")
        driver.quit()
        return None

# Step 1: Get all blog article URLs from all topics
all_blog_urls = []
for topic_url in BLOG_TOPICS:
    urls = scrape_blog_topic_urls(topic_url)
    all_blog_urls.extend(urls)

# Remove duplicates
seen_urls = set()
unique_blog_urls = []
for blog in all_blog_urls:
    if blog['url'] not in seen_urls:
        seen_urls.add(blog['url'])
        unique_blog_urls.append(blog)

print(f"\n📊 Total blog articles to scrape: {len(unique_blog_urls)}")
print(f"   - Refrigerator blogs: {len([b for b in unique_blog_urls if b['appliance_type'] == 'refrigerator'])}")
print(f"   - Dishwasher blogs: {len([b for b in unique_blog_urls if b['appliance_type'] == 'dishwasher'])}")

# Step 2: Scrape each blog article in parallel
print(f"\n⚡ Scraping blog article details with Selenium + BeautifulSoup...")
blog_articles = []

with ThreadPoolExecutor(max_workers=3) as executor:
    futures = {
        executor.submit(scrape_blog_article, blog_info): blog_info
        for blog_info in unique_blog_urls
    }

    for future in tqdm(as_completed(futures), total=len(futures), desc="Scraping blogs"):
        result = future.result()
        if result:
            blog_articles.append(result)

# Step 3: Save to JSON - only 2 files for blogs
print(f"\n💾 Saving {len(blog_articles)} blog articles...")

# Create output directory
output_dir = Path('data/rag_documents')
output_dir.mkdir(parents=True, exist_ok=True)

# Save separate files for each appliance type
refrigerator_blogs = [b for b in blog_articles if b['appliance_type'] == 'refrigerator']
dishwasher_blogs = [b for b in blog_articles if b['appliance_type'] == 'dishwasher']

with open(output_dir / 'refrigerator_blogs.json', 'w', encoding='utf-8') as f:
    json.dump(refrigerator_blogs, f, indent=2, ensure_ascii=False)

with open(output_dir / 'dishwasher_blogs.json', 'w', encoding='utf-8') as f:
    json.dump(dishwasher_blogs, f, indent=2, ensure_ascii=False)

print(f"\n{'='*60}")
print(f"✅ BLOG ARTICLES SCRAPING COMPLETE!")
print(f"{'='*60}")
print(f"   Total articles scraped: {len(blog_articles)}")
print(f"   - Refrigerator blogs: {len(refrigerator_blogs)}")
print(f"   - Dishwasher blogs: {len(dishwasher_blogs)}")
print(f"\n   Saved to: data/rag_documents/")
print(f"   - {output_dir / 'refrigerator_blogs.json'}")
print(f"   - {output_dir / 'dishwasher_blogs.json'}")
print(f"\n   Metadata extracted (from website):")
print(f"   ✓ Title, author, published date")
print(f"   ✓ Categories and meta description")
print(f"   ✓ Full article content")
print(f"   ✓ Featured images")
print(f"   ✓ Related parts mentioned")
print(f"   ✓ Video embeds")
print(f"{'='*60}")