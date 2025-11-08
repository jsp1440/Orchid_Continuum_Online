# 🎯 Task 001: Extract Orchid Traits from TraitBank

**Date:** October 20, 2025  
**Assigned To:** Julius AI  
**Priority:** HIGH  
**Expected Duration:** 10-15 minutes  

---

## 📋 Objective

Extract all orchid (Orchidaceae family) trait data from the uploaded TraitBank dataset and prepare it for import into the Orchid Continuum database.

---

## 📥 Input Data

You have a TraitBank ZIP file uploaded containing:
- `pages.csv` - Species taxonomy (page_id, scientific names, families)
- `traits.csv` - Trait measurements and values
- `metadata.csv` - Data provenance and sources
- `terms.csv` - Trait definitions
- `term_parents.csv` - Trait ontology

---

## 🔍 Task Steps

### **STEP 1: Load and Inspect Data**

Load all CSV files from the TraitBank ZIP and run:

```python
# Show structure
for file in ['pages.csv', 'traits.csv', 'metadata.csv']:
    df = pd.read_csv(file)
    print(f"\n{file}:")
    print(f"  Rows: {len(df):,}")
    print(f"  Columns: {list(df.columns)}")
    print(f"  Sample:\n{df.head(3)}")
```

**Save output to:** `task_001_response_structure.txt`

---

### **STEP 2: Filter for Orchidaceae**

Extract only orchid family records:

```python
# Filter pages for Orchidaceae
orchid_pages = pages[pages['family'] == 'Orchidaceae']

print(f"Total orchid species found: {len(orchid_pages):,}")
print(f"Total unique page_ids: {orchid_pages['page_id'].nunique():,}")

# Show top genera
genera_counts = orchid_pages['canonical'].str.split(' ').str[0].value_counts()
print(f"\nTop 10 genera:\n{genera_counts.head(10)}")
```

**Save summary to:** `task_001_response_orchid_count.txt`

---

### **STEP 3: Extract All Orchid Traits**

Join orchid pages with their trait measurements:

```python
# Get all traits for orchid species
orchid_traits = pd.merge(
    orchid_pages[['page_id', 'canonical']],
    traits,
    on='page_id',
    how='inner'
)

print(f"Total trait records: {len(orchid_traits):,}")
print(f"Species with traits: {orchid_traits['page_id'].nunique():,}")

# Show trait distribution
trait_counts = orchid_traits['predicate'].value_counts()
print(f"\nTop 20 measured traits:\n{trait_counts.head(20)}")
```

**Save to:** `task_001_response_trait_distribution.txt`

---

### **STEP 4: Create Clean Export for Database**

Prepare a clean CSV for Replit Agent to import:

```python
# Select and rename columns for database import
export_df = orchid_traits[[
    'page_id',
    'canonical',  # This is scientific_name
    'predicate',  # This is trait_name
    'measurement',  # This is trait_value (if numeric)
    'literal',  # This is trait_description (if text)
    'units'  # This is trait_unit
]].copy()

# Rename columns to match database schema
export_df.columns = [
    'page_id',
    'scientific_name',
    'trait_name',
    'trait_value_numeric',
    'trait_value_text',
    'trait_unit'
]

# Combine numeric and text values into single trait_value column
export_df['trait_value'] = export_df['trait_value_numeric'].fillna(
    export_df['trait_value_text']
)

# Keep only needed columns
final_df = export_df[[
    'page_id',
    'scientific_name',
    'trait_name',
    'trait_value',
    'trait_unit'
]].copy()

# Remove duplicates
final_df = final_df.drop_duplicates()

# Clean data
final_df = final_df.dropna(subset=['page_id', 'scientific_name', 'trait_name'])

print(f"\nFinal export:")
print(f"  Total rows: {len(final_df):,}")
print(f"  Unique species: {final_df['page_id'].nunique():,}")
print(f"  Unique traits: {final_df['trait_name'].nunique():,}")
print(f"  Data completeness: {(1 - final_df.isnull().sum().sum() / final_df.size) * 100:.1f}%")

# Save to CSV
final_df.to_csv('task_001_response_orchid_traits.csv', index=False, encoding='utf-8')
print("\n✅ Exported: task_001_response_orchid_traits.csv")
```

**CRITICAL: Save as:** `task_001_response_orchid_traits.csv`

