#!/usr/bin/env python3
"""
Specialized data source scrapers for building information collection

This module contains specialized scrapers for various data sources:
- Government property databases (assessor, planning, building permits)
- Commercial real estate platforms (LoopNet, Crexi, commercial MLS)
- Business directories (Google Places, Yellow Pages, industry directories)
- Energy databases (EPA, state energy programs)
"""

import requests
import json
import time
import logging
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote_plus
import re
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

class GovernmentDataScraper:
    """Scraper for government property databases"""
    
    def __init__(self, session: requests.Session):
        self.session = session
        
    def scrape_county_assessor(self, county: str, state: str, city: str = None) -> List[Dict]:
        """
        Generic county assessor scraper
        Many counties follow similar patterns for property search
        """
        leads = []
        
        # Common URL patterns for county assessor sites
        url_patterns = [
            f"https://{county.lower().replace(' ', '')}.gov/property-search",
            f"https://www.{county.lower().replace(' ', '')}county.gov/assessor",
            f"https://assessor.{county.lower().replace(' ', '')}.{state.lower()}.gov",
            f"https://{county.lower().replace(' ', '')}-{state.lower()}.publicaccessnow.com"
        ]
        
        for base_url in url_patterns:
            try:
                # Test if URL exists
                response = self.session.head(base_url, timeout=10)
                if response.status_code == 200:
                    logger.info(f"Found assessor site: {base_url}")
                    leads.extend(self._scrape_assessor_site(base_url, city))
                    break
            except:
                continue
                
        return leads
    
    def _scrape_assessor_site(self, base_url: str, city: str = None) -> List[Dict]:
        """Scrape a specific assessor website"""
        leads = []
        
        # Common search parameters
        search_params = {
            'property_class': 'commercial',
            'city': city,
            'page_size': 100
        }
        
        try:
            response = self.session.get(f"{base_url}/search", params=search_params)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for common table structures
            property_tables = soup.find_all('table', class_=['property-results', 'search-results', 'data-table'])
            
            for table in property_tables:
                rows = table.find_all('tr')[1:]  # Skip header
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 4:  # Minimum expected columns
                        lead_data = self._parse_assessor_row(cells)
                        if lead_data:
                            leads.append(lead_data)
                            
        except Exception as e:
            logger.error(f"Error scraping assessor site {base_url}: {e}")
            
        return leads
    
    def _parse_assessor_row(self, cells) -> Optional[Dict]:
        """Parse a row from assessor search results"""
        try:
            # Common column patterns
            address = self._extract_text(cells, ['address', 'location', 'property_address'])
            owner = self._extract_text(cells, ['owner', 'owner_name', 'taxpayer'])
            year_built = self._extract_year(cells, ['year_built', 'built', 'construction_year'])
            square_footage = self._extract_number(cells, ['sqft', 'square_feet', 'building_area'])
            
            if address:
                return {
                    'address': address,
                    'owner_name': owner,
                    'year_built': year_built,
                    'square_footage': square_footage,
                    'data_source': 'county_assessor'
                }
        except Exception as e:
            logger.error(f"Error parsing assessor row: {e}")
            
        return None
    
    def _extract_text(self, cells, patterns: List[str]) -> Optional[str]:
        """Extract text from cells based on common patterns"""
        for cell in cells:
            cell_text = cell.get_text(strip=True)
            cell_class = cell.get('class', [])
            
            for pattern in patterns:
                if (pattern in ' '.join(cell_class).lower() or 
                    pattern in cell_text.lower() or
                    cell.find(attrs={'class': re.compile(pattern, re.I)})):
                    return cell_text
        return None
    
    def _extract_year(self, cells, patterns: List[str]) -> Optional[int]:
        """Extract year from cells"""
        text = self._extract_text(cells, patterns)
        if text:
            year_match = re.search(r'\b(19|20)\d{2}\b', text)
            if year_match:
                return int(year_match.group())
        return None
    
    def _extract_number(self, cells, patterns: List[str]) -> Optional[int]:
        """Extract numeric values from cells"""
        text = self._extract_text(cells, patterns)
        if text:
            # Remove commas and extract numbers
            number_text = re.sub(r'[^\d]', '', text)
            if number_text:
                return int(number_text)
        return None
    
    def scrape_building_permits(self, county: str, state: str, city: str = None) -> List[Dict]:
        """
        Scrape building permit databases for commercial construction
        This can identify new buildings or major renovations
        """
        leads = []
        
        permit_urls = [
            f"https://{city.lower().replace(' ', '')}.gov/building-permits",
            f"https://permits.{county.lower().replace(' ', '')}.gov",
            f"https://www.{county.lower().replace(' ', '')}county.gov/permits"
        ]
        
        for url in permit_urls:
            try:
                # Search for commercial permits
                params = {
                    'permit_type': 'commercial',
                    'status': 'issued',
                    'date_from': '2020-01-01'  # Recent permits
                }
                
                response = self.session.get(url, params=params, timeout=15)
                if response.status_code == 200:
                    leads.extend(self._parse_permit_data(response.content))
                    break
                    
            except Exception as e:
                logger.debug(f"Could not access permit site {url}: {e}")
                
        return leads
    
    def _parse_permit_data(self, content) -> List[Dict]:
        """Parse building permit data"""
        leads = []
        soup = BeautifulSoup(content, 'html.parser')
        
        # Look for permit records
        permit_rows = soup.find_all('tr', class_=['permit-row', 'data-row'])
        
        for row in permit_rows:
            try:
                address = row.find('td', class_='address')
                permit_type = row.find('td', class_='permit-type')
                value = row.find('td', class_='construction-value')
                
                if address and permit_type:
                    # Filter for commercial/HVAC-related permits
                    permit_text = permit_type.get_text().lower()
                    if any(keyword in permit_text for keyword in ['hvac', 'commercial', 'mechanical', 'cooling']):
                        leads.append({
                            'address': address.get_text(strip=True),
                            'permit_type': permit_type.get_text(strip=True),
                            'construction_value': self._extract_value(value.get_text() if value else ''),
                            'data_source': 'building_permits'
                        })
                        
            except Exception as e:
                logger.error(f"Error parsing permit row: {e}")
                
        return leads
    
    def _extract_value(self, value_text: str) -> Optional[float]:
        """Extract monetary value from text"""
        if value_text:
            value_match = re.search(r'\$?([\d,]+\.?\d*)', value_text.replace(',', ''))
            if value_match:
                return float(value_match.group(1).replace(',', ''))
        return None

