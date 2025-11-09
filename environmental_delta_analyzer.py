#!/usr/bin/env python3
"""
Environmental Delta Analyzer
Compares species requirements vs. user's actual growing conditions
Provides actionable recommendations to bridge the gap
"""
from typing import Dict, List, Optional

class EnvironmentalDeltaAnalyzer:
    """
    Analyzes the difference between ideal species requirements and actual conditions
    Provides remediation suggestions
    """
    
    def __init__(self):
        pass
    
    def analyze_temperature_delta(
        self,
        species_requirement: Dict,
        actual_conditions: Dict
    ) -> Dict:
        """
        Analyze temperature mismatch
        
        Args:
            species_requirement: {'min': 65, 'max': 85, 'category': 'intermediate'}
            actual_conditions: {'avg': 60, 'min': 50, 'max': 70}
        
        Returns:
            Dict with analysis and recommendations
        """
        actual_avg = actual_conditions.get('avg', 70)
        species_min = species_requirement.get('min', 60)
        species_max = species_requirement.get('max', 80)
        
        # Calculate delta
        if actual_avg < species_min:
            delta = species_min - actual_avg
            status = 'too_cold'
            severity = 'critical' if delta > 10 else 'moderate' if delta > 5 else 'minor'
        elif actual_avg > species_max:
            delta = actual_avg - species_max
            status = 'too_warm'
            severity = 'critical' if delta > 10 else 'moderate' if delta > 5 else 'minor'
        else:
            delta = 0
            status = 'optimal'
            severity = 'none'
        
        # Generate recommendations
        recommendations = []
        if status == 'too_cold':
            if delta > 10:
                recommendations.append("⚠️ CRITICAL: Temperature significantly below ideal range")
                recommendations.append(f"💡 Add heating mat or space heater to raise temperature {delta:.0f}°F")
                recommendations.append("💡 Move to warmer location or greenhouse")
                recommendations.append("⏰ Reduce watering frequency in cooler conditions")
            elif delta > 5:
                recommendations.append(f"⚠️ Temperature {delta:.0f}°F below ideal - growth may be slower")
                recommendations.append("💡 Consider heating mat during cold months")
                recommendations.append("✨ Species may adapt but expect reduced flowering")
            else:
                recommendations.append(f"ℹ️ Slightly cooler ({delta:.0f}°F) - generally tolerable")
                recommendations.append("✨ Monitor for stress signs during winter")
        
        elif status == 'too_warm':
            if delta > 10:
                recommendations.append("⚠️ CRITICAL: Temperature significantly above ideal range")
                recommendations.append(f"💡 Add cooling/ventilation to reduce temperature {delta:.0f}°F")
                recommendations.append("💡 Increase humidity and air circulation")
                recommendations.append("🌡️ Provide afternoon shade or move to cooler location")
            elif delta > 5:
                recommendations.append(f"⚠️ Temperature {delta:.0f}°F above ideal")
                recommendations.append("💡 Increase air circulation and humidity")
                recommendations.append("💡 Shield from direct sun during hottest hours")
            else:
                recommendations.append(f"ℹ️ Slightly warmer ({delta:.0f}°F) - should adapt")
                recommendations.append("💧 May need more frequent watering")
        
        else:
            recommendations.append("✅ Temperature conditions are optimal for this species!")
        
        return {
            'status': status,
            'severity': severity,
            'delta': delta,
            'actual_avg': actual_avg,
            'species_range': {'min': species_min, 'max': species_max},
            'recommendations': recommendations
        }
    
    def analyze_humidity_delta(
        self,
        species_requirement: Optional[int],
        actual_conditions: Dict
    ) -> Dict:
        """
        Analyze humidity mismatch
        
        Args:
            species_requirement: Target humidity percentage (e.g., 60)
            actual_conditions: {'avg': 40, 'min': 30, 'max': 50}
        
        Returns:
            Dict with analysis and recommendations
        """
        if species_requirement is None:
            return {'status': 'unknown', 'recommendations': ['ℹ️ Species humidity preference not specified']}
        
        actual_avg = actual_conditions.get('avg', 50)
        delta = actual_avg - species_requirement
        
        if abs(delta) <= 10:
            status = 'optimal'
            severity = 'none'
        elif delta < -20:
            status = 'too_dry'
            severity = 'critical'
        elif delta < -10:
            status = 'too_dry'
            severity = 'moderate'
        elif delta > 20:
            status = 'too_humid'
            severity = 'moderate'
        elif delta > 10:
            status = 'too_humid'
            severity = 'minor'
        else:
            status = 'acceptable'
            severity = 'minor'
        
        recommendations = []
        if status == 'too_dry':
            if severity == 'critical':
                recommendations.append(f"⚠️ CRITICAL: Humidity {abs(delta):.0f}% below ideal ({species_requirement}%)")
                recommendations.append("💡 Add humidifier or humidity tray")
                recommendations.append("💡 Group plants together to increase local humidity")
                recommendations.append("💡 Switch to moisture-retentive substrate (more sphagnum moss)")
                recommendations.append("🌫️ Daily misting recommended")
            else:
                recommendations.append(f"⚠️ Humidity {abs(delta):.0f}% below ideal")
                recommendations.append("💡 Use humidity tray or pebble tray under pots")
                recommendations.append("💡 Mist 2-3 times daily")
                recommendations.append("💧 Consider adding sphagnum moss to substrate for moisture retention")
        
        elif status == 'too_humid':
            recommendations.append(f"ℹ️ Humidity {delta:.0f}% above ideal")
            recommendations.append("💡 Increase air circulation (fan recommended)")
            recommendations.append("💡 Use faster-draining substrate (more bark, less moss)")
            recommendations.append("⚠️ Watch for fungal/bacterial issues in high humidity")
        
        else:
            recommendations.append(f"✅ Humidity conditions {'optimal' if status == 'optimal' else 'acceptable'}")
        
        return {
            'status': status,
            'severity': severity,
            'delta': delta,
            'actual_avg': actual_avg,
            'species_requirement': species_requirement,
            'recommendations': recommendations
        }
    
    def analyze_light_delta(
        self,
        species_requirement: Optional[str],
        actual_conditions: str
    ) -> Dict:
        """
        Analyze light level mismatch
        
        Args:
            species_requirement: 'low', 'medium', 'bright', 'full_sun'
            actual_conditions: User's actual light level
        
        Returns:
            Dict with analysis and recommendations
        """
        # Light level hierarchy
        light_levels = {
            'shade': 0,
            'low': 1,
            'medium': 2,
            'bright': 3,
            'full_sun': 4
        }
        
        if not species_requirement:
            return {'status': 'unknown', 'recommendations': ['ℹ️ Species light preference not specified']}
        
        species_level = light_levels.get(species_requirement.lower(), 2)
        actual_level = light_levels.get(actual_conditions.lower(), 2)
        delta = actual_level - species_level
        
        if delta == 0:
            status = 'optimal'
            severity = 'none'
        elif abs(delta) == 1:
            status = 'acceptable'
            severity = 'minor'
        else:
            status = 'too_bright' if delta > 0 else 'too_dim'
            severity = 'critical' if abs(delta) > 2 else 'moderate'
        
        recommendations = []
        if status == 'too_dim':
            if severity == 'critical':
                recommendations.append(f"⚠️ CRITICAL: Light significantly below requirements")
                recommendations.append("💡 Add grow lights (LED recommended)")
                recommendations.append("💡 Move to brighter location (south-facing window)")
                recommendations.append("⚠️ Species unlikely to flower in low light")
            else:
                recommendations.append(f"⚠️ Light lower than ideal")
                recommendations.append("💡 Move closer to window or add supplemental lighting")
                recommendations.append("✨ Flowering may be reduced")
        
        elif status == 'too_bright':
            if severity == 'critical':
                recommendations.append(f"⚠️ CRITICAL: Light significantly above tolerance")
                recommendations.append("🌳 Add 50-70% shade cloth")
                recommendations.append("🌳 Move to shadier location")
                recommendations.append("⚠️ Leaves may burn or bleach in excessive light")
            else:
                recommendations.append(f"⚠️ Light brighter than ideal")
                recommendations.append("🌳 Add sheer curtain or 30% shade cloth")
                recommendations.append("💧 May need more frequent watering")
        
        else:
            recommendations.append(f"✅ Light conditions {'optimal' if status == 'optimal' else 'acceptable'}")
        
        return {
            'status': status,
            'severity': severity,
            'delta': delta,
            'actual_level': actual_conditions,
            'species_requirement': species_requirement,
            'recommendations': recommendations
        }
    
    def adjust_substrate_for_conditions(
        self,
        base_substrate_recs: Dict,
        environmental_deltas: Dict
    ) -> Dict:
        """
        Adjust substrate recommendations based on actual conditions
        
        Args:
            base_substrate_recs: Original substrate recommendations
            environmental_deltas: Delta analysis results
        
        Returns:
            Adjusted substrate recommendations
        """
        adjustments = []
        modified_recipe = base_substrate_recs.get('diy_recipe', {}).copy()
        
        # Adjust for humidity
        humidity_delta = environmental_deltas.get('humidity', {})
        if humidity_delta.get('status') == 'too_dry':
            adjustments.append({
                'reason': 'Low humidity environment',
                'change': 'Increase moisture retention',
                'suggestion': 'Add 10-20% more sphagnum moss, reduce perlite'
            })
        elif humidity_delta.get('status') == 'too_humid':
            adjustments.append({
                'reason': 'High humidity environment',
                'change': 'Increase drainage',
                'suggestion': 'Add 10-20% more perlite/lava rock, reduce moss'
            })
        
        # Adjust for temperature
        temp_delta = environmental_deltas.get('temperature', {})
        if temp_delta.get('status') == 'too_warm':
            adjustments.append({
                'reason': 'Warmer conditions',
                'change': 'Faster drainage needed',
                'suggestion': 'Water more frequently, ensure excellent air circulation'
            })
        elif temp_delta.get('status') == 'too_cold':
            adjustments.append({
                'reason': 'Cooler conditions',
                'change': 'Reduce moisture retention',
                'suggestion': 'Water less frequently, allow to dry more between waterings'
            })
        
        # Adjust for light
        light_delta = environmental_deltas.get('light', {})
        if light_delta.get('status') == 'too_bright':
            adjustments.append({
                'reason': 'High light conditions',
                'change': 'More frequent watering',
                'suggestion': 'Plants dry faster in bright light - check moisture daily'
            })
        
        return {
            'base_recommendations': base_substrate_recs,
            'environmental_adjustments': adjustments,
            'modified_recipe': modified_recipe if adjustments else None,
            'summary': f"{len(adjustments)} substrate adjustments based on your growing conditions" if adjustments else "Base substrate recommendations suitable for your conditions"
        }
    
    def generate_comprehensive_analysis(
        self,
        species_data: Dict,
        growing_environment: Dict
    ) -> Dict:
        """
        Generate complete environmental compatibility analysis
        
        Args:
            species_data: Requirements from Baker/AOS/microclimate
            growing_environment: User's actual conditions
        
        Returns:
            Complete delta analysis with recommendations
        """
        # Temperature analysis
        species_temp = species_data.get('temperature', {})
        temp_analysis = self.analyze_temperature_delta(
            species_requirement=species_temp,
            actual_conditions=growing_environment.get('temperature', {})
        )
        
        # Humidity analysis
        species_humidity = species_data.get('humidity')
        humidity_analysis = self.analyze_humidity_delta(
            species_requirement=species_humidity,
            actual_conditions=growing_environment.get('humidity', {})
        )
        
        # Light analysis
        species_light = species_data.get('light')
        light_analysis = self.analyze_light_delta(
            species_requirement=species_light,
            actual_conditions=growing_environment.get('light_level', 'medium')
        )
        
        # Calculate overall compatibility score
        severity_scores = {'none': 4, 'minor': 3, 'moderate': 2, 'critical': 1}
        temp_score = severity_scores.get(temp_analysis['severity'], 2)
        humidity_score = severity_scores.get(humidity_analysis.get('severity', 'minor'), 2)
        light_score = severity_scores.get(light_analysis.get('severity', 'minor'), 2)
        
        overall_score = (temp_score + humidity_score + light_score) / 12 * 100  # 0-100 scale
        
        if overall_score >= 75:
            compatibility = 'excellent'
        elif overall_score >= 60:
            compatibility = 'good'
        elif overall_score >= 40:
            compatibility = 'challenging'
        else:
            compatibility = 'not_recommended'
        
        return {
            'compatibility_score': round(overall_score, 1),
            'compatibility_rating': compatibility,
            'temperature_delta': temp_analysis,
            'humidity_delta': humidity_analysis,
            'light_delta': light_analysis,
            'growing_environment_name': growing_environment.get('name', 'Your Growing Area'),
            'summary': self._generate_summary(compatibility, temp_analysis, humidity_analysis, light_analysis)
        }
    
    def _generate_summary(
        self,
        compatibility: str,
        temp: Dict,
        humidity: Dict,
        light: Dict
    ) -> str:
        """Generate human-readable summary"""
        if compatibility == 'excellent':
            return "✅ Your growing conditions are excellent for this species! Few or no adjustments needed."
        elif compatibility == 'good':
            return "👍 Your growing conditions are suitable with minor adjustments."
        elif compatibility == 'challenging':
            return "⚠️ Growing this species in your conditions will require significant environmental modifications."
        else:
            return "❌ Your growing conditions are not recommended for this species. Consider alternative species or major environment changes."


