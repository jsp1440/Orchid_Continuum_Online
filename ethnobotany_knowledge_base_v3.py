"""
Enhanced Ethnobotany Knowledge Base v3.0
Research-grade traditional knowledge data for medicinal orchids
Primary Source: "Medicinal Orchids of Asia" by Dr. Eng Soon Teoh (Springer, 2016) - 753 pages
Additional Sources: Indigenous databases, traditional medicine records, ethnobotany research
"""

ETHNOBOTANY_DATABASE = {
    # EXISTING GENERA - Enhanced with academic research
    
    'Vanilla': {
        'traditional_uses': [
            'Food flavoring and perfume',
            'Traditional medicine for fever and digestive issues',
            'Aphrodisiac properties in traditional medicine',
            'Ritual and ceremonial uses'
        ],
        'indigenous_names': {
            'Totonac': 'xanat',
            'Nahuatl': 'tlilxochitl (black flower)',
            'Maya': 'sisbic',
            'Taino': 'vanilha'
        },
        'cultural_significance': 'Sacred to Totonac people of Mexico. Central to Aztec chocolate drinks (xocolatl) and religious ceremonies. Offered to gods as tribute.',
        'medicinal_uses': [
            'Digestive aid and stomach settler',
            'Aphrodisiac in Caribbean traditional medicine',
            'Fever reduction (Mesoamerican practice)',
            'Antiseptic properties'
        ],
        'regions': ['Mexico', 'Central America', 'Madagascar', 'Tahiti', 'Indonesia'],
        'conservation_notes': 'Over-harvesting threatens wild populations. Fair trade vanilla supports indigenous communities.',
        'modern_research': 'Vanillin compounds show antioxidant and anti-inflammatory properties (Journal of Agricultural and Food Chemistry, 2019). Teoh (2016) documents extensive use across continents.',
        'enrichment_source': 'ethnobotany_knowledge_base_v3',
        'enrichment_version': '3.0'
    },
    
    'Dendrobium': {
        'traditional_uses': [
            'Traditional Chinese Medicine (Shi Hu - 石斛)',
            'Food additive and herbal tea',
            'Anti-aging tonic',
            'Buddhist temple offerings',
            'Improve eyesight (D. fimbriatum)'
        ],
        'indigenous_names': {
            'Chinese': 'shi hu (石斛) - stone orchid',
            'Japanese': 'sekkoku',
            'Thai': 'ueang khao',
            'Vietnamese': 'thạch hộc'
        },
        'cultural_significance': 'One of 50 fundamental herbs in Traditional Chinese Medicine for over 2000 years. Featured in classical texts like "Shen Nong Ben Cao Jing" (Divine Farmer\'s Materia Medica). Over 250 orchid species used medicinally in China (Teoh, 2016).',
        'medicinal_uses': [
            'Immune system support (T-cell and macrophage immunity)',
            'Kidney and stomach health',
            'Anti-aging and longevity',
            'Yin nourishment in TCM theory',
            'Anti-inflammatory effects',
            'Liver disorders and nervous debility (Nepal)',
            'Eyesight improvement (D. fimbriatum)'
        ],
        'active_compounds': {
            'dendrobine alkaloids': 'neuroprotective effects',
            'polysaccharides': 'immunomodulatory activity, antioxidant, enhances superoxide dismutase (SOD)',
            'fimbriatone': 'from D. fimbriatum',
            'confusarin': 'from D. fimbriatum'
        },
        'regions': ['China', 'Japan', 'Southeast Asia', 'India', 'Australia', 'New Guinea', 'Nepal', 'Himalayan region'],
        'conservation_notes': 'Many species endangered due to overcollection for medicine. CITES listed. Truckloads imported for medicinal use.',
        'modern_research': 'Dendrobine alkaloids show neuroprotective effects (Phytomedicine, 2020). Polysaccharides demonstrate immunomodulatory activity and antioxidant properties (Teoh, 2016). D. fimbriatum polysaccharides enhance T-cell immunity.',
        'enrichment_source': 'ethnobotany_knowledge_base_v3',
        'enrichment_version': '3.0'
    },
    
    'Gastrodia': {
        'traditional_uses': [
            'Traditional Chinese Medicine (Tian Ma - 天麻)',
            'Treatment for headaches, dizziness, and vertigo',
            'Seizure and epilepsy management',
            'Nervous system tonic',
            'Muscle stiffness and spasm treatment',
            'Skin fungal infections (paste with vegetable oil)'
        ],
        'indigenous_names': {
            'Chinese': 'tian ma (天麻) - heavenly hemp',
            'Japanese': 'onino-yagara',
            'Korean': 'cheonma (천마)'
        },
        'cultural_significance': 'Highly valued tonic herb in TCM. Referenced in ancient texts dating to Han Dynasty (206 BCE - 220 CE). Classical medicinal herb with origins in antiquity.',
        'medicinal_uses': [
            'Headache and migraine relief',
            'Vertigo and dizziness treatment',
            'Seizure control and epilepsy management',
            'Neuroprotective effects',
            'Cognitive enhancement',
            'Muscle stiffness/spasm treatment',
            'Skin sores and fungal infections (topical)'
        ],
        'active_compounds': {
            'gastrodin': 'neuroprotective, anti-convulsant',
            '4-hydroxybenzyl alcohol': 'phenolic compound',
            '4-hydroxybenzaldehyde': 'bioactive phenolic',
            'phenolic derivatives': '8 compounds isolated (Teoh, 2016)'
        },
        'regions': ['China', 'Japan', 'Korea', 'Southeast Asia', 'Nepal', 'Sumatra'],
        'conservation_notes': 'Extensively cultivated in China to meet demand. Wild populations protected.',
        'modern_research': 'Gastrodin extensively studied for neuroprotection and seizure control. Protects brain cells and improves cognitive function (Teoh, 2016). Used in decoction form (30g root).',
        'enrichment_source': 'ethnobotany_knowledge_base_v3',
        'enrichment_version': '3.0'
    },
    
    'Bletilla': {
        'traditional_uses': [
            'Traditional Chinese Medicine (Bai Ji - 白及)',
            'Wound healing and hemostatic (stops bleeding)',
            'Treatment of tuberculosis and lung disease',
            'Cosmetic use for skin care'
        ],
        'indigenous_names': {
            'Chinese': 'bai ji (白及) - white mucilaginous root',
            'Japanese': 'shiran (purple orchid)',
            'Korean': 'jaran',
            'Vietnamese': 'bach cap',
            'Hong Kong': 'bak-kup',
            'Taiwanese (Hokien)': 'peh kiu (white ginger)'
        },
        'cultural_significance': 'Classical TCM herb mentioned in Shen Nong Ben Cao Jing (Divine Farmer\'s Materia Medica). One of three main medicinal orchids in ancient Chinese medicine.',
        'medicinal_uses': [
            'Wound healing and tissue regeneration',
            'Hemostatic (stops bleeding)',
            'Tuberculosis and lung hemorrhage treatment',
            'Gastric ulcer healing',
            'Burns and skin injuries',
            'Liver cancer embolization (starch used in interventional radiology)'
        ],
        'active_compounds': {
            'mucilage/polysaccharides': 'wound healing, hemostatic properties',
            'B. striata starch': 'drug delivery system, embolization therapy'
        },
        'regions': ['China', 'Japan', 'Korea', 'Vietnam', 'Myanmar', 'Taiwan'],
        'conservation_notes': 'Cultivated extensively for medicinal use. Wild populations stable.',
        'modern_research': 'B. striata starch employed for embolization to treat inoperable liver cancer. Being developed for drug delivery systems (Teoh, 2016). Proven wound healing and hemostatic properties.',
        'enrichment_source': 'ethnobotany_knowledge_base_v3',
        'enrichment_version': '3.0'
    },

    # NEW GENERA - From "Medicinal Orchids of Asia" academic source
    
    'Cypripedium': {
        'traditional_uses': [
            'Traditional Chinese Medicine (various species)',
            'Nervous system tonic and sedative',
            'Anti-inflammatory applications',
            'Liver health support'
        ],
        'indigenous_names': {
            'Chinese': '杓兰 (shao lan) - ladle orchid',
            'European': 'Lady\'s Slipper'
        },
        'cultural_significance': 'Featured in European and American pharmacopoeia into late 19th century. North American Cypripediums used in Western herbal medicine.',
        'medicinal_uses': [
            'Tonic for nervous system',
            'Liver health and hepatoprotection',
            'Anti-inflammatory and pain relief',
            'Anticancer properties (research ongoing)',
            'Wound healing applications'
        ],
        'active_compounds': {
            'alkaloids': 'nervous system effects',
            'phenolic compounds': 'antioxidant, anti-inflammatory'
        },
        'regions': ['China', 'Europe', 'North America', 'Himalayan region'],
        'conservation_notes': 'Many species critically endangered. CITES protection. Overcollection threatens wild populations.',
        'modern_research': 'Anticancer activity demonstrated in laboratory studies. Cymbidium agglutinin (CA) shows antiviral properties against coronaviruses (Teoh, 2016).',
        'enrichment_source': 'Teoh_2016_Medicinal_Orchids_Asia',
        'enrichment_version': '3.0'
    },
    
    'Eulophia': {
        'traditional_uses': [
            'Aphrodisiac (tubers)',
            'General tonic and vitality enhancement',
            'Fever reduction',
            'Pain relief and anti-inflammatory'
        ],
        'indigenous_names': {
            'Chinese': 'meiguan lan (美冠兰) - beautiful crown orchid',
            'Indian': 'salampanja (various regional names)'
        },
        'cultural_significance': 'Indian substitute for Mediterranean Orchis/Ophrys tubers in salep preparation. Widely used across Asia and Africa for medicinal purposes.',
        'medicinal_uses': [
            'Aphrodisiac properties (roots/tubers)',
            'Fever treatment',
            'Pain and inflammation relief',
            'Wound healing',
            'General tonic for vitality'
        ],
        'active_compounds': {
            'phenanthrenes': '5 known compounds (from E. petersii, E. spectabilis)',
            'phytosterols': 'from African species',
            'erianol': '4-alpha-methylsterol'
        },
        'regions': ['India', 'China', 'Africa', 'Southeast Asia', 'Saudi Arabia (E. petersii)'],
        'conservation_notes': 'Active trade in medicinal orchids in Africa. Some species used as charms. Wild collection threatens populations.',
        'modern_research': 'Phenanthrenes isolated show bioactive properties. Active medicinal trade in Africa (Chinsamy et al., 2011). E. dabia flowers in polyherbal aphrodisiac preparations (Teoh, 2016).',
        'enrichment_source': 'Teoh_2016_Medicinal_Orchids_Asia',
        'enrichment_version': '3.0'
    },
    
    'Flickingeria': {
        'traditional_uses': [
            'Aphrodisiac (major use in India)',
            'Vitality and rejuvenation tonic',
            'Ayurvedic medicine applications'
        ],
        'indigenous_names': {
            'Sanskrit': '32 different names including names denoting "life"',
            'Indian': 'over 36 vernacular names across India'
        },
        'cultural_significance': 'F. fimbriata (formerly Dendrobium plicatile) is one of two candidates for "Sanjeevani" - the legendary herb from Ramayana epic that restored life to dying hero Lakshmana. Truckloads shipped across borders for aphrodisiac trade.',
        'medicinal_uses': [
            'Aphrodisiac and fertility enhancement',
            'Life-restoring properties (legendary)',
            'Vitality and rejuvenation',
            'Anticancer research applications'
        ],
        'regions': ['India (Himalayan region)', 'Nepal', 'Bhutan', 'Thailand', 'Myanmar', 'Assam'],
        'conservation_notes': 'CRITICALLY ENDANGERED due to massive overcollection for aphrodisiac market. Truckloads imported into India from neighboring countries. Conservation crisis.',
        'modern_research': 'Anticancer properties under investigation. F. fimbriata has over three dozen Indian names, many denoting "life" - cultural testament to perceived medicinal power (Teoh, 2016).',
        'enrichment_source': 'Teoh_2016_Medicinal_Orchids_Asia',
        'enrichment_version': '3.0'
    },
    
    'Bulbophyllum': {
        'traditional_uses': [
            'Rheumatism treatment (root decoction)',
            'Asthma relief (flower stalk juice)',
            'Body aches and tired muscles',
            'Toothache remedy (sap)',
            'Food - edible flowers (cooked or raw)'
        ],
        'indigenous_names': {
            'Chinese': 'shi duo lan (石多兰)',
            'Malay': 'Wi buntak',
            'Iban': 'various tribal names',
            'Kelabit': 'edible flower names'
        },
        'cultural_significance': 'Enormous genus (over 2000 species). Once popular garden plant in Southeast Asia. Used by indigenous tribes for various ailments.',
        'medicinal_uses': [
            'Rheumatism (root decoction - Malacca)',
            'Asthma (flower stalk juice chewed - Peninsular Malaysia)',
            'Body aches and tired muscles (Sarawak)',
            'Toothache (sap - Ibans)',
            'Edible vegetable (flowers - Kelabit tribe)'
        ],
        'regions': ['Southeast Asia', 'Malaysia', 'Sarawak', 'India', 'China', 'widespread tropical'],
        'conservation_notes': 'Widespread genus. Some species threatened by habitat loss.',
        'modern_research': 'No chemical or pharmacological data published as of 2016 (Teoh). Ethnobotanical uses documented across Southeast Asian tribes.',
        'enrichment_source': 'Teoh_2016_Medicinal_Orchids_Asia',
        'enrichment_version': '3.0'
    },
    
    'Calanthe': {
        'traditional_uses': [
            'Hair restoration and growth',
            'Traditional tonic',
            'Ornamental and cultural uses'
        ],
        'indigenous_names': {
            'Chinese': 'xiaji lan (虾脊兰) - prawn spine orchid',
            'Japanese': 'ebine'
        },
        'cultural_significance': 'First orchid species to be artificially hybridized by humans. Name means "beautiful flower" from Greek kalos (beautiful) and anthe (bloom). Turns bluish when bruised.',
        'medicinal_uses': [
            'Hair growth and restoration (skin blood flow improvement)',
            'Anticancer - potent antitumor activity',
            'Cancer drug resistance reversal'
        ],
        'active_compounds': {
            'calanthoside': 'improves blood flow, promotes hair growth',
            'glucoindican': 'hair growth promotion',
            'calaliukiuenoside': 'skin blood flow enhancement',
            'calaphenanthrenol': 'from C. discolor, C. liukieuensis',
            'Calanquinone A': 'POTENT anticancer - lung, prostate, colon, breast, brain, nasopharyngeal cancers. Better drug resistance profile than paclitaxel!'
        },
        'regions': ['China', 'Japan', 'tropical Asia', 'Pacific Islands', 'tropical/southern Africa', 'Central America (1 species)'],
        'conservation_notes': 'Some species vulnerable to collection. Many cultivated as ornamentals.',
        'modern_research': 'BREAKTHROUGH: Calanquinone A from C. arisanensis shows potent antitumor activity against multiple cancer types and reverses vincristine resistance. Total synthesis achieved (Lee et al., 2008). Induces s-phase arrest and apoptosis in glioblastoma cells (Teoh, 2016).',
        'enrichment_source': 'Teoh_2016_Medicinal_Orchids_Asia',
        'enrichment_version': '3.0'
    },

    # EXISTING GENERA RETAINED
    
    'Anoectochilus': {
        'traditional_uses': [
            'Traditional Chinese Medicine (Jin Xian Lian - 金线莲)',
            'Hepatoprotective and liver health',
            'Anti-diabetic applications',
            'Anti-hypertensive uses'
        ],
        'indigenous_names': {
            'Chinese': 'jin xian lian (金线莲) - golden thread lotus',
            'Filipino': 'saragoya',
            'Indonesian': 'daun dewa',
            'Malaysian': 'paku rimba'
        },
        'cultural_significance': 'Known as the "King of Jewel Orchids" in Traditional Chinese Medicine. Highly prized for medicinal properties.',
        'medicinal_uses': [
            'Hepatitis treatment and liver protection',
            'Diabetes management (blood sugar regulation)',
            'Hypertension treatment',
            'Anti-inflammatory effects',
            'Immune system enhancement'
        ],
        'active_compounds': {
            'flavonoids': 'antioxidant properties',
            'polyphenols': 'anti-inflammatory',
            'kinsenosides': 'hepatoprotective compounds'
        },
        'regions': ['China', 'Taiwan', 'Southeast Asia', 'Philippines', 'Indonesia'],
        'conservation_notes': 'Critically endangered in the wild due to over-collection. Now cultivated commercially.',
        'modern_research': 'Clinical research demonstrates hepatoprotective effects and antioxidant properties. Active compounds show promise for diabetes and liver disease treatment (Medicinal Orchids of India, 2017).',
        'enrichment_source': 'ethnobotany_knowledge_base_v3',
        'enrichment_version': '3.0'
    },

    'Orchis': {
        'traditional_uses': [
            'Salep drink preparation (Turkish tradition)',
            'Turkish ice cream (dondurma) - unique stretchy texture',
            'Aphrodisiac (tuber)',
            'Nutritive tonic'
        ],
        'indigenous_names': {
            'Turkish': 'salep',
            'Arabic': 'sahlep',
            'Greek': 'salepi',
            'Persian': 'salep'
        },
        'cultural_significance': 'Central to Ottoman palace tradition. Historical street vendors (salepçi) sold warm salep drinks in winter. Tuber shape (resembling testicles) led to 2000-year aphrodisiac belief.',
        'medicinal_uses': [
            'Aphrodisiac properties (historical)',
            'Nutritive tonic',
            'Digestive aid',
            'Soothing for throat and stomach'
        ],
        'salep_preparation': {
            'traditional_drink_recipe': {
                'ingredients': ['1-2 tbsp salep powder (ground Orchis tubers)', '2 cups milk', '2 tbsp sugar', 'cinnamon for garnish'],
                'method': 'Mix salep powder with cold milk until smooth. Heat while stirring constantly until thick and creamy. Add sugar. Serve hot with cinnamon.',
                'texture': 'Thick, creamy, slightly elastic consistency'
            },
            'ice_cream_use': 'Salep powder gives Turkish dondurma its famous stretchy, chewy texture that resists melting. Traditional ice cream makers use long paddles to stretch the salep-thickened ice cream.'
        },
        'regions': ['Turkey', 'Greece', 'Iran', 'Mediterranean', 'Middle East'],
        'conservation_notes': 'CRITICALLY ENDANGERED - Conservation crisis! Requires 1000-4000 tubers per kg of salep powder. Plants take 7-10 years to mature. Mass harvesting has decimated wild populations. CITES protected. Existence precarious in Turkey and Iran.',
        'modern_research': 'Salep mucilage shows prebiotic properties. Historical European/American pharmacopoeia usage documented until late 1800s (Teoh, 2016).',
        'enrichment_source': 'ethnobotany_knowledge_base_v3',
        'enrichment_version': '3.0'
    },
    
    'Cattleya': {
        'traditional_uses': [
            'Ornamental and cultural symbolism',
            'Traditional remedies in Central/South America',
            'Spiritual and ceremonial uses'
        ],
        'indigenous_names': {
            'Spanish': 'flor de mayo',
            'Portuguese': 'orquídea',
            'Indigenous Brazilian': 'various regional names'
        },
        'cultural_significance': 'National flower of Colombia, Venezuela, and Costa Rica. Symbols of luxury and refinement in Victorian England.',
        'medicinal_uses': [
            'Minor wound healing (traditional)',
            'Fever reduction (folk medicine)',
            'Spiritual cleansing (ceremonial)'
        ],
        'regions': ['Central America', 'South America', 'Colombia', 'Brazil', 'Venezuela'],
        'conservation_notes': 'Many species threatened by habitat destruction and illegal collection.',
        'modern_research': 'Limited pharmacological research. Primarily valued for ornamental beauty.',
        'enrichment_source': 'ethnobotany_knowledge_base_v3',
        'enrichment_version': '3.0'
    },

    'Phalaenopsis': {
        'traditional_uses': [
            'Ornamental display',
            'Feng Shui applications (prosperity)',
            'Minor traditional medicine uses in Southeast Asia'
        ],
        'indigenous_names': {
            'Chinese': 'hu die lan (蝴蝶兰) - butterfly orchid',
            'Filipino': 'mariposa',
            'Thai': 'ueang phaeng',
            'Indonesian': 'anggrek bulan - moon orchid'
        },
        'cultural_significance': 'Symbol of prosperity and good fortune in Chinese culture. Popular Lunar New Year gift.',
        'medicinal_uses': [
            'Mild fever reduction (traditional)',
            'General wellness tonic',
            'Respiratory health (minimal documentation)'
        ],
        'regions': ['Southeast Asia', 'Philippines', 'Indonesia', 'Taiwan', 'India'],
        'conservation_notes': 'Wild populations declining due to habitat loss. Extensively cultivated.',
        'modern_research': 'Limited medicinal research. Primarily ornamental species.',
        'enrichment_source': 'ethnobotany_knowledge_base_v3',
        'enrichment_version': '3.0'
    },

    'Vanda': {
        'traditional_uses': [
            'Traditional perfume and fragrance',
            'Ayurvedic medicine (minor uses)',
            'Ornamental and cultural displays'
        ],
        'indigenous_names': {
            'Sanskrit': 'vanda',
            'Thai': 'ueang farang',
            'Filipino': 'waling-waling (V. sanderiana)'
        },
        'cultural_significance': 'V. sanderiana (Waling-waling) is the "Queen of Philippine Orchids" and a national symbol.',
        'medicinal_uses': [
            'Skin care (traditional)',
            'Mild anti-inflammatory',
            'Perfume and aromatherapy'
        ],
        'regions': ['India', 'Southeast Asia', 'Philippines', 'Thailand', 'Indonesia'],
        'conservation_notes': 'V. sanderiana critically endangered. Protection laws in Philippines.',
        'modern_research': 'Fragrance compounds studied. Limited medicinal research.',
        'enrichment_source': 'ethnobotany_knowledge_base_v3',
        'enrichment_version': '3.0'
    },

    'Paphiopedilum': {
        'traditional_uses': [
            'Ornamental (primarily)',
            'Traditional medicine (very limited)',
            'Cultural symbolism'
        ],
        'indigenous_names': {
            'Chinese': 'xie lan (蝎兰) - slipper orchid',
            'Vietnamese': 'hài vàng'
        },
        'cultural_significance': 'Known as "Lady Slipper Orchids" or "Venus Slippers". Highly prized by collectors.',
        'medicinal_uses': [
            'Minimal traditional medicinal use',
            'Primarily ornamental value'
        ],
        'regions': ['Southeast Asia', 'China', 'India', 'Philippines', 'Indonesia'],
        'conservation_notes': 'Many species critically endangered. CITES Appendix I listing. Illegal trade major threat.',
        'modern_research': 'No significant medicinal research. Conservation focus.',
        'enrichment_source': 'ethnobotany_knowledge_base_v3',
        'enrichment_version': '3.0'
    },

    'Oncidium': {
        'traditional_uses': [
            'Ornamental display',
            'Traditional remedies in Central/South America',
            'Ceremonial uses'
        ],
        'indigenous_names': {
            'Spanish': 'lluvia de oro (golden shower)',
            'Portuguese': 'chuva de ouro',
            'Indigenous': 'various Amazonian names'
        },
        'cultural_significance': 'Called "Dancing Lady Orchids" for flower shape. Important in tropical American cultures.',
        'medicinal_uses': [
            'Minor wound care (traditional)',
            'Fever treatment (folk medicine)',
            'Limited documentation'
        ],
        'regions': ['Central America', 'South America', 'Caribbean', 'Mexico', 'Brazil'],
        'conservation_notes': 'Some species threatened. Habitat loss in cloud forests.',
        'modern_research': 'Limited medicinal research. Ornamental focus.',
        'enrichment_source': 'ethnobotany_knowledge_base_v3',
        'enrichment_version': '3.0'
    },

    'Cymbidium': {
        'traditional_uses': [
            'Traditional Chinese Medicine',
            'Confucian scholarly symbolism',
            'Lunar New Year decorations'
        ],
        'indigenous_names': {
            'Chinese': 'lan hua (兰花) - orchid flower',
            'Japanese': 'cymbidium',
            'Korean': 'nancho'
        },
        'cultural_significance': 'Symbol of virtue and nobility in Confucian tradition. One of "Four Gentlemen" in Chinese art (with bamboo, plum, chrysanthemum).',
        'medicinal_uses': [
            'General wellness tonic',
            'Antiviral properties (Cymbidium agglutinin)',
            'Immune support'
        ],
        'active_compounds': {
            'Cymbidium agglutinin (CA)': 'strongly inhibits coronaviruses, arteriviruses, torovirus (Teoh, 2016)'
        },
        'regions': ['China', 'Japan', 'Korea', 'Southeast Asia', 'India', 'Himalayan region'],
        'conservation_notes': 'Some wild species endangered. Extensively cultivated.',
        'modern_research': 'Cymbidium agglutinin shows antiviral activity against coronaviruses (van de Meer et al., 2007). Plant lectins inhibit multiple virus types (Teoh, 2016).',
        'enrichment_source': 'ethnobotany_knowledge_base_v3',
        'enrichment_version': '3.0'
    },

    'Angraecum': {
        'traditional_uses': [
            'Traditional Malagasy medicine',
            'Perfume and fragrance',
            'Cultural ceremonies'
        ],
        'indigenous_names': {
            'Malagasy': 'angrek',
            'French': 'orchidée comète (comet orchid)'
        },
        'cultural_significance': 'A. sesquipedale famous for Darwin\'s prediction of a moth pollinator with 30cm tongue.',
        'medicinal_uses': [
            'Traditional healing (Madagascar)',
            'Aromatic and fragrance uses',
            'Limited documentation'
        ],
        'regions': ['Madagascar', 'Africa', 'Comoro Islands'],
        'conservation_notes': 'Madagascar species threatened by habitat loss.',
        'modern_research': 'Limited research. Ecological focus on pollination.',
        'enrichment_source': 'ethnobotany_knowledge_base_v3',
        'enrichment_version': '3.0'
    },

    'Phaius': {
        'traditional_uses': [
            'Traditional medicine in Asia',
            'Food source (young shoots)',
            'Ornamental gardens'
        ],
        'indigenous_names': {
            'Chinese': 'he lan',
            'Japanese': 'kakuran',
            'Filipino': 'various regional names'
        },
        'cultural_significance': 'Large terrestrial orchids valued for size and flowers.',
        'medicinal_uses': [
            'Traditional healing (various Asian cultures)',
            'Edible young shoots',
            'Limited documentation'
        ],
        'regions': ['Asia', 'Africa', 'Australia', 'Pacific Islands'],
        'conservation_notes': 'Some species threatened by collection.',
        'modern_research': 'Minimal medicinal research.',
        'enrichment_source': 'ethnobotany_knowledge_base_v3',
        'enrichment_version': '3.0'
    },

    'Spiranthes': {
        'traditional_uses': [
            'Native American medicine',
            'European folk remedies',
            'Kidney and bladder health'
        ],
        'indigenous_names': {
            'English': 'Ladies\' Tresses',
            'Native American': 'various tribal names'
        },
        'cultural_significance': 'Used in traditional medicine across Northern Hemisphere.',
        'medicinal_uses': [
            'Kidney ailments',
            'Bladder problems',
            'Urinary tract health',
            'Veneral disease treatment (historical)'
        ],
        'regions': ['North America', 'Europe', 'Asia'],
        'conservation_notes': 'Some species declining due to habitat loss.',
        'modern_research': 'Limited modern research.',
        'enrichment_source': 'ethnobotany_knowledge_base_v3',
        'enrichment_version': '3.0'
    },

    'Ludisia': {
        'traditional_uses': [
            'Traditional Chinese Medicine',
            'Ornamental jewel orchid',
            'Minor medicinal uses'
        ],
        'indigenous_names': {
            'Chinese': 'xue ye lan (blood leaf orchid)',
            'Indonesian': 'various names'
        },
        'cultural_significance': 'Jewel orchid prized for decorative foliage.',
        'medicinal_uses': [
            'Minor traditional healing',
            'Related to Anoectochilus medicinal uses',
            'Limited documentation'
        ],
        'regions': ['China', 'Southeast Asia', 'Indonesia'],
        'conservation_notes': 'Cultivated extensively as ornamental.',
        'modern_research': 'Limited research. Related to medicinal jewel orchids.',
        'enrichment_source': 'Medicinal_Orchids_India_PDF',
        'enrichment_version': '3.0'
    },

    'Macodes': {
        'traditional_uses': [
            'Traditional medicine (jewel orchid)',
            'Ornamental display',
            'Limited medicinal documentation'
        ],
        'indigenous_names': {
            'Indonesian': 'various regional names',
            'Malaysian': 'jewel orchid'
        },
        'cultural_significance': 'Jewel orchid valued for intricate leaf patterns.',
        'medicinal_uses': [
            'Traditional healing (minor)',
            'Related to Anoectochilus medicinal properties',
            'Limited documentation'
        ],
        'regions': ['Southeast Asia', 'Indonesia', 'Malaysia', 'New Guinea'],
        'conservation_notes': 'Some species threatened by collection for ornamental trade.',
        'modern_research': 'Minimal research. Part of jewel orchid medicinal complex.',
        'enrichment_source': 'Medicinal_Orchids_India_PDF',
        'enrichment_version': '3.0'
    }
}
