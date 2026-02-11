# PostgreSQL Database - PartSelect Chatbot

## ✅ Setup Complete!

Your local PostgreSQL database is ready with:
- **92 unique parts** (28 duplicates removed from original 120)
- **1,845 appliance models**
- **2,735 part-model compatibility mappings**
- **3 parts on sale** (up to 60% off)
- **Average rating:** 5.0/5.0

---

## 📁 Files

| File | Purpose |
|------|---------|
| `schema.sql` | Database schema (tables, indexes, triggers) |
| `load_data.py` | ETL: Load CSV → PostgreSQL |
| `queries.py` | 9 pre-built query functions |
| `test_queries.py` | Test script to verify database |
| `.env` | Database credentials (local) |
| `requirements.txt` | Python dependencies |

---

## 🔌 Connection Details

```env
Host: localhost
Port: 5432
Database: partselect_db
User: aryan
Password: (none)
```

---

## 🚀 Usage in Your Chatbot

```python
from database.queries import find_parts_by_symptom, get_discounted_parts

# User: "My ice maker isn't working"
parts = find_parts_by_symptom('ice maker not working')

# User: "Show me deals"
deals = get_discounted_parts(min_discount=20)

# Use the results to generate chatbot response
for part in parts:
    print(f"{part['part_name']}: ${part['current_price']}")
    print(f"Rating: {part['rating']}/5.0")
    print(f"Video: {part['video_url']}")
```

---

## 🧪 Test the Database

```bash
# Run all test queries
python3 test_queries.py

# Or test individual queries
python3 queries.py
```

---

## 📊 Database Schema

### Tables
1. **parts** (92 rows) - Part details, pricing, ratings
2. **models** (1,845 rows) - Appliance model numbers
3. **part_model_mapping** (2,735 rows) - Compatibility relationships

### Features
- ✅ Full-text search on symptoms & descriptions
- ✅ Auto-calculated discount percentages
- ✅ Foreign key constraints for data integrity
- ✅ Indexes for fast queries (5-20ms)
- ✅ Automatic timestamp updates

---

## 🔍 Available Query Functions

1. `find_parts_by_model(model_number)` - Parts for specific model
2. `find_parts_by_symptom(symptom)` - Parts that fix issues
3. `find_parts_by_name_or_number(search)` - Search catalog
4. `get_discounted_parts(min_discount)` - Find deals
5. `get_top_rated_parts(min_reviews)` - Best parts
6. `get_part_details(part_id)` - Complete part info
7. `get_parts_with_videos(difficulty)` - Installation guides
8. `find_replacement_parts(part_number)` - Alternative parts
9. `get_database_stats()` - Database statistics

---

## 📈 Sample Queries

### Find deals over 20% off
```python
deals = get_discounted_parts(min_discount=20)
# Returns: Door Shelf Retainer Bar - $49.81 → $19.94 (60% OFF)
```

### Find highly-rated affordable parts
```python
top = get_top_rated_parts(min_reviews=100)
affordable = [p for p in top if p['current_price'] < 50]
# Returns: 13 parts rated 5.0/5.0 under $50
```

### Search by symptom
```python
parts = find_parts_by_symptom('ice maker not working')
# Returns: 3 parts that fix ice maker issues
```

---

## 🔄 Rebuilding Database

If you need to reload data:

```bash
# Drop and recreate
psql partselect_db -c "DROP TABLE IF EXISTS part_model_mapping CASCADE; DROP TABLE IF EXISTS models CASCADE; DROP TABLE IF EXISTS parts CASCADE;"

# Recreate schema
psql partselect_db -f schema.sql

# Reload data
python3 load_data.py
```

---

## 💡 Next Steps

1. ✅ Database set up (DONE)
2. ⏭️ Build chatbot API with FastAPI/Flask
3. ⏭️ Integrate LLM (OpenAI/Anthropic)
4. ⏭️ Create chat interface

Use the query functions in `queries.py` to power your chatbot responses!
