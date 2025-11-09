#!/usr/bin/env python3
"""
Substrate Recommendation Engine
Intelligent substrate/potting media recommendations based on:
- Species microclimate preferences (elevation, humidity, temperature)
- Grower's conditions (climate, watering habits, experience level)
- Substrate properties (drainage, moisture retention, aeration)

Analyzes commercial mixes and provides DIY recipes
"""
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class SubstrateProperties:
    """Properties of a substrate component or mix"""
    name: str
    drainage: str  # 'excellent', 'good', 'moderate', 'poor'
    moisture_retention: str  # 'high', 'moderate', 'low'
    aeration: str  # 'excellent', 'good', 'moderate', 'poor'
    ph_level: str  # 'acidic', 'neutral', 'alkaline'
    decomposition_rate: str  # 'very slow', 'slow', 'moderate', 'fast'
    cost: str  # 'low', 'moderate', 'high'
    availability: str  # 'common', 'specialty'
    best_for: List[str]  # Growing conditions this substrate excels in
    notes: str

class SubstrateKnowledgeBase:
    """
    Comprehensive knowledge base of orchid substrates
    """
    
    # Substrate components
    COMPONENTS = {
        'bark': SubstrateProperties(
            name='Fir/Pine Bark',
            drainage='excellent',
            moisture_retention='moderate',
            aeration='excellent',
            ph_level='slightly acidic',
            decomposition_rate='slow',
            cost='low',
            availability='common',
            best_for=['epiphytes', 'intermediate growers', 'warm conditions'],
            notes='Classic orchid substrate. Available in fine, medium, coarse grades. Medium grade best for Phalaenopsis/Cattleya.'
        ),
        'sphagnum_moss': SubstrateProperties(
            name='Sphagnum Moss',
            drainage='poor',
            moisture_retention='high',
            aeration='good',
            ph_level='acidic',
            decomposition_rate='slow',
            cost='moderate',
            availability='common',
            best_for=['high humidity lovers', 'seedlings', 'mounted orchids'],
            notes='Excellent moisture retention. Long-fiber New Zealand moss is highest quality. Requires careful watering.'
        ),
        'tree_fern': SubstrateProperties(
            name='Tree Fern Fiber',
            drainage='excellent',
            moisture_retention='moderate',
            aeration='excellent',
            ph_level='neutral',
            decomposition_rate='very slow',
            cost='high',
            availability='specialty',
            best_for=['mounted orchids', 'high-elevation species', 'conservation concerns'],
            notes='Premium material but environmentally sensitive. Being phased out due to sustainability.'
        ),
        'coconut_husk': SubstrateProperties(
            name='Coconut Husk Chips',
            drainage='excellent',
            moisture_retention='moderate',
            aeration='excellent',
            ph_level='neutral',
            decomposition_rate='slow',
            cost='low',
            availability='common',
            best_for=['epiphytes', 'eco-conscious growers', 'warm growers'],
            notes='Sustainable alternative to bark. Must be rinsed before use to remove salts.'
        ),
        'perlite': SubstrateProperties(
            name='Perlite',
            drainage='excellent',
            moisture_retention='low',
            aeration='excellent',
            ph_level='neutral',
            decomposition_rate='none',
            cost='low',
            availability='common',
            best_for=['drainage improvement', 'semi-hydro', 'custom mixes'],
            notes='Volcanic glass. Improves drainage and aeration. Usually 10-20% of mix.'
        ),
        'charcoal': SubstrateProperties(
            name='Horticultural Charcoal',
            drainage='excellent',
            moisture_retention='low',
            aeration='excellent',
            ph_level='neutral',
            decomposition_rate='none',
            cost='moderate',
            availability='common',
            best_for=['drainage', 'odor control', 'preventing rot'],
            notes='Absorbs impurities and prevents souring. Usually 5-10% of mix.'
        ),
        'leca': SubstrateProperties(
            name='LECA (Clay Pebbles)',
            drainage='excellent',
            moisture_retention='moderate',
            aeration='excellent',
            ph_level='neutral',
            decomposition_rate='none',
            cost='moderate',
            availability='common',
            best_for=['semi-hydro', 'consistent moisture', 'beginners'],
            notes='Ideal for semi-hydroponic culture. Reusable. Provides consistent moisture with good aeration.'
        ),
        'rock': SubstrateProperties(
            name='Lava Rock',
            drainage='excellent',
            moisture_retention='low',
            aeration='excellent',
            ph_level='neutral',
            decomposition_rate='none',
            cost='low',
            availability='common',
            best_for=['drainage', 'weight', 'lithophytes'],
            notes='Adds weight to pots. Good for top-heavy plants. Porous surface.'
        )
    }
    
    # Commercial mixes
    COMMERCIAL_MIXES = {
        'repotme_classic': {
            'name': 'rePotme Classic Orchid Mix',
            'ingredients': ['bark (medium)', 'sponge rock', 'charcoal'],
            'grade': 'medium',
            'best_for': ['Phalaenopsis', 'Cattleya', 'Oncidium', 'beginner-friendly'],
            'drainage': 'excellent',
            'moisture_retention': 'moderate',
            'price_range': 'moderate',
            'notes': 'Industry standard. Pre-washed. Multiple size grades available.'
        },
        'repotme_imperial': {
            'name': 'rePotme Imperial Orchid Mix',
            'ingredients': ['bark (medium)', 'sponge rock', 'charcoal', 'sphagnum moss'],
            'grade': 'premium',
            'best_for': ['Phalaenopsis', 'moisture-loving species', 'consistent watering'],
            'drainage': 'good',
            'moisture_retention': 'high',
            'price_range': 'high',
            'notes': 'Premium blend with added moisture retention. Good for hot/dry climates.'
        },
        'better_gro_special': {
            'name': 'Better-Gro Special Orchid Mix',
            'ingredients': ['bark (medium)', 'charcoal', 'sponge rock'],
            'grade': 'medium',
            'best_for': ['epiphytes', 'Phalaenopsis', 'Cattleya', 'budget-conscious'],
            'drainage': 'excellent',
            'moisture_retention': 'moderate',
            'price_range': 'low',
            'notes': 'Widely available at big-box stores. Good value. May need supplemental feeding.'
        },
        'miracle_gro_orchid': {
            'name': 'Miracle-Gro Orchid Potting Mix',
            'ingredients': ['bark', 'peat moss', 'coconut coir'],
            'grade': 'basic',
            'best_for': ['beginners', 'Phalaenopsis', 'budget'],
            'drainage': 'good',
            'moisture_retention': 'high',
            'price_range': 'low',
            'notes': 'Mass-market option. Contains peat which breaks down faster. Repot more frequently.'
        },
        'orchiata_bark': {
            'name': 'Orchiata Bark',
            'ingredients': ['New Zealand pine bark (aged)'],
            'grade': 'premium',
            'best_for': ['epiphytes', 'long-lasting', 'professional growers'],
            'drainage': 'excellent',
            'moisture_retention': 'moderate',
            'price_range': 'high',
            'notes': 'Premium aged bark. Lasts 5+ years. Excellent structure. Available in 5 grades.'
        }
    }
    
    # DIY Mix Recipes
    DIY_RECIPES = {
        'warm_growers': {
            'name': 'Warm-Growing Epiphyte Mix',
            'components': {
                'bark (medium)': 60,
                'coconut_husk': 20,
                'perlite': 10,
                'charcoal': 10
            },
            'best_for': ['Phalaenopsis', 'Vanda', 'warm climates', 'tropical species'],
            'properties': 'Fast-draining with moderate moisture retention. Good aeration.',
            'care_notes': 'Water when top inch is dry. Fertilize weekly at 1/4 strength.'
        },
        'cool_growers': {
            'name': 'Cool-Growing Highland Mix',
            'components': {
                'bark (fine)': 40,
                'sphagnum_moss': 30,
                'perlite': 20,
                'charcoal': 10
            },
            'best_for': ['Masdevallia', 'Dracula', 'high-elevation species', 'cool conditions'],
            'properties': 'Higher moisture retention for species from cloud forests.',
            'care_notes': 'Keep consistently moist but not soggy. Water with distilled/RO water.'
        },
        'cattleya_mix': {
            'name': 'Classic Cattleya Mix',
            'components': {
                'bark (coarse)': 70,
                'charcoal': 15,
                'perlite': 15
            },
            'best_for': ['Cattleya', 'Laelia', 'Brassavola', 'intermediate growers'],
            'properties': 'Excellent drainage. Dries quickly. Good for plants that prefer dry periods.',
            'care_notes': 'Let dry between waterings. Water thoroughly then wait until nearly dry.'
        },
        'semi_hydro': {
            'name': 'Semi-Hydroponic Setup',
            'components': {
                'leca': 100
            },
            'best_for': ['beginners', 'consistent moisture', 'low maintenance', 'most epiphytes'],
            'properties': 'Self-watering reservoir. Consistent moisture. Prevents overwatering.',
            'care_notes': 'Maintain water level below pot holes. Flush monthly to prevent salt buildup.'
        },
        'mounted': {
            'name': 'Mounted Culture',
            'components': {
                'sphagnum_moss': 100
            },
            'mount_types': ['cork bark', 'tree fern slab', 'driftwood', 'grapewood'],
            'best_for': ['species that prefer drying', 'naturalistic display', 'warm growers'],
            'properties': 'Mimics natural epiphytic growth. Excellent air circulation.',
            'care_notes': 'Requires daily misting or high humidity (60%+). Perfect for advanced growers.'
        }
    }