def main():
    """Test environmental delta analyzer"""
    analyzer = EnvironmentalDeltaAnalyzer()
    
    print("=" * 70)
    print("🔬 ENVIRONMENTAL DELTA ANALYZER")
    print("=" * 70)
    print()
    
    # Test case: Cool-growing species in warm greenhouse
    species_requirements = {
        'temperature': {'min': 55, 'max': 70, 'category': 'cool'},
        'humidity': 70,
        'light': 'bright'
    }
    
    actual_conditions = {
        'name': 'My Warm Greenhouse',
        'temperature': {'avg': 78, 'min': 70, 'max': 85},
        'humidity': {'avg': 50, 'min': 40, 'max': 60},
        'light_level': 'full_sun'
    }
    
    analysis = analyzer.generate_comprehensive_analysis(
        species_data=species_requirements,
        growing_environment=actual_conditions
    )
    
    print(f"Compatibility Score: {analysis['compatibility_score']}/100 ({analysis['compatibility_rating'].upper()})")
    print(f"Summary: {analysis['summary']}")
    print()
    
    print("TEMPERATURE ANALYSIS:")
    for rec in analysis['temperature_delta']['recommendations']:
        print(f"  {rec}")
    print()
    
    print("HUMIDITY ANALYSIS:")
    for rec in analysis['humidity_delta']['recommendations']:
        print(f"  {rec}")
    print()
    
    print("LIGHT ANALYSIS:")
    for rec in analysis['light_delta']['recommendations']:
        print(f"  {rec}")
    
    print()
    print("✅ Delta analysis complete!")


if __name__ == '__main__':
    main()
