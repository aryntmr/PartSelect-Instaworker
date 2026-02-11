"""Test database queries to verify everything works."""

from queries import (
    find_parts_by_model,
    find_parts_by_symptom,
    find_parts_by_name_or_number,
    get_discounted_parts,
    get_top_rated_parts,
    get_database_stats
)

print("=" * 60)
print("🧪 Testing Database Queries")
print("=" * 60)

# Test 1: Database Statistics
print("\n1️⃣  DATABASE STATISTICS")
print("-" * 60)
stats = get_database_stats()
print(f"   Total Parts: {stats.get('total_parts', 0)}")
print(f"   Total Models: {stats.get('total_models', 0)}")
print(f"   Total Mappings: {stats.get('total_mappings', 0)}")
print(f"   Discounted Parts: {stats.get('discounted_parts', 0)}")
print(f"   Parts with Videos: {stats.get('parts_with_videos', 0)}")
print(f"   Average Rating: {stats.get('avg_rating', 0):.2f}/5.0")
print(f"   Average Price: ${stats.get('avg_price', 0):.2f}")

# Test 2: Find Parts by Model Number
print("\n2️⃣  FIND PARTS BY MODEL NUMBER")
print("-" * 60)
test_models = ['WDT780SAEM1', 'RF28R7351SR', 'GNE27JSMSS']
for model in test_models:
    parts = find_parts_by_model(model)
    print(f"   Model {model}: {len(parts)} compatible parts")
    if parts:
        print(f"      Example: {parts[0]['part_name']} - ${parts[0]['current_price']}")

# Test 3: Find Parts by Symptom
print("\n3️⃣  FIND PARTS BY SYMPTOM")
print("-" * 60)
symptoms = ['ice maker', 'not washing', 'door shelf']
for symptom in symptoms:
    parts = find_parts_by_symptom(symptom, limit=3)
    print(f"   Symptom '{symptom}': {len(parts)} parts found")
    for part in parts[:2]:
        print(f"      - {part['part_name']}: ${part['current_price']} (⭐ {part['rating']}/5.0)")

# Test 4: Search by Name/Number
print("\n4️⃣  SEARCH BY PART NAME")
print("-" * 60)
search_terms = ['door shelf', 'heating element', 'spray arm']
for term in search_terms:
    parts = find_parts_by_name_or_number(term, limit=3)
    print(f"   Search '{term}': {len(parts)} results")
    if parts:
        print(f"      Top result: {parts[0]['part_name']} - ${parts[0]['current_price']}")

# Test 5: Get Discounted Parts
print("\n5️⃣  DISCOUNTED PARTS (DEALS)")
print("-" * 60)
deals = get_discounted_parts(min_discount=10)
print(f"   Found {len(deals)} parts with 10%+ discount\n")
for deal in deals[:5]:
    savings = deal['original_price'] - deal['current_price']
    print(f"   - {deal['part_name'][:50]}")
    print(f"     Was: ${deal['original_price']:.2f} → Now: ${deal['current_price']:.2f}")
    print(f"     Save: ${savings:.2f} ({deal['discount_percentage']:.0f}% OFF)\n")

# Test 6: Get Top-Rated Parts
print("\n6️⃣  TOP-RATED PARTS")
print("-" * 60)
top_parts = get_top_rated_parts(min_reviews=100, limit=5)
print(f"   Found {len(top_parts)} parts with 100+ reviews\n")
for part in top_parts:
    print(f"   - {part['part_name'][:50]}")
    print(f"     ⭐ {part['rating']:.2f}/5.0 ({part['review_count']} reviews) - ${part['current_price']:.2f}\n")

# Test 7: Complex Query - Affordable Parts with Good Ratings
print("\n7️⃣  BEST VALUE (High Rating + Low Price)")
print("-" * 60)
top = get_top_rated_parts(min_reviews=50, limit=20)
affordable = [p for p in top if p['current_price'] < 50]
print(f"   Found {len(affordable)} highly-rated parts under $50\n")
for part in affordable[:3]:
    print(f"   - {part['part_name'][:50]}")
    print(f"     ⭐ {part['rating']:.2f}/5.0 | ${part['current_price']:.2f}\n")

print("=" * 60)
print("✅ ALL QUERIES EXECUTED SUCCESSFULLY!")
print("=" * 60)