class SubstrateRecommendationEngine:
    """
    Intelligent substrate recommendation based on microclimate analysis
    """
    
    def __init__(self):
        self.kb = SubstrateKnowledgeBase()
    
    def recommend_substrate(
        self,
        microclimate_data: Optional[Dict],
        grower_conditions: Optional[Dict] = None
    ) -> Dict:
        """
        Generate substrate recommendations based on species microclimate and grower conditions
        
        Args:
            microclimate_data: Output from MicroclimateAnalyzer
            grower_conditions: Dict with 'climate', 'humidity', 'experience', 'watering_frequency'
        
        Returns:
            Comprehensive substrate recommendations
        """
        recommendations = {
            'primary_recommendation': None,
            'alternative_options': [],
            'commercial_mixes': [],
            'diy_recipe': None,
            'mounting_option': None,
            'care_instructions': {},
            'rationale': []
        }
        
        # Handle insufficient microclimate data
        if not microclimate_data or microclimate_data.get('status') == 'insufficient_data':
            return self._generic_recommendations(grower_conditions)
        
        # Extract microclimate insights
        patterns = microclimate_data.get('patterns', {})
        elevation = patterns.get('elevation', {})
        coordinates = patterns.get('coordinates', {})
        
        # Determine growing conditions from microclimate
        growing_conditions = self._classify_growing_conditions(elevation, coordinates)
        
        # Match to substrate
        recommendations = self._match_substrate_to_conditions(
            growing_conditions,
            grower_conditions
        )
        
        return recommendations
    
    def _classify_growing_conditions(self, elevation: Dict, coordinates: Dict) -> Dict:
        """Classify species as warm/intermediate/cool grower"""
        conditions = {
            'temperature_preference': 'intermediate',
            'moisture_preference': 'moderate',
            'is_epiphyte': True  # Default assumption for orchids
        }
        
        # Temperature based on elevation
        if elevation.get('available'):
            mean_elev = elevation.get('mean_meters', 0)
            if mean_elev > 1500:
                conditions['temperature_preference'] = 'cool'
                conditions['moisture_preference'] = 'high'
            elif mean_elev < 800:
                conditions['temperature_preference'] = 'warm'
                conditions['moisture_preference'] = 'moderate'
            else:
                conditions['temperature_preference'] = 'intermediate'
                conditions['moisture_preference'] = 'moderate'
        
        # Moisture based on latitude (tropical = higher humidity)
        if coordinates.get('available'):
            lat = abs(coordinates['centroid']['lat'])
            if lat < 10:  # Equatorial
                conditions['moisture_preference'] = 'high'
            elif lat > 30:  # Subtropical
                conditions['moisture_preference'] = 'moderate'
        
        return conditions
    
    def _match_substrate_to_conditions(
        self,
        growing_conditions: Dict,
        grower_conditions: Optional[Dict]
    ) -> Dict:
        """Match substrate to growing and grower conditions"""
        temp_pref = growing_conditions['temperature_preference']
        moisture_pref = growing_conditions['moisture_preference']
        
        # Select DIY recipe
        if temp_pref == 'warm':
            diy = self.kb.DIY_RECIPES['warm_growers']
            commercial = ['repotme_classic', 'better_gro_special', 'orchiata_bark']
        elif temp_pref == 'cool':
            diy = self.kb.DIY_RECIPES['cool_growers']
            commercial = ['repotme_imperial', 'orchiata_bark']
        else:
            diy = self.kb.DIY_RECIPES['cattleya_mix']
            commercial = ['repotme_classic', 'orchiata_bark', 'better_gro_special']
        
        # Build recommendations
        recommendations = {
            'primary_recommendation': {
                'type': 'potted',
                'substrate': 'bark-based mix',
                'rationale': f"Based on microclimate analysis, this species is a {temp_pref}-grower with {moisture_pref} moisture needs."
            },
            'diy_recipe': {
                'name': diy['name'],
                'ingredients': diy['components'],
                'mixing_instructions': self._generate_mixing_instructions(diy['components']),
                'properties': diy['properties'],
                'care_notes': diy['care_notes']
            },
            'commercial_mixes': [
                self.kb.COMMERCIAL_MIXES[mix_id] for mix_id in commercial
            ],
            'alternative_options': self._generate_alternatives(temp_pref, moisture_pref),
            'mounting_option': self._generate_mounting_recommendation(growing_conditions),
            'care_instructions': self._generate_care_instructions(temp_pref, moisture_pref)
        }
        
        return recommendations
    
    def _generate_mixing_instructions(self, components: Dict[str, int]) -> str:
        """Generate mixing instructions for DIY recipe"""
        total_parts = sum(components.values())
        instructions = "Mix by volume:\n"
        for component, parts in components.items():
            percentage = (parts / total_parts) * 100
            instructions += f"  - {percentage:.0f}% {component}\n"
        
        instructions += "\nPrep: Soak bark components for 24 hours, rinse thoroughly, drain before mixing."
        return instructions
    
    def _generate_alternatives(self, temp_pref: str, moisture_pref: str) -> List[Dict]:
        """Generate alternative substrate options"""
        alternatives = []
        
        # Semi-hydro option
        alternatives.append({
            'method': 'Semi-Hydroponic (LECA)',
            'pros': ['Consistent moisture', 'Prevents overwatering', 'Low maintenance', 'Beginner-friendly'],
            'cons': ['Initial cost', 'Learning curve', 'Not suitable for all species'],
            'best_for': 'Growers who struggle with watering schedules'
        })
        
        # Mounted option
        alternatives.append({
            'method': 'Mounted on Cork/Wood',
            'pros': ['Naturalistic', 'Excellent air circulation', 'Beautiful display', 'Mimics native habitat'],
            'cons': ['Requires daily misting', 'Needs high humidity (60%+)', 'More maintenance'],
            'best_for': 'Advanced growers with humidity control'
        })
        
        # Sphagnum moss option (for high moisture)
        if moisture_pref == 'high':
            alternatives.append({
                'method': '100% Sphagnum Moss',
                'pros': ['Excellent moisture retention', 'Good for seedlings', 'Simple'],
                'cons': ['Easy to overwater', 'Poor drainage', 'Breaks down faster'],
                'best_for': 'High-humidity species and experienced growers'
            })
        
        return alternatives
    
    def _generate_mounting_recommendation(self, growing_conditions: Dict) -> Dict:
        """Generate mounting recommendation"""
        return {
            'suitable': True,
            'mount_types': ['Cork bark slab', 'Tree fern slab', 'Driftwood', 'Grapewood'],
            'preparation': 'Wrap roots in sphagnum moss, secure with fishing line or plant ties',
            'care': 'Mist daily or soak mount 2-3x weekly. Requires 60%+ humidity.',
            'advantages': 'Mimics natural epiphytic growth, excellent air circulation, beautiful display',
            'challenges': 'Higher maintenance, requires consistent humidity'
        }
    
    def _generate_care_instructions(self, temp_pref: str, moisture_pref: str) -> Dict:
        """Generate care instructions for each substrate type"""
        base_watering = {
            'warm': 'Water when top 1 inch is dry (typically every 5-7 days)',
            'intermediate': 'Water when top 1-2 inches are dry (typically every 7-10 days)',
            'cool': 'Keep consistently moist but not soggy (every 3-5 days)'
        }
        
        return {
            'bark_mix': {
                'watering': base_watering[temp_pref],
                'fertilizing': 'Weekly at 1/4 strength during growing season, monthly in winter',
                'repotting': 'Every 2-3 years or when bark breaks down',
                'signs_to_repot': ['Bark mushy or decomposed', 'Roots growing over pot edge', 'Poor drainage']
            },
            'semi_hydro': {
                'watering': 'Maintain 1-2 inch reservoir, flush system monthly',
                'fertilizing': 'Every watering at 1/8 strength (constant feed method)',
                'maintenance': 'Flush with plain water monthly to prevent salt buildup',
                'benefits': 'Self-regulating moisture, hard to overwater'
            },
            'mounted': {
                'watering': 'Mist daily, or soak entire mount 2-3x weekly',
                'humidity': 'Minimum 60%, ideally 70%+',
                'fertilizing': 'Foliar feed at 1/4 strength weekly',
                'display': 'Hang or display vertically for best air circulation'
            }
        }
    
    def _generic_recommendations(self, grower_conditions: Optional[Dict]) -> Dict:
        """Provide generic recommendations when microclimate data unavailable"""
        return {
            'status': 'generic',
            'note': 'Species-specific microclimate data unavailable. Providing general orchid substrate guidance.',
            'primary_recommendation': {
                'type': 'potted',
                'substrate': 'Medium-grade bark mix',
                'rationale': 'Standard orchid mix suitable for most epiphytic orchids (Phalaenopsis, Cattleya, Oncidium)'
            },
            'diy_recipe': self.kb.DIY_RECIPES['cattleya_mix'],
            'commercial_mixes': [
                self.kb.COMMERCIAL_MIXES['repotme_classic'],
                self.kb.COMMERCIAL_MIXES['better_gro_special'],
                self.kb.COMMERCIAL_MIXES['orchiata_bark']
            ],
            'alternative_options': [
                {
                    'method': 'Semi-Hydroponic (LECA)',
                    'recommendation': 'Excellent for beginners - prevents overwatering',
                    'setup': self.kb.DIY_RECIPES['semi_hydro']
                }
            ]
        }