class CommercialRealEstateScraper:
    """Scraper for commercial real estate platforms"""
    
    def __init__(self, session: requests.Session):
        self.session = session
        
    def scrape_loopnet(self, city: str, state: str) -> List[Dict]:
        """
        Scrape LoopNet for commercial property listings
        LoopNet is the largest commercial real estate platform
        """
        leads = []
        
        # LoopNet search parameters
        base_url = "https://www.loopnet.com/search"
        search_params = {
            'sk': 'bb9a7e8c8f4a77d',  # Search key
            'bb': f"{city}, {state}",
            'pt': 'for-lease,for-sale',
            'pind': 'office,retail,industrial,warehouse'
        }
        
        try:
            response = self.session.get(base_url, params=search_params, timeout=30)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Parse property cards
            property_cards = soup.find_all('div', class_=['property-card', 'search-result-item'])
            
            for card in property_cards:
                lead_data = self._parse_loopnet_listing(card)
                if lead_data:
                    leads.append(lead_data)
                    
        except Exception as e:
            logger.error(f"Error scraping LoopNet: {e}")
            
        return leads
    
    def _parse_loopnet_listing(self, card) -> Optional[Dict]:
        """Parse a LoopNet property listing"""
        try:
            # Extract address
            address_elem = card.find(['div', 'span'], class_=re.compile('address|location'))
            address = address_elem.get_text(strip=True) if address_elem else None
            
            # Extract square footage
            sqft_elem = card.find(text=re.compile(r'\d+\s*(?:sq\.?\s*ft\.?|sf)', re.I))
            square_footage = None
            if sqft_elem:
                sqft_match = re.search(r'(\d{1,3}(?:,\d{3})*)', sqft_elem)
                if sqft_match:
                    square_footage = int(sqft_match.group(1).replace(',', ''))
            
            # Extract contact information
            contact_elem = card.find('div', class_=re.compile('contact|broker'))
            contact_info = {}
            
            if contact_elem:
                phone_link = contact_elem.find('a', href=re.compile(r'tel:'))
                email_link = contact_elem.find('a', href=re.compile(r'mailto:'))
                
                if phone_link:
                    contact_info['phone'] = phone_link['href'].replace('tel:', '')
                if email_link:
                    contact_info['email'] = email_link['href'].replace('mailto:', '')
            
            # Extract property type
            type_elem = card.find(text=re.compile(r'office|retail|warehouse|industrial', re.I))
            building_type = type_elem.strip().lower() if type_elem else 'commercial'
            
            if address:
                return {
                    'address': address,
                    'building_type': building_type,
                    'square_footage': square_footage,
                    'contact_phone': contact_info.get('phone'),
                    'contact_email': contact_info.get('email'),
                    'data_source': 'loopnet'
                }
                
        except Exception as e:
            logger.error(f"Error parsing LoopNet listing: {e}")
            
        return None
    
    def scrape_crexi(self, city: str, state: str) -> List[Dict]:
        """
        Scrape Crexi for commercial property listings
        Crexi is another major commercial real estate platform
        """
        leads = []
        
        try:
            # Crexi API-style search
            search_url = "https://crexi.com/properties"
            params = {
                'location': f"{city}, {state}",
                'property_types': 'office,retail,industrial,warehouse',
                'listing_types': 'sale,lease'
            }
            
            response = self.session.get(search_url, params=params)
            
            # Check if response contains JSON data
            if 'application/json' in response.headers.get('content-type', ''):
                data = response.json()
                if 'properties' in data:
                    for prop in data['properties']:
                        lead_data = self._parse_crexi_property(prop)
                        if lead_data:
                            leads.append(lead_data)
            else:
                # Parse HTML response
                soup = BeautifulSoup(response.content, 'html.parser')
                property_items = soup.find_all('div', class_=['property-item', 'listing-card'])
                
                for item in property_items:
                    lead_data = self._parse_crexi_html(item)
                    if lead_data:
                        leads.append(lead_data)
                        
        except Exception as e:
            logger.error(f"Error scraping Crexi: {e}")
            
        return leads
    
    def _parse_crexi_property(self, prop_data: Dict) -> Optional[Dict]:
        """Parse Crexi property data from JSON response"""
        try:
            return {
                'address': prop_data.get('address', {}).get('full_address'),
                'building_type': prop_data.get('property_type', 'commercial').lower(),
                'square_footage': prop_data.get('building_area_sqft'),
                'year_built': prop_data.get('year_built'),
                'contact_phone': prop_data.get('broker', {}).get('phone'),
                'contact_email': prop_data.get('broker', {}).get('email'),
                'data_source': 'crexi'
            }
        except Exception as e:
            logger.error(f"Error parsing Crexi property data: {e}")
            return None
    
    def _parse_crexi_html(self, item) -> Optional[Dict]:
        """Parse Crexi property from HTML"""
        try:
            address_elem = item.find(['div', 'span'], class_=re.compile('address'))
            address = address_elem.get_text(strip=True) if address_elem else None
            
            # Extract other details similar to LoopNet parsing
            sqft_text = item.find(text=re.compile(r'\d+\s*sf', re.I))
            square_footage = None
            if sqft_text:
                sqft_match = re.search(r'(\d{1,3}(?:,\d{3})*)', sqft_text)
                if sqft_match:
                    square_footage = int(sqft_match.group(1).replace(',', ''))
            
            if address:
                return {
                    'address': address,
                    'square_footage': square_footage,
                    'data_source': 'crexi'
                }
                
        except Exception as e:
            logger.error(f"Error parsing Crexi HTML: {e}")
            
        return None

