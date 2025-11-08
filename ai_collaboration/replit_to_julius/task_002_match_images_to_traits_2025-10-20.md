# 🎯 Task 002: Match EOL Images to Orchid Traits

**Date:** October 20, 2025  
**Assigned To:** Julius AI  
**Priority:** HIGH  
**Status:** PENDING (Awaits Task 001 completion)  
**Expected Duration:** 10-15 minutes  

---

## 📋 Objective

Match EOL orchid images to their trait data using `page_id` as the linking key. This creates a complete dataset with both visual and phenotypic information for each species.

---

## 📥 Input Data

### **From Task 001 (Your Previous Work):**
- `task_001_response_orchid_traits.csv` - Orchid traits with page_id

### **From Orchid Continuum Database:**
Replit Agent will provide you with:
- `eol_images_export.csv` - 95,000+ EOL images with page_id, eol_url, license, copyright

---

## 🔍 Task Steps

### **STEP 1: Load Both Datasets**

```python
import pandas as pd

# Load your trait data from Task 001
traits = pd.read_csv('task_001_response_orchid_traits.csv')
print(f"Loaded {len(traits):,} trait records")
print(f"Unique species in traits: {traits['page_id'].nunique():,}")

# Load EOL images (Replit Agent will provide this)
images = pd.read_csv('eol_images_export.csv')
print(f"Loaded {len(images):,} image records")
print(f"Unique species with images: {images['page_id'].nunique():,}")
```

---

### **STEP 2: Match Images to Traits**

```python
# Inner join: species with BOTH images AND traits
matched = pd.merge(
    images,
    traits,
    on='page_id',
    how='inner',
    suffixes=('_image', '_trait')
)

print(f"\n✅ MATCHED DATA:")
print(f"  Total records: {len(matched):,}")
print(f"  Unique species with both: {matched['page_id'].nunique():,}")
print(f"  Total images involved: {matched['eol_url'].nunique():,}")
print(f"  Total trait types: {matched['trait_name'].nunique():,}")

# Show sample
print(f"\nSample matched record:")
print(matched.head(1).T)
```

---

### **STEP 3: Calculate Coverage Statistics**

```python
# Species with images only (no traits)
images_only = images[~images['page_id'].isin(traits['page_id'])]
print(f"\n📊 COVERAGE ANALYSIS:")
print(f"  Species with images only: {images_only['page_id'].nunique():,}")

# Species with traits only (no images)
traits_only = traits[~traits['page_id'].isin(images['page_id'])]
print(f"  Species with traits only: {traits_only['page_id'].nunique():,}")

# Species with both
both = matched['page_id'].nunique()
print(f"  Species with BOTH: {both:,}")

# Calculate percentages
total_species = pd.concat([
    images['page_id'],
    traits['page_id']
]).nunique()

print(f"\n  Total unique species: {total_species:,}")
print(f"  Coverage rate: {both / total_species * 100:.1f}%")
```

**Save to:** `task_002_response_coverage_stats.txt`

---

### **STEP 4: Create Matched Export**

```python
# Clean matched data for database import
matched_export = matched[[
    'page_id',
    'scientific_name',
    'eol_url',
    'license',
    'copyright',
    'source_url',
    'trait_name',
    'trait_value',
    'trait_unit'
]].copy()

# Remove duplicates
matched_export = matched_export.drop_duplicates()

print(f"\n📤 EXPORT READY:")
print(f"  Total rows: {len(matched_export):,}")
print(f"  File size estimate: {len(matched_export) * 200 / 1024 / 1024:.1f} MB")

matched_export.to_csv('task_002_response_matched_images_traits.csv', index=False)
print("✅ Saved: task_002_response_matched_images_traits.csv")
```

**CRITICAL: Save as:** `task_002_response_matched_images_traits.csv`

---

### **STEP 5: Identify Data Gaps**

```python
# Species needing more images (have traits but few/no images)
species_needs_images = (
    traits_only.groupby(['page_id', 'scientific_name'])
    .size()
    .reset_index(name='trait_count')
    .sort_values('trait_count', ascending=False)
)

print(f"\n🔍 PRIORITY: Species needing images")
print(f"  Total species: {len(species_needs_images):,}")
print(f"\nTop 50 species by trait coverage (but no images):")
print(species_needs_images.head(50))

species_needs_images.to_csv('task_002_response_needs_images.csv', index=False)
print("✅ Saved: task_002_response_needs_images.csv")

# Species needing more traits (have images but few/no traits)
species_needs_traits = (
    images_only.groupby(['page_id'])
    .size()
    .reset_index(name='image_count')
    .sort_values('image_count', ascending=False)
)

print(f"\n🔍 OPPORTUNITY: Species needing traits")
print(f"  Total species: {len(species_needs_traits):,}")

species_needs_traits.to_csv('task_002_response_needs_traits.csv', index=False)
print("✅ Saved: task_002_response_needs_traits.csv")
```

**Save as:** 
- `task_002_response_needs_images.csv`
- `task_002_response_needs_traits.csv`

---

### **STEP 6: Create Priority List for Next Collection**

```python
# Top 100 high-value species to prioritize for more data
# Criteria: Have some data, but could use more

priority = matched.groupby(['page_id', 'scientific_name']).agg({
    'eol_url': 'nunique',  # Image count
    'trait_name': 'nunique'  # Trait type count
}).reset_index()

priority.columns = ['page_id', 'scientific_name', 'image_count', 'trait_count']
priority['completeness_score'] = priority['image_count'] * priority['trait_count']

# Sort by potential (species with moderate coverage that could be improved)
priority = priority[
    (priority['image_count'] >= 1) & (priority['image_count'] < 50) &
    (priority['trait_count'] >= 5) & (priority['trait_count'] < 20)
].sort_values('completeness_score', ascending=False)

print(f"\n🎯 PRIORITY COLLECTION LIST:")
print(f"  Species to prioritize: {len(priority):,}")
print(priority.head(100))

priority.head(100).to_csv('task_002_response_priority_collection.csv', index=False)
print("✅ Saved: task_002_response_priority_collection.csv")
```

**Save as:** `task_002_response_priority_collection.csv`

---

## 📤 Expected Outputs

Please generate these **6 files**:

1. ✅ `task_002_response_matched_images_traits.csv` - Main matched dataset
2. ✅ `task_002_response_coverage_stats.txt` - Statistics summary
3. ✅ `task_002_response_needs_images.csv` - Species needing more images
4. ✅ `task_002_response_needs_traits.csv` - Species needing trait data
5. ✅ `task_002_response_priority_collection.csv` - Top 100 species to prioritize
6. ✅ `task_002_response_report.txt` - Full processing report

---

## ✅ Success Criteria

- [ ] All 6 output files generated
- [ ] At least 500 species with both images AND traits
- [ ] Matched dataset links page_id correctly
- [ ] Priority list identifies actionable targets
- [ ] Gap analysis shows where to focus next data collection

---

## 🔄 Next Task Preview

After completion, Replit Agent will:
1. Import matched data to database
2. Create visualizations of coverage
3. Generate **Task 003**: Automated collection for priority species

---

**Awaiting Task 001 completion. Stand by!** 🚀