def main():
    """Test substrate recommendation engine"""
    engine = SubstrateRecommendationEngine()
    
    print("=" * 70)
    print("🌱 SUBSTRATE RECOMMENDATION ENGINE")
    print("=" * 70)
    print()
    
    # Test with warm grower
    test_microclimate = {
        'status': 'success',
        'patterns': {
            'elevation': {
                'available': True,
                'mean_meters': 500
            },
            'coordinates': {
                'available': True,
                'centroid': {'lat': 5.0, 'lon': -75.0}
            }
        }
    }
    
    recommendations = engine.recommend_substrate(test_microclimate)
    
    print("📊 WARM-GROWING TROPICAL SPECIES")
    print(json.dumps(recommendations, indent=2))
    
    print()
    print("=" * 70)
    print("🏔️ COOL-GROWING HIGHLAND SPECIES")
    print("=" * 70)
    
    # Test with cool grower
    test_microclimate_cool = {
        'status': 'success',
        'patterns': {
            'elevation': {
                'available': True,
                'mean_meters': 2000
            },
            'coordinates': {
                'available': True,
                'centroid': {'lat': 0.5, 'lon': -78.0}
            }
        }
    }
    
    recommendations_cool = engine.recommend_substrate(test_microclimate_cool)
    print(json.dumps(recommendations_cool, indent=2))
    
    print()
    print("✅ Substrate recommendations generated!")


if __name__ == '__main__':
    main()