---

### **STEP 5: Generate Species Summary**

Create a per-species statistics file:

```python
# Calculate stats per species
species_summary = final_df.groupby(['page_id', 'scientific_name']).agg({
    'trait_name': 'count',  # Number of trait measurements
    'trait_value': lambda x: x.notna().sum()  # Number of non-null values
}).reset_index()

species_summary.columns = ['page_id', 'scientific_name', 'total_traits', 'filled_traits']
species_summary['completeness_percent'] = (
    species_summary['filled_traits'] / species_summary['total_traits'] * 100
).round(1)

# Sort by most complete
species_summary = species_summary.sort_values('total_traits', ascending=False)

print(f"\nTop 20 species by trait coverage:")
print(species_summary.head(20))

species_summary.to_csv('task_001_response_species_summary.csv', index=False)
print("\n✅ Exported: task_001_response_species_summary.csv")
```

**Save as:** `task_001_response_species_summary.csv`

---

### **STEP 6: Create Processing Report**

Write a summary report:

```python
report = f"""
# Task 001: Extract Orchid Traits - COMPLETION REPORT

**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Status:** COMPLETE ✅

## Summary Statistics

- **Total orchid species in TraitBank:** {orchid_pages['page_id'].nunique():,}
- **Species with trait data:** {final_df['page_id'].nunique():,}
- **Total trait measurements:** {len(final_df):,}
- **Unique trait types:** {final_df['trait_name'].nunique():,}
- **Data completeness:** {(1 - final_df.isnull().sum().sum() / final_df.size) * 100:.1f}%

## Top 10 Traits by Frequency

{final_df['trait_name'].value_counts().head(10).to_string()}

## Top 10 Genera

{genera_counts.head(10).to_string()}

## Output Files Generated

1. ✅ task_001_response_orchid_traits.csv ({len(final_df):,} rows)
2. ✅ task_001_response_species_summary.csv ({len(species_summary):,} rows)
3. ✅ task_001_response_processing_report.txt (this file)

## Next Steps for Replit Agent

1. Import task_001_response_orchid_traits.csv to database
2. Match page_id to existing EOL images (95,000 already in database)
3. Generate Task 002: Match images to traits

## Data Quality Notes

- page_id format: {final_df['page_id'].iloc[0] if len(final_df) > 0 else 'N/A'}
- Scientific names: Follow binomial nomenclature
- Trait values: Mix of numeric and text
- Units: Present for ~{final_df['trait_unit'].notna().sum() / len(final_df) * 100:.0f}% of records

**Task completed successfully! Ready for Replit Agent processing.**
"""

with open('task_001_response_processing_report.txt', 'w') as f:
    f.write(report)

print(report)
```

**Save as:** `task_001_response_processing_report.txt`

---

## 📤 Expected Outputs

Please generate these **3 files** and make them available for download:

1. ✅ `task_001_response_orchid_traits.csv` - Main dataset (estimated 500K-1M rows)
2. ✅ `task_001_response_species_summary.csv` - Per-species statistics
3. ✅ `task_001_response_processing_report.txt` - Summary report

---

## ✅ Success Criteria

- [ ] All 3 output files generated
- [ ] orchid_traits.csv has page_id, scientific_name, trait_name, trait_value, trait_unit
- [ ] No NULL page_id values
- [ ] At least 1,000 unique orchid species
- [ ] At least 100,000 trait measurements
- [ ] CSV files are UTF-8 encoded and ready for database import

---

## 🔄 Next Task Preview

After you complete this, Replit Agent will:
1. Import your CSV to the Orchid Continuum database
2. Match the page_ids to 95,000 existing EOL images
3. Generate **Task 002** to analyze the matched coverage

**Then we'll create Task 003 to extract more images for species with low coverage!**

---

## 💬 Response Format

When you've completed this task, please say:

```
Task 001 COMPLETE ✅

Generated files:
1. task_001_response_orchid_traits.csv (X,XXX rows)
2. task_001_response_species_summary.csv (X,XXX rows)
3. task_001_response_processing_report.txt

Summary:
- Extracted traits for X,XXX orchid species
- Total measurements: X,XXX
- Top 3 traits: [list them]

Ready for Replit Agent import!
```

---

**Let's go! Execute this task and let's accelerate this project! 🚀🌸**
