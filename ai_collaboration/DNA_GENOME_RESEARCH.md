# DNA & Genome Analysis for Orchid Research
**Research Document - October 21, 2025**

## 🧬 CONCEPT: Gene-Trait Correlation Analysis

### Vision
Correlate morphological traits (flower color, spur length, etc.) with genetic sequences to discover gene-trait associations in orchids.

---

## 📊 Available DNA/Genome Databases (FREE APIs)

### 1. **NCBI GenBank** ⭐ PRIMARY CHOICE
**URL**: https://www.ncbi.nlm.nih.gov/genbank/
**API**: NCBI E-utilities (Entrez Programming Utilities)
**Cost**: FREE (no API key required for small-scale use)

**What It Has**:
- Complete genome sequences
- Gene sequences (DNA, RNA)
- Protein sequences
- Species-specific genetic data
- Orchid genome projects

**API Endpoints**:
```
Search: https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi
Fetch: https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi
Summary: https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi
```

**Example Query** (search for Phalaenopsis DNA):
```
https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=nuccore&term=Phalaenopsis[Organism]+AND+complete+genome
```

**Usage Limits**: 
- 3 requests/second without API key
- 10 requests/second WITH API key (free to obtain)

### 2. **BOLD Systems** (Barcode of Life Data System)
**URL**: http://www.boldsystems.org/
**API**: Public Data Portal API
**Cost**: FREE

**What It Has**:
- DNA barcoding sequences (COI, matK, rbcL)
- Species identification barcodes
- Geographic data linked to sequences
- Orchid-specific barcoding projects

**API Endpoints**:
```
Specimen Data: http://www.boldsystems.org/index.php/API_Public/specimen
Sequence Data: http://www.boldsystems.org/index.php/API_Public/sequence
Taxonomy: http://www.boldsystems.org/index.php/API_Public/taxonomy
```

**Example Query** (get Orchidaceae barcodes):
```
http://www.boldsystems.org/index.php/API_Public/specimen?taxon=Orchidaceae&format=json
```

### 3. **European Nucleotide Archive (ENA)**
**URL**: https://www.ebi.ac.uk/ena
**API**: ENA Browser API
**Cost**: FREE

**What It Has**:
- Comprehensive nucleotide sequences
- Raw sequencing data
- Assembled genomes
- Metagenomics data

**API Endpoint**:
```
https://www.ebi.ac.uk/ena/browser/api/
```

### 4. **Orchid-Specific Genome Projects**
- **Phalaenopsis equestris** (complete genome sequenced)
- **Dendrobium catenatum** (genome available)
- **Apostasia shenzhenica** (early-diverging orchid genome)
- **Vanilla planifolia** (genome project)

---

## 🎯 Gene-Trait Associations to Explore

### Color Genetics
**Traits to Correlate**:
- Flower color (red, purple, yellow, white)
- Pigment types (anthocyanins, carotenoids, betalains)

**Target Genes**:
- **DFR** (Dihydroflavonol 4-reductase) - anthocyanin synthesis
- **F3H** (Flavanone 3-hydroxylase) - flower color pathway
- **CHS** (Chalcone synthase) - pigment production
- **PAL** (Phenylalanine ammonia-lyase) - phenylpropanoid pathway

### Morphological Traits
**Spur Length** (pollinator adaptation):
- Growth regulatory genes
- Cell elongation genes
- Development timing genes

**Fragrance Production**:
- Terpene synthase genes
- Volatile compound biosynthesis
- Scent-related genes

**Flower Size**:
- Cell division genes
- Organ size regulators
- Growth hormone pathways

### Environmental Adaptation
**Epiphytic Adaptation**:
- Water retention genes
- CAM photosynthesis genes (drought tolerance)
- Velamen root development genes

**Mycorrhizal Associations**:
- Symbiosis genes
- Nutrient acquisition genes

---

## 💾 Database Schema Design

### New Table: `orchid_genome_data`

```sql
CREATE TABLE orchid_genome_data (
    id SERIAL PRIMARY KEY,
    taxonomy_id INTEGER REFERENCES orchid_taxonomy(id),
    genbank_accession VARCHAR(50),
    sequence_type VARCHAR(50), -- 'complete_genome', 'gene', 'barcode', 'chloroplast'
    gene_name VARCHAR(100), -- e.g., 'DFR', 'CHS', 'matK'
    sequence_data TEXT, -- DNA sequence (can be very long)
    sequence_length INTEGER,
    ncbi_url TEXT,
    bold_process_id VARCHAR(50),
    source_database VARCHAR(50), -- 'NCBI', 'BOLD', 'ENA'
    geographic_origin VARCHAR(255),
    specimen_voucher VARCHAR(255),
    collection_date DATE,
    imported_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB -- additional data (protein sequences, annotations, etc.)
);

CREATE INDEX idx_genome_taxonomy ON orchid_genome_data(taxonomy_id);
CREATE INDEX idx_genome_gene ON orchid_genome_data(gene_name);
CREATE INDEX idx_genome_accession ON orchid_genome_data(genbank_accession);
```

