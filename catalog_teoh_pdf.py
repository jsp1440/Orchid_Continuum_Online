#!/usr/bin/env python3
"""
Catalog Teoh's Medicinal Orchids of Asia PDF into research document database
"""
from app import app, db
from models import ResearchDocument, DocumentTopic, GenusKnowledgeCard
from datetime import datetime
import os

def catalog_teoh_pdf():
    """Add Teoh PDF to research document catalog with genus knowledge cards"""
    
    with app.app_context():
        # Check if already catalogued
        existing = ResearchDocument.query.filter_by(
            title="Medicinal Orchids of Asia"
        ).first()
        
        if existing:
            print(f"⚠️  Document already catalogued (ID: {existing.id})")
            return existing.id
        
        # Create main document entry
        document = ResearchDocument(
            title="Medicinal Orchids of Asia",
            author="Eng Soon Teoh, M.D.",
            year=2016,  # Note: 2017 is publication year, but Springer shows 2016
            publisher="Springer International Publishing",
            doi="10.1007/978-3-319-24274-3",
            file_path="attached_assets/2017_Medicinal_Orchids_of_Asia_1760302124193.pdf",
            file_name="Medicinal_Orchids_of_Asia_Teoh_2017.pdf",
            file_size_mb=os.path.getsize("attached_assets/2017_Medicinal_Orchids_of_Asia_1760302124193.pdf") / (1024 * 1024) if os.path.exists("attached_assets/2017_Medicinal_Orchids_of_Asia_1760302124193.pdf") else None,
            page_count=753,
            document_type="book",
            themes=[
                "Ethnobotany",
                "Orchid Medicinal Uses",
                "Asian Traditional Medicine",
                "Pharmacology",
                "Cultural Uses",
                "Conservation",
                "Phytochemistry",
                "Traditional Chinese Medicine",
                "Ayurveda",
                "Thai Herbalism"
            ],
            genera_covered=[
                "Gastrodia",
                "Dendrobium",
                "Bletilla",
                "Vanilla",
                "Anoectochilus",
                "Bulbophyllum",
                "Calanthe",
                "Cymbidium",
                "Eulophia",
                "Flickingeria",
                "Cypripedium",
                "Orchis",
                "Paphiopedilum",
                "Phalaenopsis",
                "Vanda"
            ],
            language="English",
            abstract="Comprehensive reference on medicinal uses of Asian orchids, covering traditional medicine systems (TCM, Ayurveda), phytochemical analysis, pharmacological research, and conservation concerns. Documents historical uses from classical texts like Shen Nong Ben Cao Jing to modern clinical research.",
            keywords=[
                "medicinal orchids",
                "ethnobotany",
                "TCM",
                "traditional medicine",
                "alkaloids",
                "phytochemistry",
                "conservation",
                "orchid pharmacology",
                "Asian herbalism"
            ],
            is_searchable=True,
            citation_count=0,
            view_count=0
        )
        
        db.session.add(document)
        db.session.flush()  # Get the document ID
        
        print(f"📚 Created document record: {document.title} (ID: {document.id})")
        
        # Extract searchable topics from the book
        topics_data = [
            # Traditional uses
            {
                "type": "traditional_use",
                "name": "Aphrodisiacs",
                "description": "Orchids used as aphrodisiacs in various cultures",
                "pages": [8],
                "cultural_area": "Global",
                "tags": ["traditional medicine", "reproductive health", "cultural practices"]
            },
            {
                "type": "traditional_use",
                "name": "Neurological Conditions",
                "description": "Treatment of brain disorders, stroke, epilepsy",
                "pages": [7, 8],
                "cultural_area": "China",
                "genus": "Gastrodia",
                "tags": ["TCM", "neurology", "brain health"]
            },
            {
                "type": "traditional_use",
                "name": "Respiratory Diseases",
                "description": "Treatment of tuberculosis, bronchiectasis, cough",
                "pages": [7],
                "cultural_area": "China",
                "genus": "Bletilla",
                "tags": ["TCM", "pulmonary", "infectious disease"]
            },
            # Chemical compounds
            {
                "type": "chemical_compound",
                "name": "Alkaloids",
                "description": "Nitrogen-containing compounds with pharmacological activity",
                "pages": [7, 8, 9],
                "genus": "Dendrobium",
                "tags": ["phytochemistry", "bioactive compounds", "pharmacology"]
            },
            {
                "type": "chemical_compound",
                "name": "Phenols and Flavonoids",
                "description": "Antioxidant compounds with neuroprotective effects",
                "pages": [7, 8],
                "genus": "Gastrodia",
                "tags": ["phytochemistry", "antioxidants", "neuroprotection"]
            },
            {
                "type": "chemical_compound",
                "name": "Vanillin",
                "description": "Primary aromatic compound from vanilla orchids",
                "pages": [8],
                "genus": "Vanilla",
                "tags": ["flavoring", "aromatic compounds", "commercial use"]
            },
            # Cultural contexts
            {
                "type": "cultural_context",
                "name": "Shen Nong Ben Cao Jing",
                "description": "First century CE classical Chinese medical text documenting orchid medicines",
                "pages": [7, 8, 9],
                "cultural_area": "China",
                "tags": ["TCM", "historical texts", "classical medicine"]
            },
            {
                "type": "cultural_context",
                "name": "Aztec Medicine",
                "description": "Pre-Columbian use of vanilla in Mesoamerican cultures",
                "pages": [8],
                "cultural_area": "Mesoamerica",
                "genus": "Vanilla",
                "tags": ["indigenous knowledge", "historical use", "Aztec"]
            },
            # Conservation issues
            {
                "type": "conservation",
                "name": "Overharvesting of Medicinal Orchids",
                "description": "Conservation threats from medicinal trade",
                "pages": [7, 8, 9],
                "cultural_area": "Asia",
                "tags": ["conservation", "endangered species", "sustainable use", "CITES"]
            },
            {
                "type": "conservation",
                "name": "Dendrobium Trade",
                "description": "Commercial exploitation threatening wild populations",
                "pages": [7, 8, 9],
                "cultural_area": "SE Asia",
                "genus": "Dendrobium",
                "tags": ["conservation", "commercial trade", "sustainability"]
            },
            {
                "type": "conservation",
                "name": "Gastrodia Conservation",
                "description": "Protection needed for neurological medicine orchid",
                "pages": [7, 8],
                "cultural_area": "China",
                "genus": "Gastrodia",
                "tags": ["conservation", "endangered", "medicinal trade"]
            }
        ]
        
        for topic_data in topics_data:
            topic = DocumentTopic(
                document_id=document.id,
                topic_type=topic_data["type"],
                topic_name=topic_data["name"],
                description=topic_data["description"],
                page_references=topic_data["pages"],
                cultural_area=topic_data.get("cultural_area"),
                genus=topic_data.get("genus"),
                search_tags=topic_data["tags"],
                relevance_score=1.0
            )
            db.session.add(topic)
        
        print(f"📑 Created {len(topics_data)} searchable topics")
        
        # Create genus-specific knowledge cards from user's table
        genus_cards = [
            {
                "genus": "Gastrodia",
                "medicinal_uses": [
                    "Neurological conditions",
                    "Brain tonic",
                    "Stroke recovery",
                    "Epilepsy treatment",
                    "Headache relief"
                ],
                "traditional_uses": [
                    "Tianma (天麻) in Shen Nong Ben Cao Jing",
                    "Used in Chinese medicine for over 2000 years"
                ],
                "active_compounds": {
                    "phenols": "Neuroprotective phenolic compounds",
                    "flavonoids": "Antioxidant flavonoid compounds",
                    "gastrodin": "Primary bioactive compound for neurological effects"
                },
                "compound_classes": ["Phenols", "Flavonoids", "Glycosides"],
                "cultural_areas": ["China", "Korea", "Japan"],
                "page_references": [7, 8],
                "key_findings": "Classical medicinal orchid documented in Shen Nong Ben Cao Jing. Extensively researched for neurological applications.",
                "conservation_notes": "High demand for medicinal use threatens wild populations"
            },
            {
                "genus": "Dendrobium",
                "medicinal_uses": [
                    "Tonic and longevity herb",
                    "Aphrodisiac",
                    "Immune system modulation",
                    "Anti-aging effects",
                    "Digestive health"
                ],
                "traditional_uses": [
                    "Shihu (石斛) in Shen Nong Ben Cao Jing",
                    "One of the 50 fundamental TCM herbs",
                    "Emperor's tonic in ancient China"
                ],
                "active_compounds": {
                    "alkaloids": "Bioactive alkaloid compounds",
                    "bibenzyls": "Phenolic bibenzyl compounds",
                    "polysaccharides": "Immune-modulating polysaccharides"
                },
                "compound_classes": ["Alkaloids", "Bibenzyls", "Polysaccharides"],
                "cultural_areas": ["China", "SE Asia", "Thailand", "Vietnam"],
                "page_references": [7, 8, 9],
                "key_findings": "Most extensively studied medicinal orchid genus. Over 70 species used in traditional medicine.",
                "conservation_status": "CITES Appendix II",
                "conservation_notes": "Massive commercial trade threatens wild populations. Cultivation programs established."
            },
            {
                "genus": "Bletilla",
                "medicinal_uses": [
                    "Tuberculosis treatment",
                    "Bronchiectasis",
                    "Skin wound healing",
                    "Hemostatic (stops bleeding)",
                    "Burn treatment"
                ],
                "traditional_uses": [
                    "Baiji (白及) in traditional Chinese medicine",
                    "Used in wound care for centuries"
                ],
                "active_compounds": {
                    "phytoalexins": "Antimicrobial defense compounds",
                    "starch": "Wound-healing mucilaginous starch",
                    "phenanthrenes": "Bioactive phenanthrene compounds"
                },
                "compound_classes": ["Phytoalexins", "Polysaccharides", "Phenanthrenes"],
                "cultural_areas": ["China", "Japan", "Korea"],
                "page_references": [7],
                "key_findings": "Bletilla striata starch used in modern medical technology for embolization therapy and drug delivery.",
                "pharmacological_effects": [
                    "Hemostatic activity",
                    "Antimicrobial properties",
                    "Wound healing acceleration"
                ]
            },
            {
                "genus": "Vanilla",
                "medicinal_uses": [
                    "Aphrodisiac",
                    "Appetite stimulant",
                    "Digestive aid",
                    "Mood enhancer"
                ],
                "traditional_uses": [
                    "Aztec ceremonial beverage",
                    "Flavoring agent in traditional medicine",
                    "Used by Totonac people of Mexico"
                ],
                "active_compounds": {
                    "vanillin": "Primary aromatic and bioactive compound",
                    "vanillic_acid": "Antioxidant phenolic acid"
                },
                "compound_classes": ["Phenolic aldehydes", "Aromatic compounds"],
                "cultural_areas": ["Mesoamerica", "Mexico", "Global"],
                "indigenous_names": {
                    "Totonac": "Tlilxochitl",
                    "Aztec": "Tlilxochitl (black flower)"
                },
                "page_references": [8],
                "key_findings": "Most economically important orchid genus. Vanilla planifolia is only food orchid.",
                "conservation_status": "Vulnerable",
                "conservation_notes": "Wild populations declining due to habitat loss. Most production from cultivation."
            },
            {
                "genus": "Anoectochilus",
                "medicinal_uses": [
                    "General tonic",
                    "Traditional folk medicine",
                    "Liver protection",
                    "Anti-inflammatory"
                ],
                "traditional_uses": [
                    "Jewel orchid used in Asian herbal remedies",
                    "Ground orchid traditional medicine"
                ],
                "active_compounds": {
                    "glycosides": "Bioactive glycoside compounds",
                    "flavonoids": "Antioxidant compounds"
                },
                "compound_classes": ["Glycosides", "Flavonoids"],
                "cultural_areas": ["SE Asia", "China", "Taiwan"],
                "page_references": ["various"],
                "key_findings": "Jewel orchid with ornamental and medicinal value.",
                "conservation_notes": "Popular in ornamental trade; conservation status varies by species"
            }
        ]
        
        for card_data in genus_cards:
            card = GenusKnowledgeCard(
                genus=card_data["genus"],
                document_id=document.id,
                medicinal_uses=card_data["medicinal_uses"],
                traditional_uses=card_data["traditional_uses"],
                active_compounds=card_data["active_compounds"],
                compound_classes=card_data["compound_classes"],
                cultural_areas=card_data["cultural_areas"],
                indigenous_names=card_data.get("indigenous_names", {}),
                pharmacological_effects=card_data.get("pharmacological_effects", []),
                page_references=card_data["page_references"],
                key_findings=card_data["key_findings"],
                conservation_status=card_data.get("conservation_status"),
                conservation_notes=card_data.get("conservation_notes"),
                confidence_score=0.95  # High confidence from authoritative source
            )
            db.session.add(card)
        
        print(f"🌺 Created {len(genus_cards)} genus knowledge cards")
        
        # Commit all changes
        db.session.commit()
        
        print("\n✅ Successfully catalogued Teoh's Medicinal Orchids of Asia!")
        print(f"   📚 Document ID: {document.id}")
        print(f"   📑 Topics: {len(topics_data)}")
        print(f"   🌺 Genus cards: {len(genus_cards)}")
        print(f"   🏷️  Themes: {len(document.themes)}")
        print(f"   🌍 Genera covered: {len(document.genera_covered)}")
        
        return document.id

if __name__ == "__main__":
    doc_id = catalog_teoh_pdf()
    print(f"\n🔍 Document can be searched by:")
    print(f"   - Title: 'Medicinal Orchids of Asia'")
    print(f"   - Author: 'Teoh'")
    print(f"   - Genera: Gastrodia, Dendrobium, Bletilla, Vanilla, Anoectochilus")
    print(f"   - Topics: TCM, alkaloids, conservation, ethnobotany")
    print(f"   - Cultural areas: China, SE Asia, Mesoamerica")
