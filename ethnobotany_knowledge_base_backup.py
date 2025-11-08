"""
Expanded Ethnobotany Knowledge Base
Research-grade traditional knowledge data for orchids
Sources: Indigenous databases, ethnobotany research, traditional medicine records
"""

ETHNOBOTANY_DATABASE = {
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
        'modern_research': 'Vanillin compounds show antioxidant and anti-inflammatory properties (Journal of Agricultural and Food Chemistry, 2019)'
    },
    
    'Dendrobium': {
        'traditional_uses': [
            'Traditional Chinese Medicine (Shi Hu - 石斛)',
            'Food additive and herbal tea',
            'Anti-aging tonic',
            'Buddhist temple offerings'
        ],
        'indigenous_names': {
            'Chinese': 'shi hu (石斛) - stone orchid',
            'Japanese': 'sekkoku',
            'Thai': 'ueang khao',
            'Vietnamese': 'thạch hộc'
        },
        'cultural_significance': 'One of 50 fundamental herbs in Traditional Chinese Medicine for over 2000 years. Featured in classical texts like "Shen Nong Ben Cao Jing" (Divine Farmer\'s Materia Medica).',
        'medicinal_uses': [
            'Immune system support',
            'Kidney and stomach health',
            'Anti-aging and longevity',
            'Yin nourishment in TCM theory',
            'Anti-inflammatory effects'
        ],
        'regions': ['China', 'Japan', 'Southeast Asia', 'India', 'Australia', 'New Guinea'],
        'conservation_notes': 'Many species endangered due to overcollection for medicine. CITES listed.',
        'modern_research': 'Dendrobine alkaloids show neuroprotective effects (Phytomedicine, 2020). Polysaccharides demonstrate immunomodulatory activity.'
    },
    
    'Gastrodia': {
        'traditional_uses': [
            'Traditional Chinese Medicine (Tian Ma - 天麻)',
            'Treatment for headaches, dizziness, and vertigo',
            'Seizure and epilepsy management',
            'Nervous system tonic'
        ],
        'indigenous_names': {
            'Chinese': 'tian ma (天麻) - heavenly hemp',
            'Japanese': 'onino-yagara',
            'Korean': 'cheonma (천마)'
        },
        'cultural_significance': 'Highly valued tonic herb in TCM. Referenced in ancient texts dating to Han Dynasty (206 BCE - 220 CE).',
        'medicinal_uses': [
            'Headache and migraine relief',
            'Vertigo and dizziness treatment',
            'Seizure control',
            'Neuroprotection',
            'Sedative properties'
        ],
        'regions': ['China', 'Japan', 'Korea', 'Taiwan', 'Bhutan'],
        'conservation_notes': 'Wild populations declining. Now primarily cultivated for medicine.',
        'modern_research': 'Gastrodin compound shows anti-convulsant activity (Epilepsy Research, 2018). Neuroprotective effects validated in multiple studies.'
    },
    
    'Phaius': {
        'traditional_uses': [
            'Ornamental in temple gardens',
            'Traditional medicine in Southeast Asia',
            'Anti-inflammatory treatments',
            'Ceremonial decorations'
        ],
        'indigenous_names': {
            'Thai': 'กล้วยไม้พื้นดิน (ground orchid)',
            'Vietnamese': 'lan đất',
            'Malay': 'anggerik tanah'
        },
        'cultural_significance': 'Used in traditional Thai and Vietnamese medicine. Featured in Buddhist temple gardens across Southeast Asia.',
        'medicinal_uses': [
            'Anti-inflammatory applications',
            'Wound healing',
            'Fever reduction',
            'Skin conditions'
        ],
        'regions': ['Southeast Asia', 'Pacific Islands', 'Madagascar', 'East Africa'],
        'conservation_notes': 'Habitat loss threatens some species. Protected in several national parks.',
        'modern_research': 'Phenolic compounds show antimicrobial activity (Asian Pacific Journal of Tropical Medicine, 2017)'
    },
    
    'Cymbidium': {
        'traditional_uses': [
            'Traditional Chinese Medicine',
            'Cultural ceremonies and art',
            'Perfume and fragrance',
            'Symbol of nobility and refinement'
        ],
        'indigenous_names': {
            'Chinese': 'lan hua (兰花) - orchid flower',
            'Japanese': 'ran',
            'Korean': 'nan cho (난초)',
            'Sanskrit': 'vanda'
        },
        'cultural_significance': 'One of the "Four Gentlemen" (四君子) in Chinese art alongside plum blossom, bamboo, and chrysanthemum. Represents Confucian ideals of humility and refinement.',
        'medicinal_uses': [
            'Respiratory health',
            'Anti-inflammatory',
            'Digestive aid',
            'Lung tonic in TCM'
        ],
        'regions': ['China', 'Japan', 'India', 'Southeast Asia', 'Himalayan regions'],
        'conservation_notes': 'Wild collection for horticulture impacts some species.',
        'modern_research': 'Aromatic compounds studied for perfumery applications (Flavour and Fragrance Journal, 2019)'
    },
    
    'Angraecum': {
        'traditional_uses': [
            'Traditional Madagascar medicine',
            'Perfume industry (especially A. sesquipedale)',
            'Ritual and spiritual practices',
            'Treatment of respiratory ailments'
        ],
        'indigenous_names': {
            'Malagasy': 'faham (A. fragrans)',
            'Comorian': 'ilangilang',
            'Swahili': 'mpapai wa mwitu'
        },
        'cultural_significance': 'Sacred in Madagascar traditional beliefs. A. fragrans leaves used ceremonially. A. sesquipedale famous for Darwin\'s pollination prediction.',
        'medicinal_uses': [
            'Digestive aid and tea',
            'Respiratory health',
            'Aromatic therapy',
            'Wound treatment'
        ],
        'regions': ['Madagascar', 'Comoros', 'East Africa', 'Indian Ocean Islands', 'West Africa'],
        'conservation_notes': 'Madagascar deforestation threatens habitat. Several species endangered.',
        'modern_research': 'Coumarin compounds from A. fragrans show antioxidant properties (Natural Product Research, 2016)'
    },
    
    'Bletilla': {
        'traditional_uses': [
            'Traditional Chinese Medicine (Bai Ji - 白及)',
            'Wound healing paste',
            'Hemostatic (stops bleeding)',
            'Cosmetic applications'
        ],
        'indigenous_names': {
            'Chinese': 'bai ji (白及) - white collecting',
            'Japanese': 'shiran',
            'Korean': 'ja ran (자란)'
        },
        'cultural_significance': 'Important TCM herb since Tang Dynasty (618-907 CE). Widely cultivated for medicine.',
        'medicinal_uses': [
            'Hemostatic agent - stops bleeding',
            'Wound healing and tissue repair',
            'Lung health and TB treatment historically',
            'Skin regeneration and scar reduction',
            'Gastrointestinal ulcer treatment'
        ],
        'regions': ['China', 'Japan', 'Korea', 'Taiwan'],
        'conservation_notes': 'Widely cultivated. Wild populations stable in most areas.',
        'modern_research': 'Polysaccharides demonstrate wound healing acceleration (International Journal of Biological Macromolecules, 2020)'
    },
    
    'Spiranthes': {
        'traditional_uses': [
            'Native American medicine',
            'Love charms and aphrodisiacs',
            'Kidney and urinary treatments',
            'Women\'s health remedies'
        ],
        'indigenous_names': {
            'Cherokee': 'Ladies\' tresses',
            'Ojibwe': 'spiral flower',
            'English traditional': 'Lady\'s tresses'
        },
        'cultural_significance': 'Used by Native Americans for various medicinal purposes. European folklore associated with fertility and romance.',
        'medicinal_uses': [
            'Kidney health',
            'Urinary tract issues',
            'Women\'s reproductive health',
            'Diuretic properties'
        ],
        'regions': ['North America', 'Europe', 'Asia', 'Australia'],
        'conservation_notes': 'Some species declining due to habitat loss. Protected in several regions.',
        'modern_research': 'Limited modern research. Traditional uses documented in ethnobotanical surveys.'
    },
    
    'Orchis': {
        'traditional_uses': [
            'Salep/Sahlep drink (traditional hot beverage)',
            'Salep ice cream (dondurma)',
            'Aphrodisiac in Mediterranean cultures',
            'Nutritional supplement and strengthening tonic',
            'Thickening agent in cooking'
        ],
        'indigenous_names': {
            'Turkish': 'salep / salep içeceği',
            'Persian': 'sahlep / ثعلب',
            'Arabic': 'sahlab / سحلب',
            'Greek': 'salepi / σαλέπι',
            'Ottoman Turkish': 'sahlab'
        },
        'cultural_significance': 'Root tubers ground into salep powder, integral to Ottoman and Turkish culture for centuries. Traditional winter drink sold by street vendors. Central to Turkish ice cream (Maraş dondurması) production. Symbol of hospitality and warmth.',
        
        'salep_preparation': {
            'powder_production': 'Orchid tubers are harvested in summer after flowering, boiled to kill the plant, dried in sun, and ground into fine powder. One kg powder requires ~1000-4000 tubers.',
            'traditional_drink_recipe': {
                'ingredients': [
                    '1 tablespoon salep powder',
                    '4 cups milk (traditionally whole milk)',
                    '3-4 tablespoons sugar',
                    'Cinnamon for garnish'
                ],
                'method': 'Mix salep powder with small amount of cold milk to form paste. Heat remaining milk with sugar. Slowly add salep paste while stirring constantly. Simmer until thickened (5-10 min). Serve hot with cinnamon on top.',
                'texture': 'Thick, creamy, stretchy consistency due to glucomannan'
            },
            'ice_cream_use': 'Salep powder is the secret ingredient in Turkish dondurma (Maraş ice cream), giving it unique chewy, stretchy texture. Mixed with milk, sugar, and mastic gum. Ice cream resists melting and can be cut with knife.',
            'other_culinary_uses': [
                'Thickening agent for soups and stews',
                'Boza (fermented grain drink) additive',
                'Dessert preparations',
                'Traditional pastry fillings'
            ]
        },
        
        'cultural_context': {
            'street_vendors': 'Salep traditionally sold by street vendors (salepçi) in winter months throughout Turkey, Iran, and Greece. Vendors use ornate copper urns and decorative glasses.',
            'seasonal_tradition': 'Peak consumption in winter months. Considered warming and nourishing. Often paired with simit (sesame bread rings).',
            'ottoman_palace': 'Served in Ottoman palace to sultans and dignitaries. Considered luxury item.',
            'modern_practice': 'Still popular in Turkey, Greece, and Iran. Modern instant versions available but traditional preparation valued.'
        },
        
        'medicinal_uses': [
            'Digestive health and soothing demulcent',
            'Energy boost and nutritional recovery',
            'Aphrodisiac properties (historical and traditional)',
            'Respiratory support and cough relief',
            'Recovery from illness and surgery',
            'Children\'s nutrition supplement',
            'Elderly care - easy to digest protein source'
        ],
        
        'nutritional_content': {
            'main_component': 'Glucomannan (water-soluble polysaccharide)',
            'properties': 'High fiber, low calorie, forms viscous gel',
            'benefits': 'Prebiotic effects, digestive health, blood sugar regulation'
        },
        
        'species_used': [
            'Orchis mascula (early purple orchid)',
            'Orchis militaris (military orchid)',
            'Orchis anatolica',
            'Orchis palustris',
            'Also Ophrys, Anacamptis, and other related genera'
        ],
        
        'regions': ['Turkey', 'Iran', 'Greece', 'Syria', 'Lebanon', 'Cyprus', 'Balkans', 'Central Asia'],
        
        'conservation_crisis': {
            'status': 'CRITICALLY ENDANGERED - Multiple species extinct in parts of range',
            'threat': 'Overharvesting for salep powder. One kg requires 1000-4000 tubers, each taking 7-10 years to mature.',
            'cites_status': 'CITES Appendix II - All Orchidaceae',
            'illegal_trade': 'Despite bans, black market trade continues. Tubers smuggled from Turkey, Iran, and surrounding countries.',
            'alternatives': 'Commercial salep now often mixed with or replaced by corn starch, rice flour, or carob powder. True orchid salep increasingly rare and expensive.'
        },
        
        'conservation_efforts': 'Turkey banned wild harvesting in 2012. Cultivation attempts ongoing but challenging. Consumer education about conservation needed.',
        
        'modern_research': 'Glucomannan polysaccharides studied for prebiotic potential (Food Hydrocolloids, 2018). Weight management applications researched (Journal of Ethnopharmacology, 2017). Antioxidant properties documented.',
        
        'authentic_sources': {
            'note': 'Genuine orchid salep is now rare and expensive. Most commercial "salep" is substitute blend.',
            'traditional_markets': 'Spice bazaars in Istanbul (Egyptian Bazaar/Mısır Çarşısı), Tehran Grand Bazaar, Athens central market',
            'ethical_note': 'Due to conservation crisis, recommend avoiding genuine orchid salep. Support synthetic alternatives and conservation efforts.'
        }
    },
    
    'Eulophia': {
        'traditional_uses': [
            'African traditional medicine',
            'Food source (edible tubers)',
            'Fertility treatments',
            'Spiritual and ritual uses'
        ],
        'indigenous_names': {
            'Swahili': 'kinanda',
            'Zulu': 'incema',
            'Shona': 'chikandakanda',
            'Yoruba': 'ewe-oro'
        },
        'cultural_significance': 'Important in various African traditional healing practices and spiritual ceremonies. Tubers eaten during food scarcity.',
        'medicinal_uses': [
            'Digestive issues',
            'Fertility enhancement',
            'General health tonic',
            'Wound healing',
            'Respiratory ailments'
        ],
        'regions': ['Sub-Saharan Africa', 'Madagascar', 'India', 'Southeast Asia', 'Australia'],
        'conservation_notes': 'Overcollection and habitat loss threaten some species. Traditional use vs. conservation requires balance.',
        'modern_research': 'Alkaloids show antimicrobial activity (Journal of Ethnopharmacology, 2019)'
    },
    
    'Cattleya': {
        'traditional_uses': [
            'Ornamental and ceremonial in Latin America',
            'Traditional medicine in Amazon',
            'Love charms in Brazilian folklore',
            'Decorative in religious festivals'
        ],
        'indigenous_names': {
            'Portuguese': 'orquídea rainha',
            'Guarani': 'ysypó guasu',
            'Tupi': 'uaraná-etá'
        },
        'cultural_significance': 'National flower of Colombia, Costa Rica, and several Brazilian states. Important in Catholic festivals and indigenous ceremonies.',
        'medicinal_uses': [
            'Fever reduction (Amazon traditional)',
            'Anti-inflammatory (traditional)',
            'Perfume and aromatherapy'
        ],
        'regions': ['Central America', 'South America', 'Caribbean'],
        'conservation_notes': 'Overcollection for horticulture. Many species CITES protected.',
        'modern_research': 'Aromatic compounds studied for perfumery and aromatherapy applications'
    },
    
    'Phalaenopsis': {
        'traditional_uses': [
            'Ornamental in Southeast Asian cultures',
            'Traditional medicine in Philippines',
            'Feng Shui applications',
            'Wedding and celebration decorations'
        ],
        'indigenous_names': {
            'Filipino': 'mariposa (butterfly)',
            'Thai': 'เอื้องผีเสื้อ (butterfly orchid)',
            'Malay': 'rama-rama',
            'Chinese': '蝴蝶兰 (butterfly orchid)'
        },
        'cultural_significance': 'Symbol of good fortune and prosperity in Chinese culture. Popular in Lunar New Year celebrations.',
        'medicinal_uses': [
            'Skin care (traditional Philippines)',
            'Anti-inflammatory applications',
            'Decorative medicine jars'
        ],
        'regions': ['Southeast Asia', 'Philippines', 'Indonesia', 'Taiwan', 'Australia'],
        'conservation_notes': 'Habitat loss threatens wild species. Most commercial plants are hybrids.',
        'modern_research': 'Phenolic compounds studied for cosmetic applications (Molecules, 2021)'
    },
    
    'Vanda': {
        'traditional_uses': [
            'Traditional Thai medicine',
            'Ceremonial garlands and offerings',
            'Natural dyes from flowers',
            'Buddhist temple decorations'
        ],
        'indigenous_names': {
            'Thai': 'แวนด้า (wanda)',
            'Sanskrit': 'वन्दा (vanda)',
            'Bengali': 'রাসনা (rasna)',
            'Tamil': 'வந்தா (vantha)'
        },
        'cultural_significance': 'Important in Hindu and Buddhist religious ceremonies. National flower of Singapore (V. Miss Joaquim).',
        'medicinal_uses': [
            'Anti-inflammatory (Ayurvedic)',
            'Fever reduction',
            'Wound healing',
            'Digestive aid'
        ],
        'regions': ['India', 'Southeast Asia', 'Philippines', 'Papua New Guinea', 'Northern Australia'],
        'conservation_notes': 'Overcollection threatens some species. Cultivation encouraged.',
        'modern_research': 'Antibacterial properties documented (BMC Complementary Medicine, 2020)'
    },
    
    'Paphiopedilum': {
        'traditional_uses': [
            'Ornamental in Asian gardens',
            'Traditional medicine in China and Vietnam',
            'Decorative in temples',
            'Symbol of rare beauty'
        ],
        'indigenous_names': {
            'Chinese': '兜兰 (dou lan) - pouch orchid',
            'Vietnamese': 'giày tiên',
            'Thai': 'รองเท้านารี (lady slipper)',
            'Japanese': 'atsumori-sou'
        },
        'cultural_significance': 'Highly prized in Asian horticulture for centuries. Symbol of rare beauty and elegance.',
        'medicinal_uses': [
            'Traditional Chinese Medicine applications',
            'Anti-inflammatory (traditional Vietnam)',
            'Wound care (historical)'
        ],
        'regions': ['Southeast Asia', 'China', 'India', 'Philippines', 'Indonesia'],
        'conservation_notes': 'CRITICALLY ENDANGERED - Many species. CITES Appendix I. Poaching major threat.',
        'modern_research': 'Conservation genetics studies focus on breeding programs'
    },
    
    'Oncidium': {
        'traditional_uses': [
            'Ornamental in Latin American cultures',
            'Traditional medicine in Andes',
            'Perfume extraction',
            'Ceremonial decorations'
        ],
        'indigenous_names': {
            'Spanish': 'bailarina (dancing lady)',
            'Quechua': 'wakanki',
            'Portuguese': 'chuva de ouro (golden shower)'
        },
        'cultural_significance': 'Popular in South American gardens and festivals. Dancing lady flowers used in traditional celebrations.',
        'medicinal_uses': [
            'Respiratory ailments (Andean traditional)',
            'Fever reduction',
            'Perfume and aromatherapy'
        ],
        'regions': ['Central America', 'South America', 'Caribbean', 'Florida'],
        'conservation_notes': 'Habitat loss affects some species. Cloud forest species particularly vulnerable.',
        'modern_research': 'Fragranceomic studies of scent compounds (Journal of Chemical Ecology, 2019)'
    },
    
    'Anoectochilus': {
        'traditional_uses': [
            'Traditional Chinese Medicine (Jin Xian Lian - 金线莲)',
            'Herbal tea and tonic',
            'Treatment for liver disease',
            'Jewel orchid cultivated for ornamental foliage'
        ],
        'indigenous_names': {
            'Chinese': 'jin xian lian (金线莲) - golden thread orchid',
            'English': 'King of Jewel Orchids',
            'Thai': 'กล้วยไม้เส้นทอง',
            'Vietnamese': 'lan kim tuyến'
        },
        'cultural_significance': 'Highly revered in Traditional Chinese Medicine. One of the most valuable medicinal orchids. "King of Jewel Orchids" for its stunning golden-veined leaves and potent medicinal properties.',
        
        'medicinal_uses': [
            'Hepatoprotective - liver protection and hepatitis treatment',
            'Anti-inflammatory effects',
            'Antioxidant properties - fights free radicals',
            'Hypertension (high blood pressure) management',
            'Diabetes treatment and blood sugar regulation',
            'Immune system enhancement',
            'Fever reduction',
            'Respiratory health'
        ],
        
        'active_compounds': {
            'flavonoids': 'Powerful antioxidant compounds',
            'polyphenols': 'Anti-inflammatory and antioxidant effects',
            'kinsenosides': 'Unique compounds with hepatoprotective activity',
            'glycosides': 'Various medicinal glycoside compounds'
        },
        
        'research_applications': {
            'hepatitis_treatment': 'Clinical studies show effectiveness in treating viral hepatitis and protecting liver function',
            'antioxidant_activity': 'Strong free radical scavenging ability documented in multiple studies',
            'anti_inflammatory': 'Reduces inflammatory markers in research models',
            'antidiabetic': 'Helps regulate blood sugar levels',
            'anticancer_potential': 'Preliminary research on tumor suppression'
        },
        
        'cultivation_notes': {
            'difficulty': 'Challenging to grow - requires specific conditions',
            'environment': 'High humidity (60-80%), low light, cool temperatures',
            'substrate': 'Well-draining mix with sphagnum moss',
            'terrarium': 'Best grown in terrariums for humidity control',
            'commercial_value': 'High value for medicinal use - often cultivated in Asia'
        },
        
        'species_varieties': [
            'Anoectochilus roxburghii - most medicinally valuable',
            'Anoectochilus formosanus - Taiwanese variety',
            'Anoectochilus albolineatus - white-veined jewel orchid',
            'Anoectochilus chapaensis - Vietnam endemic'
        ],
        
        'regions': ['China', 'Taiwan', 'India', 'Sri Lanka', 'Southeast Asia', 'Japan'],
        
        'conservation_notes': 'Endangered in wild due to overcollection for medicine. Now primarily cultivated. Protected species in many countries.',
        
        'modern_research': 'Extensively studied for medicinal properties. Flavonoids and kinsenosides show hepatoprotective activity (Journal of Ethnopharmacology, 2020). Antioxidant compounds validated (Phytochemistry, 2019). Clinical trials ongoing for liver disease treatment.',
        
        'traditional_preparation': {
            'dried_herb': 'Whole plant dried and used in decoctions',
            'tea': 'Fresh or dried leaves steeped as medicinal tea',
            'tonic': 'Extracted compounds used in health tonics',
            'dosage': 'Traditional dose: 3-10g dried herb per day'
        }
    },
    
    'Ludisia': {
        'traditional_uses': [
            'Ornamental jewel orchid',
            'Traditional Southeast Asian medicine',
            'Decorative in temple gardens',
            'Terrarium cultivation'
        ],
        'indigenous_names': {
            'English': 'Jewel Orchid',
            'Chinese': '血叶兰 (blood-leaf orchid)',
            'Malay': 'anggerik permata',
            'Thai': 'เอื้องใบสี'
        },
        'cultural_significance': 'Most popular and easiest to grow jewel orchid. Prized for velvety dark leaves with striking red/pink veins rather than flowers.',
        'medicinal_uses': [
            'Mild anti-inflammatory (traditional Southeast Asia)',
            'Ornamental and stress relief',
            'Air purification in terrariums'
        ],
        'regions': ['Malaysia', 'Indonesia', 'Philippines', 'Myanmar', 'Southern China'],
        'conservation_notes': 'Not threatened - widely cultivated. Easy to propagate.',
        'modern_research': 'Popular in horticulture. Leaf pigmentation studied for ornamental breeding.'
    },
    
    'Macodes': {
        'traditional_uses': [
            'Ornamental jewel orchid',
            'Traditional medicine in Indonesia',
            'Decorative in rainforest exhibits',
            'Collector\'s specimen plant'
        ],
        'indigenous_names': {
            'English': 'Lightning Bolt Orchid',
            'Indonesian': 'anggrek kilat',
            'Malay': 'anggerik kilat'
        },
        'cultural_significance': 'Famous for iridescent golden lightning-bolt leaf patterns. Considered one of the most beautiful jewel orchids.',
        'medicinal_uses': [
            'Traditional wound healing (Indonesia)',
            'Anti-inflammatory applications',
            'Fever reduction (folk medicine)'
        ],
        'regions': ['Malaysia', 'Indonesia', 'New Guinea', 'Philippines', 'Borneo'],
        'conservation_notes': 'Habitat loss threatens wild populations. Protected in some regions. Widely cultivated.',
        'modern_research': 'Leaf iridescence studied for biomimetic applications (Nature, 2016). Ornamental breeding programs active.'
    }
}

# Synonyms and variant names for matching
GENUS_SYNONYMS = {
    'Bletilla': ['Bletia'],
    'Cymbidium': ['Cym'],
    'Dendrobium': ['Den'],
    'Phalaenopsis': ['Phal'],
    'Cattleya': ['Catt', 'C.'],
    'Paphiopedilum': ['Paph'],
    'Oncidium': ['Onc'],
    'Vanda': ['V.']
}

def get_ethnobotany_for_genus(genus):
    """Get ethnobotany data for a genus, checking synonyms"""
    if genus in ETHNOBOTANY_DATABASE:
        return ETHNOBOTANY_DATABASE[genus]
    
    # Check synonyms
    for main_genus, synonyms in GENUS_SYNONYMS.items():
        if genus in synonyms:
            return ETHNOBOTANY_DATABASE.get(main_genus)
    
    return None
