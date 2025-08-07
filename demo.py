#!/usr/bin/env python3
"""
Simplified Demo of Building Lead Generation Agent

This demo script shows the core functionality of the building lead generation
agent without requiring external dependencies like requests, pandas, etc.
It demonstrates the scoring algorithms and data structures.
"""

import json
import sqlite3
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple

@dataclass
class BuildingLead:
    """Data structure for building lead information"""
    # Basic identification
    property_id: str
    address: str
    city: str
    state: str
    zip_code: str
    county: str
    
    # Building characteristics
    building_type: str
    square_footage: Optional[int]
    year_built: Optional[int]
    stories: Optional[int]
    
    # Ownership/Contact info
    owner_name: Optional[str]
    owner_type: Optional[str]
    management_company: Optional[str]
    contact_phone: Optional[str]
    contact_email: Optional[str]
    
    # HVAC/Energy characteristics
    hvac_type: Optional[str]
    heating_fuel: Optional[str]
    cooling_type: Optional[str]
    estimated_energy_cost: Optional[float]
    energy_efficiency_rating: Optional[str]
    
    # Metadata
    data_source: str
    last_updated: str
    
    # Lead scoring factors
    energy_savings_potential: float = 0.0
    accessibility_score: float = 0.0
    project_size_score: float = 0.0
    urgency_score: float = 0.0
    overall_lead_score: float = 0.0
    notes: Optional[str] = None

class DemoScorer:
    """Simplified scoring system for demo purposes"""
    
    def __init__(self):
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
            'commercial': 16.0
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
    
    def score_energy_potential(self, building: Dict) -> float:
        """Calculate energy savings potential score"""
        score = 0.0
        building_type = building.get('building_type', 'commercial').lower()
        square_footage = building.get('square_footage', 0)
        year_built = building.get('year_built')
        
        # Size-based scoring
        if square_footage > 200000:
            score += 40
        elif square_footage > 100000:
            score += 35
        elif square_footage > 50000:
            score += 30
        elif square_footage > 25000:
            score += 25
        else:
            score += 15
        
        # Age-based scoring
        if year_built:
            age = datetime.now().year - year_built
            if age > 30:
                score += 25
            elif age > 20:
                score += 20
            elif age > 10:
                score += 15
            else:
                score += 5
        
        # Building type scoring
        type_scores = {
            'manufacturing': 25,
            'data_center': 30,
            'healthcare': 20,
            'hospitality': 20,
            'office': 15,
            'retail': 15,
            'warehouse': 10
        }
        score += type_scores.get(building_type, 10)
        
        return min(score, 100.0)
    
    def score_accessibility(self, building: Dict) -> float:
        """Calculate accessibility score"""
        score = 20.0
        
        if building.get('contact_phone'):
            score += 25
        if building.get('contact_email'):
            score += 25
        if building.get('owner_name'):
            score += 20
        if building.get('management_company'):
            score += 10
        
        return min(score, 100.0)
    
    def score_project_size(self, building: Dict) -> float:
        """Calculate project size score"""
        square_footage = building.get('square_footage', 0)
        
        if square_footage > 500000:
            return 100
        elif square_footage > 300000:
            return 90
        elif square_footage > 200000:
            return 80
        elif square_footage > 100000:
            return 70
        elif square_footage > 50000:
            return 60
        elif square_footage > 25000:
            return 50
        elif square_footage > 10000:
            return 40
        else:
            return 30
    
    def score_urgency(self, building: Dict) -> float:
        """Calculate urgency score"""
        score = 20.0
        building_type = building.get('building_type', '').lower()
        year_built = building.get('year_built')
        
        # HVAC age estimation
        if year_built:
            age = datetime.now().year - year_built
            hvac_age = age % 17  # Assume 17-year replacement cycle
            if hvac_age > 15:
                score += 30
            elif hvac_age > 12:
                score += 20
            elif hvac_age > 8:
                score += 15
            else:
                score += 5
        
        # Critical facility types
        if building_type == 'data_center':
            score += 15
        elif building_type == 'healthcare':
            score += 12
        elif building_type == 'manufacturing':
            score += 10
        
        return min(score, 100.0)
    
    def calculate_overall_score(self, building: Dict) -> Tuple[float, Dict[str, float]]:
        """Calculate overall weighted score"""
        energy_score = self.score_energy_potential(building)
        accessibility_score = self.score_accessibility(building)
        project_size_score = self.score_project_size(building)
        urgency_score = self.score_urgency(building)
        
        # Weighted combination
        overall_score = (
            energy_score * 0.40 +
            accessibility_score * 0.25 +
            project_size_score * 0.20 +
            urgency_score * 0.15
        )
        
        scores = {
            'energy_savings_potential': energy_score,
            'accessibility_score': accessibility_score,
            'project_size_score': project_size_score,
            'urgency_score': urgency_score,
            'overall_lead_score': overall_score
        }
        
        return overall_score, scores
    
    def estimate_savings(self, building: Dict, electricity_rate: float = 0.12) -> Dict[str, float]:
        """Estimate HVAC savings potential"""
        square_footage = building.get('square_footage', 0)
        building_type = building.get('building_type', 'commercial').lower()
        year_built = building.get('year_built')
        
        if not square_footage:
            return {}
        
        # Calculate energy usage
        intensity = self.energy_intensity.get(building_type, 16.0)
        hvac_portion = self.hvac_percentage.get(building_type, 0.40)
        
        annual_kwh = square_footage * intensity
        annual_cost = annual_kwh * electricity_rate
        hvac_annual_cost = annual_cost * hvac_portion
        
        # Improvement potential based on age
        if year_built:
            age = datetime.now().year - year_built
            if age > 30:
                improvement = 0.35
            elif age > 20:
                improvement = 0.25
            elif age > 10:
                improvement = 0.20
            else:
                improvement = 0.15
        else:
            improvement = 0.25
        
        annual_savings = hvac_annual_cost * improvement
        lifetime_savings = annual_savings * 15  # 15-year equipment life
        
        return {
            'annual_total_energy_cost': annual_cost,
            'annual_hvac_energy_cost': hvac_annual_cost,
            'improvement_potential_percent': improvement * 100,
            'estimated_annual_hvac_savings': annual_savings,
            'estimated_lifetime_savings': lifetime_savings
        }

