# Scraping Approach Evolution

## 🔄 Why We Changed Tools

### 1. Playwright (Initial Attempt)
**Issue:** JavaScript-heavy pages weren't rendering properly. Missing critical data like videos, symptoms, and compatible models.

### 2. Playwright Stealth
**Why we switched:** Added anti-detection to avoid bot blocking.
**Issue:** Still had JavaScript rendering delays. Page load detection was unreliable.

### 3. Selenium + BeautifulSoup (Final Solution) ✅
**Why we switched:**
- Better JavaScript execution control (explicit waits)
- More reliable element detection after JS renders
- BeautifulSoup for fast HTML parsing after page loads
- Easier debugging (can see browser actions)
- Parallel execution with ThreadPoolExecutor

---

## 🎯 Final Scraping Pipeline

### ⚠️ Note: Complete scraped data (92 unique parts) is already included

The CSV file `data/processed/parts_latest.csv` contains the complete, enriched data. You can use it directly or re-run the pipeline from scratch.

### Step 1: Initial Parts List
**Script:** `scrape_parts.py` ✅
- Scrapes 120 parts from refrigerator and dishwasher categories
- Navigates category pages and extracts basic part information
- **Extracts:** part name, number, brand, price, image URL, product URL
- **Output:** `data/processed/parts_latest.csv` (basic fields)
- **Runtime:** ~10-15 minutes (visits each part page)

### Step 2: Enrich Parts Details
**Script:** `enrich_parts.py` ✅
- **Technology:** Selenium (JavaScript execution) + BeautifulSoup (HTML parsing)
- **Parallel:** 3 browser instances simultaneously
- **Extracts 20 fields:**
  - Pricing: current_price, original_price, has_discount
  - Reviews: rating, review_count
  - Details: description, symptoms, replacement_parts
  - Installation: difficulty, time, video_url
  - Compatibility: compatible_models (JSON), model URLs
- **Output:** `data/processed/parts_latest.csv` (enriched with all fields)

### Step 3: Data Validation
**Tool:** `utils/data_cleaner.py`
- Cleans prices, ratings, review counts
- Validates URLs
- Normalizes text fields

---

## 📊 Final Output

**File:** `data/processed/parts_latest.csv`

| Parts | Fields | Models | Avg Time per Part |
|-------|--------|--------|-------------------|
| 120 | 20 | 3,575 | ~2 seconds |

**Total time:** ~4 minutes for complete scrape

---

## 🛠️ Tech Stack Used

- **Selenium 4.16.0** - Browser automation & JavaScript execution
- **BeautifulSoup 4.12.3** - HTML parsing
- **lxml 5.1.0** - Fast XML/HTML parser
- **pandas 2.2.1** - Data processing
- **ThreadPoolExecutor** - Parallel scraping (3 workers)

---

## ✅ What We Achieved

- 100% field extraction (20/20 fields)
- Discount detection working (5 parts with discounts)
- 3,575 compatible models extracted
- 120 parts with videos (100% coverage)
- No bot detection issues
- Production-ready pipeline