class BusinessDirectoryScraper:
    """Scraper for business directories and industrial databases"""
    
    def __init__(self, session: requests.Session):
        self.session = session
        
    def scrape_google_places(self, city: str, state: str, api_key: str = None) -> List[Dict]:
        """
        Use Google Places API to find commercial/industrial businesses
        Requires API key but provides high-quality data
        """
        leads = []
        
        if not api_key:
            logger.warning("Google Places API key not provided")
            return leads
        
        # Industries with high HVAC energy consumption
        target_industries = [
            'manufacturing company',
            'warehouse',
            'distribution center',
            'office building',
            'shopping mall',
            'retail store',
            'data center',
            'hospital',
            'hotel'
        ]
        
        base_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        
        for industry in target_industries:
            try:
                params = {
                    'query': f"{industry} in {city}, {state}",
                    'key': api_key,
                    'type': 'establishment'
                }
                
                response = self.session.get(base_url, params=params)
                data = response.json()
                
                if data.get('status') == 'OK':
                    for place in data.get('results', []):
                        lead_data = self._parse_google_place(place, industry)
                        if lead_data:
                            leads.append(lead_data)
                
                time.sleep(0.1)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Error scraping Google Places for {industry}: {e}")
                
        return leads
    
    def _parse_google_place(self, place: Dict, industry: str) -> Optional[Dict]:
        """Parse Google Places result"""
        try:
            return {
                'name': place.get('name'),
                'address': place.get('formatted_address'),
                'building_type': industry.replace(' company', '').replace(' center', ''),
                'rating': place.get('rating'),
                'phone': place.get('formatted_phone_number'),
                'website': place.get('website'),
                'data_source': 'google_places'
            }
        except Exception as e:
            logger.error(f"Error parsing Google Place: {e}")
            return None
    
    def scrape_manufacturing_directories(self, state: str) -> List[Dict]:
        """
        Scrape manufacturing directories for industrial facilities
        Manufacturing facilities typically have high HVAC loads
        """
        leads = []
        
        # Manufacturing directory URLs
        directory_urls = [
            f"https://www.manufacturersdirectory.com/{state.lower()}",
            f"https://www.thomasnet.com/browse/manufacturing/{state.lower()}",
            f"https://www.industrynet.com/directory/{state.lower()}"
        ]
        
        for url in directory_urls:
            try:
                response = self.session.get(url, timeout=20)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for company listings
                company_links = soup.find_all('a', href=re.compile(r'/company/|/manufacturer/'))
                
                for link in company_links[:50]:  # Limit to avoid overwhelming
                    company_url = urljoin(url, link['href'])
                    lead_data = self._scrape_company_page(company_url)
                    if lead_data:
                        leads.append(lead_data)
                        
                time.sleep(2)  # Be respectful with rate limiting
                
            except Exception as e:
                logger.error(f"Error scraping manufacturing directory {url}: {e}")
                
        return leads
    
    def _scrape_company_page(self, company_url: str) -> Optional[Dict]:
        """Scrape individual company page for details"""
        try:
            response = self.session.get(company_url, timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract company information
            company_name = self._extract_company_name(soup)
            address = self._extract_address(soup)
            phone = self._extract_phone(soup)
            email = self._extract_email(soup)
            
            if company_name and address:
                return {
                    'name': company_name,
                    'address': address,
                    'building_type': 'manufacturing',
                    'contact_phone': phone,
                    'contact_email': email,
                    'data_source': 'manufacturing_directory'
                }
                
        except Exception as e:
            logger.debug(f"Error scraping company page {company_url}: {e}")
            
        return None
    
    def _extract_company_name(self, soup) -> Optional[str]:
        """Extract company name from page"""
        selectors = [
            'h1.company-name',
            'h1[class*="name"]',
            '.company-title',
            'h1',
            'title'
        ]
        
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                return elem.get_text(strip=True)
        return None
    
    def _extract_address(self, soup) -> Optional[str]:
        """Extract address from page"""
        # Look for address patterns
        address_selectors = [
            '.address',
            '[class*="address"]',
            '.contact-info',
            '[itemtype*="PostalAddress"]'
        ]
        
        for selector in address_selectors:
            elem = soup.select_one(selector)
            if elem:
                address_text = elem.get_text(strip=True)
                # Validate it looks like an address
                if re.search(r'\d+.*\w+.*\w+', address_text):
                    return address_text
        
        # Search for address patterns in text
        text = soup.get_text()
        address_pattern = r'\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Boulevard|Blvd|Lane|Ln|Way|Court|Ct|Place|Pl)[^,]*,\s*[A-Za-z\s]+,\s*[A-Z]{2}\s*\d{5}'
        address_match = re.search(address_pattern, text)
        if address_match:
            return address_match.group().strip()
            
        return None
    
    def _extract_phone(self, soup) -> Optional[str]:
        """Extract phone number from page"""
        # Look for phone links
        phone_link = soup.find('a', href=re.compile(r'tel:'))
        if phone_link:
            return phone_link['href'].replace('tel:', '').strip()
        
        # Search for phone patterns in text
        text = soup.get_text()
        phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        phone_match = re.search(phone_pattern, text)
        if phone_match:
            return phone_match.group()
            
        return None
    
    def _extract_email(self, soup) -> Optional[str]:
        """Extract email address from page"""
        # Look for email links
        email_link = soup.find('a', href=re.compile(r'mailto:'))
        if email_link:
            return email_link['href'].replace('mailto:', '').strip()
        
        # Search for email patterns in text
        text = soup.get_text()
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, text)
        if email_match:
            return email_match.group()
            
        return None