def create_demo_leads() -> List[Dict]:
    """Create sample building leads for demonstration"""
    return [
        {
            'property_id': 'DEMO_001',
            'address': '123 Business Park Dr, Austin, TX 78701',
            'city': 'Austin',
            'state': 'TX',
            'zip_code': '78701',
            'county': 'Travis County',
            'building_type': 'office',
            'square_footage': 85000,
            'year_built': 1998,
            'stories': 5,
            'owner_name': 'Austin Office Properties LLC',
            'owner_type': 'LLC',
            'management_company': 'Premier Property Management',
            'contact_phone': '(512) 555-0123',
            'contact_email': 'leasing@austinoffice.com',
            'hvac_type': 'Central Air',
            'heating_fuel': 'Electric',
            'cooling_type': 'Chilled Water',
            'data_source': 'demo',
            'last_updated': datetime.now().isoformat(),
            'notes': 'Multi-tenant office building with aging HVAC system'
        },
        {
            'property_id': 'DEMO_002',
            'address': '456 Industrial Way, Seattle, WA 98101',
            'city': 'Seattle',
            'state': 'WA',
            'zip_code': '98101',
            'county': 'King County',
            'building_type': 'manufacturing',
            'square_footage': 150000,
            'year_built': 1985,
            'stories': 2,
            'owner_name': 'Pacific Manufacturing Corp',
            'owner_type': 'Corporation',
            'contact_phone': '(206) 555-0456',
            'hvac_type': 'Rooftop Units',
            'heating_fuel': 'Natural Gas',
            'cooling_type': 'DX Cooling',
            'data_source': 'demo',
            'last_updated': datetime.now().isoformat(),
            'notes': 'Large manufacturing facility with high energy usage'
        },
        {
            'property_id': 'DEMO_003',
            'address': '789 Retail Center, Atlanta, GA 30309',
            'city': 'Atlanta',
            'state': 'GA',
            'zip_code': '30309',
            'county': 'Fulton County',
            'building_type': 'retail',
            'square_footage': 45000,
            'year_built': 2005,
            'stories': 1,
            'owner_name': 'Southern Retail Investment Trust',
            'owner_type': 'Trust',
            'management_company': 'Retail Management Solutions',
            'contact_phone': '(404) 555-0789',
            'contact_email': 'management@southernretail.com',
            'hvac_type': 'Split Systems',
            'heating_fuel': 'Heat Pump',
            'cooling_type': 'Heat Pump',
            'data_source': 'demo',
            'last_updated': datetime.now().isoformat(),
            'notes': 'Modern retail space with moderate efficiency potential'
        },
        {
            'property_id': 'DEMO_004',
            'address': '321 Data Center Blvd, Phoenix, AZ 85001',
            'city': 'Phoenix',
            'state': 'AZ',
            'zip_code': '85001',
            'county': 'Maricopa County',
            'building_type': 'data_center',
            'square_footage': 75000,
            'year_built': 2010,
            'stories': 1,
            'owner_name': 'Desert Data Holdings',
            'owner_type': 'LLC',
            'contact_phone': '(602) 555-0321',
            'contact_email': 'facilities@desertdata.com',
            'hvac_type': 'Precision Cooling',
            'heating_fuel': 'Electric',
            'cooling_type': 'Chilled Water',
            'energy_efficiency_rating': 'ENERGY STAR 85',
            'data_source': 'demo',
            'last_updated': datetime.now().isoformat(),
            'notes': 'High-efficiency data center with continuous cooling requirements'
        },
        {
            'property_id': 'DEMO_005',
            'address': '654 Medical Plaza, Denver, CO 80202',
            'city': 'Denver',
            'state': 'CO',
            'zip_code': '80202',
            'county': 'Denver County',
            'building_type': 'healthcare',
            'square_footage': 120000,
            'year_built': 1992,
            'stories': 8,
            'owner_name': 'Mountain Medical Properties',
            'owner_type': 'Corporation',
            'management_company': 'Healthcare Facility Management',
            'contact_phone': '(303) 555-0654',
            'hvac_type': 'VAV Systems',
            'heating_fuel': 'Natural Gas',
            'cooling_type': 'Centrifugal Chiller',
            'data_source': 'demo',
            'last_updated': datetime.now().isoformat(),
            'notes': 'Large medical facility with critical HVAC requirements'
        }
    ]

