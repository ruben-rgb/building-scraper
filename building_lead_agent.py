#!/usr/bin/env python3
"""
Commercial/Industrial Building Lead Generation Agent

This agent scrapes building information from multiple sources to identify 
potential customers for energy efficiency solutions, particularly HVAC systems.

Key features:
- Multi-source data collection (government databases, real estate sites, business directories)
- Building filtering based on size, age, HVAC characteristics 
- Lead scoring based on energy efficiency potential
- Geographic targeting
- Export capabilities for CRM integration
"""

import asyncio
import json
import logging
import os
import sqlite3
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from urllib.parse import urljoin, quote_plus
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('building_agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

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
    building_type: str  # office, retail, warehouse, manufacturing, etc.
    square_footage: Optional[int]
    year_built: Optional[int]
    stories: Optional[int]
    
    # Ownership/Contact info
    owner_name: Optional[str]
    owner_type: Optional[str]  # individual, corporation, llc, etc.
    management_company: Optional[str]
    contact_phone: Optional[str]
    contact_email: Optional[str]
    
    # HVAC/Energy characteristics
    hvac_type: Optional[str]
    heating_fuel: Optional[str]  # gas, electric, oil
    cooling_type: Optional[str]
    estimated_energy_cost: Optional[float]
    energy_efficiency_rating: Optional[str]
    
    # Lead scoring factors
    energy_savings_potential: float = 0.0
    accessibility_score: float = 0.0  # how easy to reach decision maker
    project_size_score: float = 0.0
    urgency_score: float = 0.0  # age of equipment, recent changes
    overall_lead_score: float = 0.0
    
    # Metadata
    data_source: str
    last_updated: str
    notes: Optional[str] = None

class BuildingDataScraper:
    """Main class for scraping building data from various sources"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config = self.load_config(config_file)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.db_path = self.config.get('database_path', 'building_leads.db')
        self.init_database()
        
    def load_config(self, config_file: str) -> Dict:
        """Load configuration from JSON file"""
        default_config = {
            "target_locations": [],
            "building_types": ["office", "retail", "warehouse", "manufacturing", "mixed_use"],
            "min_square_footage": 10000,
            "max_building_age": 50,
            "rate_limit_delay": 2.0,
            "database_path": "building_leads.db",
            "export_formats": ["csv", "json", "excel"]
        }
        
        try:
            with open(config_file, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        except FileNotFoundError:
            logger.warning(f"Config file {config_file} not found, using defaults")
            # Create default config file
            with open(config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
                
        return default_config
    
    def init_database(self):
        """Initialize SQLite database for storing leads"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS building_leads (
                property_id TEXT PRIMARY KEY,
                address TEXT,
                city TEXT,
                state TEXT,
                zip_code TEXT,
                county TEXT,
                building_type TEXT,
                square_footage INTEGER,
                year_built INTEGER,
                stories INTEGER,
                owner_name TEXT,
                owner_type TEXT,
                management_company TEXT,
                contact_phone TEXT,
                contact_email TEXT,
                hvac_type TEXT,
                heating_fuel TEXT,
                cooling_type TEXT,
                estimated_energy_cost REAL,
                energy_efficiency_rating TEXT,
                energy_savings_potential REAL,
                accessibility_score REAL,
                project_size_score REAL,
                urgency_score REAL,
                overall_lead_score REAL,
                data_source TEXT,
                last_updated TEXT,
                notes TEXT
            )
        ''')
        
        # Create indexes for common queries
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_city_state ON building_leads(city, state)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_building_type ON building_leads(building_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_lead_score ON building_leads(overall_lead_score)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_square_footage ON building_leads(square_footage)')
        
        conn.commit()
        conn.close()
        
    def save_lead(self, lead: BuildingLead):
        """Save a building lead to the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Convert dataclass to dict and handle None values
        lead_dict = asdict(lead)
        
        cursor.execute('''
            INSERT OR REPLACE INTO building_leads 
            (property_id, address, city, state, zip_code, county, building_type, 
             square_footage, year_built, stories, owner_name, owner_type, 
             management_company, contact_phone, contact_email, hvac_type, 
             heating_fuel, cooling_type, estimated_energy_cost, energy_efficiency_rating,
             energy_savings_potential, accessibility_score, project_size_score, 
             urgency_score, overall_lead_score, data_source, last_updated, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', tuple(lead_dict.values()))
        
        conn.commit()
        conn.close()
        
    def scrape_government_assessor_data(self, location: Dict) -> List[BuildingLead]:
        """
        Scrape commercial property data from county assessor websites
        This is often the most reliable source for property characteristics
        """
        leads = []
        city = location.get('city', '')
        state = location.get('state', '')
        county = location.get('county', '')
        
        logger.info(f"Scraping assessor data for {city}, {state}")
        
        # Example implementation for a generic assessor search
        # This would need to be customized for each county's specific website
        try:
            # Many counties have searchable property databases
            search_url = f"https://{county.lower().replace(' ', '')}.gov/property-search"
            
            # Search parameters for commercial properties
            params = {
                'property_type': 'commercial',
                'city': city,
                'min_sqft': self.config['min_square_footage']
            }
            
            response = self.session.get(search_url, params=params, timeout=30)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Parse property listings (this would be site-specific)
                property_rows = soup.find_all('tr', class_='property-row')
                
                for row in property_rows:
                    try:
                        lead = self.parse_assessor_row(row, city, state, county)
                        if lead and self.passes_filters(lead):
                            leads.append(lead)
                    except Exception as e:
                        logger.error(f"Error parsing assessor row: {e}")
                        continue
                        
            time.sleep(self.config['rate_limit_delay'])
            
        except Exception as e:
            logger.error(f"Error scraping assessor data for {location}: {e}")
            
        return leads
    
    def parse_assessor_row(self, row, city: str, state: str, county: str) -> Optional[BuildingLead]:
        """Parse a row from county assessor property search results"""
        try:
            # This is a template - actual implementation would depend on county website structure
            address = row.find('td', class_='address').text.strip()
            building_type = row.find('td', class_='property-type').text.strip().lower()
            
            # Extract square footage
            sqft_text = row.find('td', class_='square-feet').text.strip()
            square_footage = int(''.join(filter(str.isdigit, sqft_text))) if sqft_text else None
            
            # Extract year built
            year_text = row.find('td', class_='year-built').text.strip()
            year_built = int(year_text) if year_text.isdigit() else None
            
            # Extract owner information
            owner_name = row.find('td', class_='owner').text.strip() if row.find('td', class_='owner') else None
            
            # Create property ID
            property_id = f"{state}_{county}_{address}".replace(' ', '_').replace(',', '')
            
            lead = BuildingLead(
                property_id=property_id,
                address=address,
                city=city,
                state=state,
                zip_code='',  # Would extract from detailed page
                county=county,
                building_type=building_type,
                square_footage=square_footage,
                year_built=year_built,
                stories=None,
                owner_name=owner_name,
                owner_type=None,
                management_company=None,
                contact_phone=None,
                contact_email=None,
                hvac_type=None,
                heating_fuel=None,
                cooling_type=None,
                estimated_energy_cost=None,
                energy_efficiency_rating=None,
                data_source='county_assessor',
                last_updated=datetime.now().isoformat()
            )
            
            return lead
            
        except Exception as e:
            logger.error(f"Error parsing assessor row: {e}")
            return None
    
    def scrape_commercial_real_estate_sites(self, location: Dict) -> List[BuildingLead]:
        """
        Scrape commercial real estate listing sites like LoopNet, Crexi, etc.
        These often have more detailed building information and contact details
        """
        leads = []
        city = location.get('city', '')
        state = location.get('state', '')
        
        logger.info(f"Scraping commercial real estate sites for {city}, {state}")
        
        # Example: LoopNet-style search
        try:
            # Construct search URL for commercial properties
            search_params = {
                'sk': 'e85f89d62',  # Example search key
                'bb': f"{city}, {state}",
                'pt': 'all',  # property types
                'pind': 'warehouse,office,retail,industrial'
            }
            
            # This would be implemented for actual commercial real estate APIs/sites
            # For now, using placeholder structure
            
            base_url = "https://www.loopnet.com/search"
            response = self.session.get(base_url, params=search_params, timeout=30)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Parse property listings
                listings = soup.find_all('div', class_='property-card')
                
                for listing in listings:
                    try:
                        lead = self.parse_commercial_listing(listing, city, state)
                        if lead and self.passes_filters(lead):
                            leads.append(lead)
                    except Exception as e:
                        logger.error(f"Error parsing commercial listing: {e}")
                        continue
                        
            time.sleep(self.config['rate_limit_delay'])
            
        except Exception as e:
            logger.error(f"Error scraping commercial real estate sites: {e}")
            
        return leads
    
    def parse_commercial_listing(self, listing, city: str, state: str) -> Optional[BuildingLead]:
        """Parse a commercial real estate listing"""
        try:
            # Extract address
            address_elem = listing.find('div', class_='property-address')
            address = address_elem.text.strip() if address_elem else ''
            
            # Extract building details
            details = listing.find('div', class_='property-details')
            building_type = 'commercial'  # Default
            square_footage = None
            year_built = None
            
            if details:
                # Parse square footage
                sqft_match = details.text
                import re
                sqft_pattern = r'(\d{1,3}(?:,\d{3})*)\s*(?:sq\.?\s*ft\.?|sf)'
                sqft_search = re.search(sqft_pattern, sqft_match, re.IGNORECASE)
                if sqft_search:
                    square_footage = int(sqft_search.group(1).replace(',', ''))
                
                # Parse year built
                year_pattern = r'(?:built|year)\s*:?\s*(\d{4})'
                year_search = re.search(year_pattern, sqft_match, re.IGNORECASE)
                if year_search:
                    year_built = int(year_search.group(1))
            
            # Extract contact information
            contact_elem = listing.find('div', class_='broker-info')
            contact_phone = None
            contact_email = None
            
            if contact_elem:
                phone_elem = contact_elem.find('a', href=lambda x: x and 'tel:' in x)
                if phone_elem:
                    contact_phone = phone_elem.get('href').replace('tel:', '')
                
                email_elem = contact_elem.find('a', href=lambda x: x and 'mailto:' in x)
                if email_elem:
                    contact_email = email_elem.get('href').replace('mailto:', '')
            
            property_id = f"CRE_{state}_{city}_{address}".replace(' ', '_').replace(',', '')
            
            lead = BuildingLead(
                property_id=property_id,
                address=address,
                city=city,
                state=state,
                zip_code='',
                county='',
                building_type=building_type,
                square_footage=square_footage,
                year_built=year_built,
                stories=None,
                owner_name=None,
                owner_type=None,
                management_company=None,
                contact_phone=contact_phone,
                contact_email=contact_email,
                hvac_type=None,
                heating_fuel=None,
                cooling_type=None,
                estimated_energy_cost=None,
                energy_efficiency_rating=None,
                data_source='commercial_real_estate',
                last_updated=datetime.now().isoformat()
            )
            
            return lead
            
        except Exception as e:
            logger.error(f"Error parsing commercial listing: {e}")
            return None
    
    def scrape_business_directories(self, location: Dict) -> List[BuildingLead]:
        """
        Scrape business directories to find commercial/industrial facilities
        These provide business contact information and sometimes facility details
        """
        leads = []
        city = location.get('city', '')
        state = location.get('state', '')
        
        logger.info(f"Scraping business directories for {city}, {state}")
        
        # Target industries that typically have large HVAC loads
        target_industries = [
            'manufacturing', 'warehouse', 'distribution', 'data center',
            'retail', 'office', 'healthcare', 'hospitality', 'education'
        ]
        
        for industry in target_industries:
            try:
                # Example search (would implement specific directory APIs)
                search_params = {
                    'what': industry,
                    'where': f"{city}, {state}",
                    'size': 'large'  # Target larger businesses
                }
                
                # This is a placeholder for actual directory API calls
                # Could use Yellow Pages API, Google Places API, etc.
                
                time.sleep(self.config['rate_limit_delay'])
                
            except Exception as e:
                logger.error(f"Error scraping business directory for {industry}: {e}")
                
        return leads
    
    def passes_filters(self, lead: BuildingLead) -> bool:
        """Check if a building lead meets our targeting criteria"""
        
        # Size filter
        if lead.square_footage and lead.square_footage < self.config['min_square_footage']:
            return False
            
        # Age filter
        if lead.year_built:
            building_age = datetime.now().year - lead.year_built
            if building_age > self.config['max_building_age']:
                return False
        
        # Building type filter
        if lead.building_type and lead.building_type.lower() not in self.config['building_types']:
            return False
            
        return True
    
    def calculate_lead_scores(self, lead: BuildingLead) -> BuildingLead:
        """Calculate various scores for lead prioritization"""
        
        # Energy savings potential (0-100)
        energy_score = 0.0
        
        # Size-based scoring
        if lead.square_footage:
            if lead.square_footage > 100000:
                energy_score += 30
            elif lead.square_footage > 50000:
                energy_score += 20
            elif lead.square_footage > 25000:
                energy_score += 15
            else:
                energy_score += 10
        
        # Age-based scoring (older buildings = more opportunity)
        if lead.year_built:
            building_age = datetime.now().year - lead.year_built
            if building_age > 30:
                energy_score += 25
            elif building_age > 20:
                energy_score += 20
            elif building_age > 10:
                energy_score += 15
            else:
                energy_score += 5
        
        # Building type scoring
        energy_intensive_types = {
            'manufacturing': 25,
            'warehouse': 20,
            'data_center': 30,
            'retail': 15,
            'office': 15,
            'healthcare': 20,
            'hospitality': 20
        }
        
        if lead.building_type:
            energy_score += energy_intensive_types.get(lead.building_type.lower(), 10)
        
        lead.energy_savings_potential = min(energy_score, 100.0)
        
        # Accessibility score (how easy to reach decision maker)
        accessibility_score = 30.0  # Base score
        
        if lead.contact_phone:
            accessibility_score += 25
        if lead.contact_email:
            accessibility_score += 25
        if lead.owner_name:
            accessibility_score += 20
        
        lead.accessibility_score = min(accessibility_score, 100.0)
        
        # Project size score
        project_score = 0.0
        if lead.square_footage:
            if lead.square_footage > 200000:
                project_score = 100
            elif lead.square_footage > 100000:
                project_score = 80
            elif lead.square_footage > 50000:
                project_score = 60
            elif lead.square_footage > 25000:
                project_score = 40
            else:
                project_score = 20
        
        lead.project_size_score = project_score
        
        # Urgency score (based on equipment age estimates)
        urgency_score = 20.0  # Base urgency
        
        if lead.year_built:
            building_age = datetime.now().year - lead.year_built
            # Assume HVAC equipment replaced every 15-20 years
            hvac_age_estimate = building_age % 20
            if hvac_age_estimate > 15:
                urgency_score += 30
            elif hvac_age_estimate > 10:
                urgency_score += 20
            elif hvac_age_estimate > 5:
                urgency_score += 10
        
        lead.urgency_score = urgency_score
        
        # Overall lead score (weighted average)
        weights = {
            'energy_savings_potential': 0.4,
            'accessibility_score': 0.25,
            'project_size_score': 0.25,
            'urgency_score': 0.1
        }
        
        overall_score = (
            lead.energy_savings_potential * weights['energy_savings_potential'] +
            lead.accessibility_score * weights['accessibility_score'] +
            lead.project_size_score * weights['project_size_score'] +
            lead.urgency_score * weights['urgency_score']
        )
        
        lead.overall_lead_score = round(overall_score, 2)
        
        return lead
    
    def run_full_scrape(self, locations: List[Dict]) -> int:
        """Run complete scraping process for all specified locations"""
        total_leads = 0
        
        for location in locations:
            logger.info(f"Processing location: {location}")
            
            # Scrape from all data sources
            assessor_leads = self.scrape_government_assessor_data(location)
            cre_leads = self.scrape_commercial_real_estate_sites(location)
            directory_leads = self.scrape_business_directories(location)
            
            # Combine and process leads
            all_leads = assessor_leads + cre_leads + directory_leads
            
            for lead in all_leads:
                # Calculate scores
                lead = self.calculate_lead_scores(lead)
                
                # Save to database
                self.save_lead(lead)
                total_leads += 1
                
                logger.info(f"Saved lead: {lead.address}, Score: {lead.overall_lead_score}")
        
        logger.info(f"Scraping complete. Total leads processed: {total_leads}")
        return total_leads
    
    def get_top_leads(self, limit: int = 100, min_score: float = 50.0) -> List[Dict]:
        """Retrieve top-scoring leads from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM building_leads 
            WHERE overall_lead_score >= ? 
            ORDER BY overall_lead_score DESC 
            LIMIT ?
        ''', (min_score, limit))
        
        columns = [description[0] for description in cursor.description]
        leads = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return leads
    
    def export_leads(self, filename: str, format: str = 'csv', min_score: float = 50.0):
        """Export leads to various formats"""
        leads = self.get_top_leads(limit=10000, min_score=min_score)
        
        if not leads:
            logger.warning("No leads found to export")
            return
        
        df = pd.DataFrame(leads)
        
        if format.lower() == 'csv':
            df.to_csv(filename, index=False)
        elif format.lower() == 'excel':
            df.to_excel(filename, index=False)
        elif format.lower() == 'json':
            df.to_json(filename, orient='records', indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")
        
        logger.info(f"Exported {len(leads)} leads to {filename}")

def main():
    """Main execution function"""
    logger.info("Starting Building Lead Generation Agent")
    
    # Initialize scraper
    scraper = BuildingDataScraper()
    
    # Example target locations
    locations = [
        {"city": "Chicago", "state": "IL", "county": "Cook County"},
        {"city": "Houston", "state": "TX", "county": "Harris County"},
        {"city": "Phoenix", "state": "AZ", "county": "Maricopa County"},
        {"city": "Atlanta", "state": "GA", "county": "Fulton County"},
        {"city": "Denver", "state": "CO", "county": "Denver County"}
    ]
    
    # Run scraping process
    total_leads = scraper.run_full_scrape(locations)
    
    # Export top leads
    scraper.export_leads('top_building_leads.csv', format='csv', min_score=60.0)
    scraper.export_leads('building_leads_detailed.json', format='json', min_score=50.0)
    
    logger.info(f"Lead generation complete. Total leads: {total_leads}")

if __name__ == "__main__":
    main()