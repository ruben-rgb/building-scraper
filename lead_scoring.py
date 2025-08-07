#!/usr/bin/env python3
"""
Lead Scoring System for Commercial/Industrial Building Energy Efficiency

This module provides comprehensive lead scoring algorithms to identify
the most promising opportunities for energy efficiency solutions,
particularly focusing on HVAC systems.

Scoring factors include:
- Energy savings potential
- Building characteristics (size, age, type)
- Accessibility (contact information availability)
- Project viability and urgency
- Market factors
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

@dataclass
class ScoringWeights:
    """Configurable weights for different scoring factors"""
    energy_potential: float = 0.40      # Energy savings opportunity
    accessibility: float = 0.25         # Ease of reaching decision maker
    project_size: float = 0.20          # Project value/scale
    urgency: float = 0.10               # Timing factors
    market_factors: float = 0.05        # Local market conditions

class EnergyEfficiencyScorer:
    """Main class for scoring building leads for energy efficiency potential"""
    
    def __init__(self, weights: ScoringWeights = None):
        self.weights = weights or ScoringWeights()
        
        # Energy consumption factors by building type (kWh/sqft/year)
        self.energy_intensity = {
            'office': 15.0,
            'retail': 20.0,
            'warehouse': 8.0,
            'manufacturing': 25.0,
            'data_center': 200.0,
            'healthcare': 30.0,
            'hospitality': 22.0,
            'education': 12.0,
            'mixed_use': 18.0,
            'commercial': 16.0  # Default
        }
        
        # HVAC energy percentage by building type
        self.hvac_percentage = {
            'office': 0.45,
            'retail': 0.40,
            'warehouse': 0.30,
            'manufacturing': 0.35,
            'data_center': 0.60,
            'healthcare': 0.50,
            'hospitality': 0.45,
            'education': 0.40,
            'mixed_use': 0.42,
            'commercial': 0.40
        }
        
        # Efficiency improvement potential by building age
        self.age_efficiency_potential = {
            (0, 5): 0.10,      # New buildings - minimal opportunity
            (6, 10): 0.15,     # Recent buildings - some opportunity
            (11, 20): 0.25,    # Moderate age - good opportunity
            (21, 30): 0.35,    # Older buildings - high opportunity
            (31, 50): 0.45,    # Very old - very high opportunity
            (51, 100): 0.35    # Historic - high but constrained
        }
    
    def calculate_energy_savings_potential(self, building_data: Dict) -> float:
        """
        Calculate energy savings potential score (0-100)
        Higher scores indicate greater opportunity for energy savings
        """
        score = 0.0
        
        # Base score from building type
        building_type = building_data.get('building_type', 'commercial').lower()
        base_intensity = self.energy_intensity.get(building_type, 16.0)
        hvac_portion = self.hvac_percentage.get(building_type, 0.40)
        
        # Size factor (larger buildings = more total savings potential)
        square_footage = building_data.get('square_footage', 0)
        if square_footage:
            if square_footage > 200000:
                size_multiplier = 1.0
            elif square_footage > 100000:
                size_multiplier = 0.9
            elif square_footage > 50000:
                size_multiplier = 0.8
            elif square_footage > 25000:
                size_multiplier = 0.7
            elif square_footage > 10000:
                size_multiplier = 0.6
            else:
                size_multiplier = 0.4
                
            # Calculate annual HVAC energy consumption
            annual_hvac_kwh = square_footage * base_intensity * hvac_portion
            
            # Base energy score (0-40 points)
            if annual_hvac_kwh > 1000000:  # > 1M kWh/year
                score += 40
            elif annual_hvac_kwh > 500000:
                score += 35
            elif annual_hvac_kwh > 250000:
                score += 30
            elif annual_hvac_kwh > 100000:
                score += 25
            elif annual_hvac_kwh > 50000:
                score += 20
            else:
                score += 15
                
            score *= size_multiplier
        
        # Age factor (older buildings = more opportunity)
        year_built = building_data.get('year_built')
        if year_built:
            building_age = datetime.now().year - year_built
            age_potential = self._get_age_potential(building_age)
            score += age_potential * 30  # Up to 30 points for age
        
        # Building type bonus for energy-intensive types
        if building_type in ['manufacturing', 'data_center', 'healthcare']:
            score += 15
        elif building_type in ['office', 'retail', 'hospitality']:
            score += 10
        elif building_type in ['warehouse', 'education']:
            score += 5
        
        # HVAC system age estimation bonus
        hvac_urgency = self._estimate_hvac_urgency(building_data)
        score += hvac_urgency * 15  # Up to 15 points for equipment urgency
        
        return min(score, 100.0)
    
    def _get_age_potential(self, building_age: int) -> float:
        """Get efficiency potential based on building age"""
        for (min_age, max_age), potential in self.age_efficiency_potential.items():
            if min_age <= building_age <= max_age:
                return potential
        return 0.35  # Default for very old buildings
    
    def _estimate_hvac_urgency(self, building_data: Dict) -> float:
        """
        Estimate HVAC equipment replacement urgency (0-1.0)
        Based on building age and permit history
        """
        urgency = 0.0
        
        # Basic age-based urgency
        year_built = building_data.get('year_built')
        if year_built:
            building_age = datetime.now().year - year_built
            # Assume HVAC replaced every 15-20 years
            hvac_cycles = building_age // 17  # Average cycle length
            years_since_replacement = building_age % 17
            
            if years_since_replacement > 15:
                urgency = 1.0  # Very urgent
            elif years_since_replacement > 12:
                urgency = 0.8  # High urgency
            elif years_since_replacement > 8:
                urgency = 0.6  # Medium urgency
            else:
                urgency = 0.3  # Lower urgency
        
        # Boost urgency for very energy-intensive types
        building_type = building_data.get('building_type', '').lower()
        if building_type in ['data_center', 'manufacturing']:
            urgency += 0.2
        
        # Check for recent HVAC permits (reduces urgency)
        permit_type = building_data.get('permit_type', '').lower()
        if 'hvac' in permit_type or 'mechanical' in permit_type:
            urgency *= 0.3  # Recent HVAC work reduces urgency
        
        return min(urgency, 1.0)
    
    def calculate_accessibility_score(self, building_data: Dict) -> float:
        """
        Calculate how accessible the decision maker is (0-100)
        Higher scores = easier to reach and engage
        """
        score = 20.0  # Base accessibility score
        
        # Contact information availability
        if building_data.get('contact_phone'):
            score += 25
        if building_data.get('contact_email'):
            score += 25
        if building_data.get('website'):
            score += 10
        
        # Owner information quality
        owner_name = building_data.get('owner_name', '')
        if owner_name:
            score += 15
            # Individual owners may be easier to reach than corporations
            if any(indicator in owner_name.lower() for indicator in ['llc', 'inc', 'corp', 'company']):
                score += 5  # Corporate contact
            else:
                score += 10  # Individual contact (often easier)
        
        # Management company presence
        if building_data.get('management_company'):
            score += 15  # Professional management suggests organized decision-making
        
        # Data source reliability
        data_source = building_data.get('data_source', '')
        if data_source in ['commercial_real_estate', 'business_directory']:
            score += 10  # These sources often have current contact info
        elif data_source == 'county_assessor':
            score += 5   # Government data is accurate but may be outdated
        
        return min(score, 100.0)
    
    def calculate_project_size_score(self, building_data: Dict) -> float:
        """
        Calculate project size/value potential (0-100)
        Larger projects = higher scores
        """
        score = 0.0
        
        square_footage = building_data.get('square_footage', 0)
        if square_footage:
            if square_footage > 500000:
                score = 100
            elif square_footage > 300000:
                score = 90
            elif square_footage > 200000:
                score = 80
            elif square_footage > 100000:
                score = 70
            elif square_footage > 50000:
                score = 60
            elif square_footage > 25000:
                score = 50
            elif square_footage > 10000:
                score = 40
            else:
                score = 30
        
        # Adjust based on building type complexity
        building_type = building_data.get('building_type', '').lower()
        if building_type in ['manufacturing', 'data_center', 'healthcare']:
            score *= 1.2  # Complex buildings = higher project value
        elif building_type in ['warehouse']:
            score *= 0.8  # Simpler systems = lower project value
        
        # Construction value from permits
        construction_value = building_data.get('construction_value', 0)
        if construction_value:
            if construction_value > 10000000:  # $10M+
                score += 20
            elif construction_value > 5000000:
                score += 15
            elif construction_value > 1000000:
                score += 10
            else:
                score += 5
        
        return min(score, 100.0)
    
    def calculate_urgency_score(self, building_data: Dict) -> float:
        """
        Calculate urgency factors (0-100)
        Higher scores = more time-sensitive opportunities
        """
        score = 20.0  # Base urgency
        
        # HVAC equipment age urgency
        hvac_urgency = self._estimate_hvac_urgency(building_data)
        score += hvac_urgency * 40  # Up to 40 points for equipment urgency
        
        # Recent permit activity (indicates active building improvements)
        permit_date = building_data.get('permit_date')
        if permit_date:
            try:
                permit_dt = datetime.fromisoformat(permit_date)
                days_ago = (datetime.now() - permit_dt).days
                if days_ago < 30:
                    score += 25  # Very recent activity
                elif days_ago < 90:
                    score += 15  # Recent activity
                elif days_ago < 365:
                    score += 10  # Activity within last year
            except:
                pass
        
        # Building type urgency factors
        building_type = building_data.get('building_type', '').lower()
        if building_type == 'data_center':
            score += 15  # Data centers need reliable cooling
        elif building_type == 'healthcare':
            score += 12  # Healthcare facilities can't afford downtime
        elif building_type == 'manufacturing':
            score += 10  # Manufacturing often has critical temperature requirements
        
        # Energy efficiency rating (poor ratings = more urgent)
        energy_rating = building_data.get('energy_efficiency_rating', '')
        if energy_rating:
            if 'f' in energy_rating.lower() or 'poor' in energy_rating.lower():
                score += 20
            elif 'c' in energy_rating.lower() or 'average' in energy_rating.lower():
                score += 10
        
        return min(score, 100.0)
    
    def calculate_market_factors_score(self, building_data: Dict) -> float:
        """
        Calculate market factors that might influence success (0-100)
        Considers local utility programs, climate, regulations
        """
        score = 50.0  # Base market score
        
        # State-level factors
        state = building_data.get('state', '').upper()
        
        # States with strong energy efficiency programs
        efficiency_leaders = ['CA', 'NY', 'MA', 'CT', 'RI', 'VT', 'WA', 'OR']
        if state in efficiency_leaders:
            score += 20
        
        # States with utility rebate programs
        rebate_states = ['TX', 'FL', 'IL', 'PA', 'OH', 'MI', 'GA', 'NC', 'VA']
        if state in rebate_states:
            score += 15
        
        # Climate factors (extreme climates = more HVAC usage)
        hot_climate_states = ['TX', 'FL', 'AZ', 'NV', 'CA', 'GA', 'LA', 'AL', 'MS', 'SC']
        cold_climate_states = ['MN', 'WI', 'ND', 'SD', 'MT', 'ME', 'NH', 'VT', 'NY', 'MI']
        
        if state in hot_climate_states or state in cold_climate_states:
            score += 10  # Extreme climates drive more HVAC usage
        
        # Urban vs rural (urban areas often have more stringent efficiency requirements)
        city = building_data.get('city', '').lower()
        major_cities = ['new york', 'los angeles', 'chicago', 'houston', 'phoenix', 
                       'philadelphia', 'san antonio', 'san diego', 'dallas', 'san jose',
                       'austin', 'jacksonville', 'fort worth', 'columbus', 'charlotte',
                       'san francisco', 'indianapolis', 'seattle', 'denver', 'washington']
        
        if any(major_city in city for major_city in major_cities):
            score += 15  # Major cities often have efficiency mandates
        
        return min(score, 100.0)
    
    def calculate_overall_score(self, building_data: Dict) -> Tuple[float, Dict[str, float]]:
        """
        Calculate overall lead score using weighted combination of factors
        Returns (overall_score, individual_scores)
        """
        # Calculate individual scores
        energy_score = self.calculate_energy_savings_potential(building_data)
        accessibility_score = self.calculate_accessibility_score(building_data)
        project_size_score = self.calculate_project_size_score(building_data)
        urgency_score = self.calculate_urgency_score(building_data)
        market_score = self.calculate_market_factors_score(building_data)
        
        # Calculate weighted overall score
        overall_score = (
            energy_score * self.weights.energy_potential +
            accessibility_score * self.weights.accessibility +
            project_size_score * self.weights.project_size +
            urgency_score * self.weights.urgency +
            market_score * self.weights.market_factors
        )
        
        individual_scores = {
            'energy_savings_potential': energy_score,
            'accessibility_score': accessibility_score,
            'project_size_score': project_size_score,
            'urgency_score': urgency_score,
            'market_factors_score': market_score,
            'overall_lead_score': overall_score
        }
        
        return overall_score, individual_scores
    
    def estimate_annual_energy_cost(self, building_data: Dict, electricity_rate: float = 0.12) -> Optional[float]:
        """
        Estimate annual energy costs for the building
        Used for calculating potential savings value
        """
        square_footage = building_data.get('square_footage')
        building_type = building_data.get('building_type', 'commercial').lower()
        
        if not square_footage:
            return None
        
        # Get energy intensity for building type
        intensity = self.energy_intensity.get(building_type, 16.0)
        
        # Calculate annual energy consumption
        annual_kwh = square_footage * intensity
        
        # Calculate annual cost
        annual_cost = annual_kwh * electricity_rate
        
        return annual_cost
    
    def estimate_hvac_savings_potential(self, building_data: Dict, electricity_rate: float = 0.12) -> Dict[str, float]:
        """
        Estimate potential HVAC energy and cost savings
        Returns dict with savings estimates
        """
        annual_cost = self.estimate_annual_energy_cost(building_data, electricity_rate)
        
        if not annual_cost:
            return {}
        
        # Get HVAC portion of energy use
        building_type = building_data.get('building_type', 'commercial').lower()
        hvac_portion = self.hvac_percentage.get(building_type, 0.40)
        hvac_annual_cost = annual_cost * hvac_portion
        
        # Get efficiency improvement potential based on building age
        year_built = building_data.get('year_built')
        if year_built:
            building_age = datetime.now().year - year_built
            improvement_potential = self._get_age_potential(building_age)
        else:
            improvement_potential = 0.25  # Default 25% improvement potential
        
        # Calculate potential savings
        annual_hvac_savings = hvac_annual_cost * improvement_potential
        
        # Project savings over equipment lifetime (15 years)
        lifetime_savings = annual_hvac_savings * 15
        
        return {
            'annual_total_energy_cost': annual_cost,
            'annual_hvac_energy_cost': hvac_annual_cost,
            'improvement_potential_percent': improvement_potential * 100,
            'estimated_annual_hvac_savings': annual_hvac_savings,
            'estimated_lifetime_savings': lifetime_savings
        }

class LeadFilter:
    """Filter leads based on various criteria"""
    
    def __init__(self):
        pass
    
    def filter_by_score(self, leads: List[Dict], min_score: float = 50.0) -> List[Dict]:
        """Filter leads by minimum overall score"""
        return [lead for lead in leads if lead.get('overall_lead_score', 0) >= min_score]
    
    def filter_by_size(self, leads: List[Dict], min_sqft: int = 10000, max_sqft: int = None) -> List[Dict]:
        """Filter leads by building size"""
        filtered = []
        for lead in leads:
            sqft = lead.get('square_footage', 0)
            if sqft >= min_sqft:
                if max_sqft is None or sqft <= max_sqft:
                    filtered.append(lead)
        return filtered
    
    def filter_by_building_type(self, leads: List[Dict], building_types: List[str]) -> List[Dict]:
        """Filter leads by building type"""
        building_types_lower = [bt.lower() for bt in building_types]
        return [lead for lead in leads 
                if lead.get('building_type', '').lower() in building_types_lower]
    
    def filter_by_age(self, leads: List[Dict], min_age: int = 0, max_age: int = 100) -> List[Dict]:
        """Filter leads by building age"""
        current_year = datetime.now().year
        filtered = []
        
        for lead in leads:
            year_built = lead.get('year_built')
            if year_built:
                age = current_year - year_built
                if min_age <= age <= max_age:
                    filtered.append(lead)
            elif min_age == 0:  # Include buildings with unknown age if min_age is 0
                filtered.append(lead)
        
        return filtered
    
    def filter_by_location(self, leads: List[Dict], states: List[str] = None, cities: List[str] = None) -> List[Dict]:
        """Filter leads by geographic location"""
        filtered = leads
        
        if states:
            states_upper = [s.upper() for s in states]
            filtered = [lead for lead in filtered 
                       if lead.get('state', '').upper() in states_upper]
        
        if cities:
            cities_lower = [c.lower() for c in cities]
            filtered = [lead for lead in filtered 
                       if lead.get('city', '').lower() in cities_lower]
        
        return filtered
    
    def filter_by_contact_availability(self, leads: List[Dict], require_phone: bool = False, 
                                     require_email: bool = False) -> List[Dict]:
        """Filter leads by contact information availability"""
        filtered = []
        
        for lead in leads:
            include = True
            
            if require_phone and not lead.get('contact_phone'):
                include = False
            
            if require_email and not lead.get('contact_email'):
                include = False
            
            if include:
                filtered.append(lead)
        
        return filtered
    
    def get_top_leads(self, leads: List[Dict], limit: int = 100, 
                     sort_by: str = 'overall_lead_score') -> List[Dict]:
        """Get top leads sorted by specified field"""
        sorted_leads = sorted(leads, 
                            key=lambda x: x.get(sort_by, 0), 
                            reverse=True)
        return sorted_leads[:limit]