def export_to_csv(leads: List[Dict], filename: str):
    """Export leads to CSV format"""
    if not leads:
        print("No leads to export")
        return
    
    # Get all possible field names
    all_fields = set()
    for lead in leads:
        all_fields.update(lead.keys())
    
    fields = sorted(all_fields)
    
    with open(filename, 'w') as f:
        # Write header
        f.write(','.join(fields) + '\n')
        
        # Write data
        for lead in leads:
            row = []
            for field in fields:
                value = lead.get(field, '')
                if value is None:
                    value = ''
                # Escape commas and quotes
                value_str = str(value).replace('"', '""')
                if ',' in value_str or '"' in value_str:
                    value_str = f'"{value_str}"'
                row.append(value_str)
            f.write(','.join(row) + '\n')
    
    print(f"Exported {len(leads)} leads to {filename}")

def main():
    """Run the demo"""
    print("Building Lead Generation Agent - Demo Mode")
    print("=" * 60)
    print()
    
    # Create demo leads
    demo_leads = create_demo_leads()
    scorer = DemoScorer()
    
    scored_leads = []
    
    print(f"Processing {len(demo_leads)} sample building leads...")
    print()
    
    for lead_data in demo_leads:
        # Calculate scores
        overall_score, individual_scores = scorer.calculate_overall_score(lead_data)
        
        # Add scores to lead data
        lead_data.update(individual_scores)
        
        # Calculate savings estimates
        savings = scorer.estimate_savings(lead_data)
        lead_data.update(savings)
        
        scored_leads.append(lead_data)
    
    # Sort by overall score
    scored_leads.sort(key=lambda x: x['overall_lead_score'], reverse=True)
    
    # Display results
    print("DEMO RESULTS")
    print("-" * 60)
    
    for i, lead in enumerate(scored_leads, 1):
        print(f"\n{i}. {lead['address']}")
        print(f"   Building Type: {lead['building_type'].title()}")
        print(f"   Size: {lead['square_footage']:,} sq ft")
        print(f"   Year Built: {lead['year_built']}")
        print(f"   Overall Score: {lead['overall_lead_score']:.1f}/100")
        print(f"   Energy Potential: {lead['energy_savings_potential']:.1f}/100")
        print(f"   Accessibility: {lead['accessibility_score']:.1f}/100")
        print(f"   Project Size: {lead['project_size_score']:.1f}/100")
        print(f"   Urgency: {lead['urgency_score']:.1f}/100")
        
        if lead.get('estimated_annual_hvac_savings'):
            print(f"   Est. Annual HVAC Savings: ${lead['estimated_annual_hvac_savings']:,.0f}")
            print(f"   Est. Lifetime Savings: ${lead['estimated_lifetime_savings']:,.0f}")
            print(f"   Improvement Potential: {lead['improvement_potential_percent']:.1f}%")
        
        if lead.get('contact_phone'):
            print(f"   Contact: {lead['contact_phone']}")
        if lead.get('contact_email'):
            print(f"   Email: {lead['contact_email']}")
        
        if lead.get('notes'):
            print(f"   Notes: {lead['notes']}")
    
    # Export to CSV
    export_to_csv(scored_leads, 'demo_leads.csv')
    
    print(f"\n{'='*60}")
    print("DEMO SUMMARY")
    print(f"{'='*60}")
    print(f"Total Leads Processed: {len(scored_leads)}")
    print(f"Average Score: {sum(lead['overall_lead_score'] for lead in scored_leads) / len(scored_leads):.1f}")
    
    high_value_leads = [lead for lead in scored_leads if lead['overall_lead_score'] >= 70]
    print(f"High-Value Leads (70+ score): {len(high_value_leads)}")
    
    total_annual_savings = sum(lead.get('estimated_annual_hvac_savings', 0) for lead in scored_leads)
    total_lifetime_savings = sum(lead.get('estimated_lifetime_savings', 0) for lead in scored_leads)
    
    print(f"Total Est. Annual Savings: ${total_annual_savings:,.0f}")
    print(f"Total Est. Lifetime Savings: ${total_lifetime_savings:,.0f}")
    
    print(f"\nDemo data exported to: demo_leads.csv")
    print(f"Log file: building_agent.log")
    
    print(f"\n{'='*60}")
    print("NEXT STEPS")
    print(f"{'='*60}")
    print("1. Install required packages: pip install -r requirements.txt")
    print("2. Run with real data: python cli.py --locations 'YourCity,ST'")
    print("3. Customize scoring weights based on your priorities")
    print("4. Export results to your CRM system")
    print("\nFor help: python cli.py --help")

if __name__ == "__main__":
    main()