### New Table: `gene_trait_correlations`

```sql
CREATE TABLE gene_trait_correlations (
    id SERIAL PRIMARY KEY,
    gene_name VARCHAR(100),
    trait_name VARCHAR(255),
    correlation_type VARCHAR(100), -- 'color', 'morphology', 'fragrance', 'adaptation'
    correlation_strength DECIMAL(3,2), -- 0.00 to 1.00
    sample_size INTEGER,
    statistical_method VARCHAR(100),
    p_value DECIMAL(10,8),
    discovery_method VARCHAR(100), -- 'julius_ai_analysis', 'literature', 'experimental'
    reference_url TEXT,
    notes TEXT,
    discovered_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_gene_trait_gene ON gene_trait_correlations(gene_name);
CREATE INDEX idx_gene_trait_trait ON gene_trait_correlations(trait_name);
```

---

## 🔬 Analysis Workflow

### Phase 1: Data Collection
1. **Extract species names** from orchid_taxonomy (35,320 species)
2. **Query NCBI GenBank** for each species:
   - Complete genomes (if available)
   - Chloroplast genes (matK, rbcL)
   - Color genes (DFR, CHS, F3H)
   - Fragrance genes (terpene synthases)
3. **Query BOLD Systems** for DNA barcodes
4. **Store sequences** in orchid_genome_data table

### Phase 2: Julius AI Analysis
**Julius's Tasks**:
1. **Sequence Alignment**: Compare similar genes across species
2. **Mutation Detection**: Identify SNPs and structural variants
3. **Pattern Recognition**: Find correlations between:
   - Gene variants ↔ Flower color (from TraitBank/images)
   - Gene expression ↔ Morphology (spur length, petal size)
   - Genetic distance ↔ Geographic distribution
4. **Phylogenetic Analysis**: Build evolutionary trees
5. **Gene-Trait Mapping**: Associate specific mutations with traits

### Phase 3: Correlation Discovery
**Example Analysis**:
```
Question: "Do red-flowered orchids share specific DFR gene variants?"

Method:
1. Extract DFR gene sequences for 100 species
2. Extract flower color from TraitBank (78,225 traits)
3. Align sequences, identify variants
4. Statistical correlation: DFR variant → red color
5. Map geographic distribution of variant
```

---

## 🚀 Implementation Plan

### Step 1: Get NCBI API Key (Optional but Recommended)
**Why**: Increases rate limit from 3 to 10 requests/second
**How**: 
1. Create free NCBI account
2. Generate API key at: https://www.ncbi.nlm.nih.gov/account/settings/
3. Store in Replit Secrets as `NCBI_API_KEY`

**Cost**: FREE

### Step 2: Build Data Collection Script
**File**: `validation/enrich_genome_data.py`

Features:
- Query NCBI for orchid genome sequences
- Query BOLD for DNA barcodes
- Store in orchid_genome_data table
- Rate limiting (respect API limits)
- Progress tracking

### Step 3: Julius AI Analysis
**Julius analyzes**:
- DNA sequences for pattern recognition
- Gene-trait correlations
- Phylogenetic relationships
- Novel genetic associations

**Output**: gene_trait_correlations table

### Step 4: Visualization & Discovery
- Map gene variants geographically
- Correlate with climate data
- Link to pollinator syndromes
- Identify convergent evolution

---

## 📈 Expected Outcomes

### Scientific Discoveries
- **Gene-Color Associations**: "Red orchids have specific DFR mutation X"
- **Adaptation Patterns**: "High-altitude orchids share CAM genes"
- **Pollinator Genetics**: "Long-spurred species have common growth genes"
- **Geographic Genetics**: "Madagascar orchids cluster genetically"

### Research Value
- Publishable gene-trait correlations
- Evolutionary insights
- Conservation genetics
- Breeding applications

---

## 💰 Cost Analysis

**All databases FREE**:
- NCBI GenBank: FREE ✅
- BOLD Systems: FREE ✅
- ENA: FREE ✅

**Only cost**: Julius AI computation time
- Sequence analysis: ~$50-100 for 10K sequences
- Pattern recognition: Included in Vision AI budget

**Total Additional Cost**: ~$50-100 (within approved budget)

---

## ✅ RECOMMENDATION

**START WITH**:
1. Get NCBI API key (free, 5 minutes)
2. Query 100 test species for genome data
3. Julius analyzes sequences for patterns
4. Correlate with existing 78K traits
5. Publish pilot findings

**This adds a THIRD dimension to our analysis**:
- Dimension 1: Morphology (Vision AI on images)
- Dimension 2: Geography (GPS coordinates)
- Dimension 3: Genetics (DNA sequences) ← NEW!

**Julius can analyze DNA sequences just as easily as images!** 🧬

---

**Next Steps**: 
1. Ask user to get NCBI API key (or I can guide them)
2. Build genome data collection script
3. Julius analyzes sequences
4. Discover gene-trait correlations!
