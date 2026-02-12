# PartSelect Instaworker - Project Overview

## About
AI chatbot for PartSelect e-commerce assisting customers with refrigerator & dishwasher parts - helping with product search, compatibility checks, installation guidance, and troubleshooting.

## Assessment Goal
Build a scoped chat agent (from [Assesment.rtf](../Assesment.rtf)) focused on user experience, extensibility, and accurate query handling for refrigerator/dishwasher parts only.

---

## 📁 File Structure

### `/backend` - FastAPI Server (Port 8000)
- `app.py` - Application entry point with CORS-enabled FastAPI server
- `config.py` - Environment configuration loader
- `test_backend.py` - Comprehensive API test suite
- `models/` - Pydantic schemas for chat, parts, and responses
- `routes/` - API endpoints (health, chat, parts)
- `services/` - Business logic (database operations, search service)

### `/frontend` - React UI (Port 3000)
- `src/App.js` - Main chat interface component
- `src/components/` - Reusable UI components (ChatMessage, PartCard, etc.)
- `src/api/` - API client for backend communication

### `/database` - PostgreSQL Setup
- `schema.sql` - Table definitions with indexes and triggers
- `load_data.py` - ETL script to load CSV data into PostgreSQL
- `queries.py` - 9 pre-built query functions for common searches
- `test_queries.py` - Database query validation tests

### `/scraping` - Data Collection Pipeline
- `scrape_parts.py` - Initial scraper for basic part listings (120 parts)
- `enrich_parts.py` - Selenium + BeautifulSoup enrichment (20+ fields per part)
- `scrape_repairs.py` - Symptom and repair guide scraper
- `scrape_blogs.py` - Educational content scraper
- `data/processed/` - Output CSV files with scraped data

---

## 🚀 Core Features

1. **Natural Language Search** - Find parts by symptoms, model numbers, or part names
2. **Smart Compatibility Checks** - Verify part compatibility with specific appliance models
3. **Installation Guidance** - Provide difficulty ratings, time estimates, and video links
4. **Deal Detection** - Highlight discounted parts with savings percentages
5. **Multi-Part Comparison** - Display multiple matching parts with ratings/reviews

---

## 🗄️ Database (PostgreSQL)

**Tables:**
- `parts` (92 unique parts) - Product catalog with pricing, ratings, symptoms, installation data
- `models` (1,845 models) - Compatible appliance model numbers
- `part_models` (2,735 mappings) - Part-to-model compatibility relationships

**Key Features:** Full-text search indexes, automatic timestamp triggers, optimized for symptom/model/brand queries

---

## 🔌 Backend APIs

**Base URL:** `http://localhost:8000`

- `GET /health` - Health check with database status
- `POST /api/chat` - Main search endpoint (body: `{"message": "search query"}`)
- `GET /api/parts/{part_id}` - Get detailed part information

**Technology:** FastAPI + Uvicorn (ASGI), psycopg2 for PostgreSQL, Pydantic validation

---

## 🕷️ Scraping Pipeline

**Evolution:** Playwright → Playwright Stealth → Selenium + BeautifulSoup (final)

**Process:**
1. **Scrape Parts List** - Navigate category pages, extract 120 parts (refrigerator/dishwasher)
2. **Enrich Details** - Parallel Selenium scraping (3 browsers) to extract 20+ fields per part
3. **Data Cleaning** - Remove duplicates (92 unique parts), normalize prices, validate URLs
4. **Load to DB** - ETL pipeline loads processed CSV into PostgreSQL

**Extracted Fields:** Part numbers, pricing, discounts, ratings, reviews, symptoms, compatible models, installation difficulty/time, videos, images, descriptions

**Runtime:** ~15-20 minutes for complete pipeline | **Output:** Pre-scraped data in `data/processed/parts_latest.csv`
