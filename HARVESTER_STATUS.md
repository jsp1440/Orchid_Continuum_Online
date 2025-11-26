# 🌺 Orchid Image Harvester - Current Status

**Last Updated:** Nov 26, 2025, 4:58 AM

## 📊 Database Coverage

| Metric | Value | Target | Progress |
|--------|-------|--------|----------|
| **Total Images** | 238,209 | 500,000+ | ▓▓░░░░░░░░ 48% |
| **Species Covered** | 10,841 / 35,327 | 28,261 (80%) | ▓▓░░░░░░░░ 31% |
| **Countries** | 458 | 250+ | ▓▓▓░░░░░░░ 183% |
| **Harvest Rate** | 216 img/min | Keep high | ✅ Optimal |

## 🏗️ Active Workers (19 Total)

### Primary Harvesters
- **12× GBIF Expanded** - ALL 247 countries → massive global coverage
- **2× iNaturalist** - Community research-grade observations
- **2× Tropicos** - Missouri Botanical Garden herbarium
- **1× iDigBio** - Digitized specimens fallback
- **1× API Coordinator** - Health monitoring + fallback routing

## 🔄 Fallback System

```
GBIF ────→ [Health Check] ───┐
              │ Healthy: ✅   │
              │ Failed: ❌    ↓
                           iNaturalist
                              │
                              ↓
                           Tropicos
                              │
                              ↓
                           iDigBio
```

All APIs monitored every 5 minutes. If any API fails, harvesting automatically routes to next source.

## 📈 Coverage by Source

| Source | Images | Species | Percent |
|--------|--------|---------|---------|
| GBIF | 140,008+ | 10,728+ | 30.4%+ |
| iNaturalist | 852+ | 63+ | 0.2%+ |
| Tropicos | 440+ | 92+ | 0.3%+ |
| iDigBio | 39+ | 27+ | 0.1%+ |
| EOL/BHL (Local) | 95,000 | Pending linking | - |

## 🎯 Path to 80% Coverage (28,261 species)

**Current:** 10,841 species (31%)  
**Needed:** 17,420 more species  

### Strategy
1. **Maximize GBIF coverage** - Expand country queries, optimize batch sizes
2. **Leverage all 4 APIs** - Parallel harvesting from multiple sources
3. **Link EOL/BHL taxonomy** - 95K images awaiting species matching
4. **Continuous 24/7 harvesting** - Reserved VM deployment required

### Estimated Timeline
- **At 216 img/min:** 2,332+ images/hour
- **To reach 80% species:** Need 45,000+ new images from untargeted species
- **Timeline:** ~20 hours of optimized harvesting

## 🚀 Next Steps

1. **Deploy to Reserved VM** - For true 24/7 operation
2. **Monitor API health** - Watch coordinator logs
3. **Optimize GBIF queries** - Per-genus country targeting
4. **Link EOL taxonomy** - Massive batch of 95K images pending

## 📝 Notes

- Harvesters auto-restart on crash
- Rate limiting: 300ms between GBIF requests
- Deduplication: All images checked before insert
- Metadata: Full occurrence data stored in JSON fields