class EnergyDatabaseScraper:
    """Scraper for energy-related databases and programs"""
    
    def __init__(self, session: requests.Session):
        self.session = session
    
    def scrape_energy_star_buildings(self, state: str) -> List[Dict]:
        """
        Scrape EPA's ENERGY STAR certified buildings database
        These buildings may be targets for additional efficiency improvements
        """
        leads = []
        
        # EPA ENERGY STAR building search
        base_url = "https://www.energystar.gov/buildings/about-us/how-can-we-help-you/benchmark-energy-use/energy-star-score"
        
        try:
            # Search for certified buildings by state
            search_params = {
                'state': state,
                'building_type': 'commercial'
            }
            
            response = self.session.get(base_url, params=search_params)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Parse building listings
            building_rows = soup.find_all('tr', class_=['building-row', 'data-row'])
            
            for row in building_rows:
                lead_data = self._parse_energy_star_building(row)
                if lead_data:
                    leads.append(lead_data)
                    
        except Exception as e:
            logger.error(f"Error scraping ENERGY STAR buildings: {e}")
            
        return leads
    
    def _parse_energy_star_building(self, row) -> Optional[Dict]:
        """Parse ENERGY STAR building row"""
        try:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 4:
                building_name = cells[0].get_text(strip=True)
                address = cells[1].get_text(strip=True)
                building_type = cells[2].get_text(strip=True)
                energy_score = cells[3].get_text(strip=True)
                
                return {
                    'name': building_name,
                    'address': address,
                    'building_type': building_type.lower(),
                    'energy_efficiency_rating': f"ENERGY STAR {energy_score}",
                    'data_source': 'energy_star'
                }
        except Exception as e:
            logger.error(f"Error parsing ENERGY STAR building: {e}")
            
        return None