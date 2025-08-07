#!/usr/bin/env python3
"""
Command Line Interface for Building Lead Generation Agent

This script provides a user-friendly command-line interface for running
the building information scraper and lead generation system.

Usage examples:
    python cli.py --locations "Chicago,IL" "Houston,TX" --min-score 60
    python cli.py --config custom_config.json --export-format csv
    python cli.py --demo  # Run with sample data
"""

import argparse
import json
import sys
import logging
from pathlib import Path
from typing import List, Dict

from building_lead_agent import BuildingDataScraper, BuildingLead
from lead_scoring import EnergyEfficiencyScorer, LeadFilter, ScoringWeights
from data_sources import (
    GovernmentDataScraper, 
    CommercialRealEstateScraper, 
    BusinessDirectoryScraper,
    EnergyDatabaseScraper
)

def setup_logging(verbose: bool = False):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('lead_generation.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def parse_locations(location_strings: List[str]) -> List[Dict]:
    """Parse location strings into structured format"""
    locations = []
    
    for loc_str in location_strings:
        parts = loc_str.split(',')
        if len(parts) >= 2:
            city = parts[0].strip()
            state = parts[1].strip()
            county = parts[2].strip() if len(parts) > 2 else None
            
            location = {
                'city': city,
                'state': state
            }
            if county:
                location['county'] = county
                
            locations.append(location)
        else:
            print(f"Warning: Invalid location format '{loc_str}'. Use 'City,State' or 'City,State,County'")
    
    return locations

def run_demo_mode():
    """Run the agent with sample data for demonstration"""
    print("Running Building Lead Generation Agent in Demo Mode")
    print("=" * 60)
    
    # Sample locations
    demo_locations = [
        {"city": "Austin", "state": "TX", "county": "Travis County"},
        {"city": "Seattle", "state": "WA", "county": "King County"},
        {"city": "Atlanta", "state": "GA", "county": "Fulton County"}
    ]
    
    # Initialize scraper with demo config
    demo_config = {
        "target_locations": demo_locations,
        "building_types": ["office", "retail", "warehouse", "manufacturing"],
        "min_square_footage": 15000,
        "max_building_age": 40,
        "rate_limit_delay": 1.0
    }
    
    # Create demo data
    demo_leads = [
        {
            'property_id': 'DEMO_1',
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
            'contact_phone': '(512) 555-0123',
            'contact_email': 'leasing@austinoffice.com',
            'data_source': 'demo'
        },
        {
            'property_id': 'DEMO_2',
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
            'contact_phone': '(206) 555-0456',
            'data_source': 'demo'
        },
        {
            'property_id': 'DEMO_3',
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
            'contact_phone': '(404) 555-0789',
            'contact_email': 'management@southernretail.com',
            'data_source': 'demo'
        }
    ]
    
    # Score the demo leads
    scorer = EnergyEfficiencyScorer()
    
    scored_leads = []
    for lead_data in demo_leads:
        overall_score, individual_scores = scorer.calculate_overall_score(lead_data)
        
        # Add scores to lead data
        lead_data.update(individual_scores)
        
        # Calculate savings potential
        savings = scorer.estimate_hvac_savings_potential(lead_data)
        lead_data.update(savings)
        
        scored_leads.append(lead_data)
    
    # Display results
    print(f"\nDemo Results: {len(scored_leads)} leads generated and scored")
    print("-" * 60)
    
    for lead in sorted(scored_leads, key=lambda x: x['overall_lead_score'], reverse=True):
        print(f"\nBuilding: {lead['address']}")
        print(f"Type: {lead['building_type'].title()}")
        print(f"Size: {lead['square_footage']:,} sq ft")
        print(f"Year Built: {lead['year_built']}")
        print(f"Overall Score: {lead['overall_lead_score']:.1f}/100")
        print(f"Energy Potential: {lead['energy_savings_potential']:.1f}/100")
        print(f"Accessibility: {lead['accessibility_score']:.1f}/100")
        
        if lead.get('estimated_annual_hvac_savings'):
            print(f"Est. Annual HVAC Savings: ${lead['estimated_annual_hvac_savings']:,.0f}")
            print(f"Est. Lifetime Savings: ${lead['estimated_lifetime_savings']:,.0f}")
        
        if lead.get('contact_phone'):
            print(f"Contact: {lead['contact_phone']}")
        if lead.get('contact_email'):
            print(f"Email: {lead['contact_email']}")
    
    print(f"\n{'='*60}")
    print("Demo completed successfully!")
    print("Run with real data using: python cli.py --locations 'YourCity,ST'")

def main():
    parser = argparse.ArgumentParser(
        description='Building Lead Generation Agent for Energy Efficiency Solutions',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --demo
  %(prog)s --locations "Chicago,IL" "Houston,TX" --min-score 70
  %(prog)s --config config.json --export leads.csv --format csv
  %(prog)s --locations "Phoenix,AZ,Maricopa County" --building-types office manufacturing
        """
    )
    
    # Mode selection
    parser.add_argument('--demo', action='store_true',
                       help='Run in demo mode with sample data')
    
    # Location targeting
    parser.add_argument('--locations', nargs='+', metavar='CITY,STATE[,COUNTY]',
                       help='Target locations in format "City,State" or "City,State,County"')
    
    # Configuration
    parser.add_argument('--config', type=str, default='config.json',
                       help='Path to configuration file (default: config.json)')
    
    # Filtering options
    parser.add_argument('--building-types', nargs='+', 
                       choices=['office', 'retail', 'warehouse', 'manufacturing', 
                               'healthcare', 'hospitality', 'education', 'mixed_use'],
                       help='Building types to target')
    
    parser.add_argument('--min-sqft', type=int, default=10000,
                       help='Minimum building square footage (default: 10000)')
    
    parser.add_argument('--max-age', type=int, default=50,
                       help='Maximum building age in years (default: 50)')
    
    parser.add_argument('--min-score', type=float, default=50.0,
                       help='Minimum lead score for export (default: 50.0)')
    
    # Export options
    parser.add_argument('--export', type=str, metavar='FILENAME',
                       help='Export results to file')
    
    parser.add_argument('--format', choices=['csv', 'json', 'excel'], default='csv',
                       help='Export format (default: csv)')
    
    parser.add_argument('--limit', type=int, default=1000,
                       help='Maximum number of leads to export (default: 1000)')
    
    # API keys
    parser.add_argument('--google-api-key', type=str,
                       help='Google Places API key for enhanced data collection')
    
    # Logging
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Suppress output except errors')
    
    # Scoring weights
    parser.add_argument('--energy-weight', type=float, default=0.40,
                       help='Weight for energy savings potential (default: 0.40)')
    
    parser.add_argument('--accessibility-weight', type=float, default=0.25,
                       help='Weight for accessibility score (default: 0.25)')
    
    parser.add_argument('--size-weight', type=float, default=0.20,
                       help='Weight for project size (default: 0.20)')
    
    parser.add_argument('--urgency-weight', type=float, default=0.10,
                       help='Weight for urgency factors (default: 0.10)')
    
    parser.add_argument('--market-weight', type=float, default=0.05,
                       help='Weight for market factors (default: 0.05)')
    
    args = parser.parse_args()
    
    # Setup logging
    if not args.quiet:
        setup_logging(args.verbose)
    
    logger = logging.getLogger(__name__)
    
    # Run demo mode
    if args.demo:
        run_demo_mode()
        return
    
    # Validate required arguments for normal mode
    if not args.locations:
        parser.error("--locations is required when not using --demo mode")
    
    # Parse locations
    locations = parse_locations(args.locations)
    if not locations:
        print("Error: No valid locations provided")
        sys.exit(1)
    
    logger.info(f"Starting lead generation for {len(locations)} locations")
    
    # Load configuration
    try:
        config_path = Path(args.config)
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"Loaded configuration from {args.config}")
        else:
            config = {}
            logger.info("Using default configuration")
    except Exception as e:
        logger.error(f"Error loading config file: {e}")
        config = {}
    
    # Update config with command line arguments
    if args.building_types:
        config['building_types'] = args.building_types
    if args.min_sqft:
        config['min_square_footage'] = args.min_sqft
    if args.max_age:
        config['max_building_age'] = args.max_age
    
    # Save updated config
    config['target_locations'] = locations
    with open(args.config, 'w') as f:
        json.dump(config, f, indent=2)
    
    # Create scoring weights
    weights = ScoringWeights(
        energy_potential=args.energy_weight,
        accessibility=args.accessibility_weight,
        project_size=args.size_weight,
        urgency=args.urgency_weight,
        market_factors=args.market_weight
    )
    
    # Initialize components
    try:
        scraper = BuildingDataScraper(args.config)
        scorer = EnergyEfficiencyScorer(weights)
        lead_filter = LeadFilter()
        
        logger.info("Initialized scraper and scoring components")
        
        # Run the scraping process
        total_leads = scraper.run_full_scrape(locations)
        
        if total_leads == 0:
            logger.warning("No leads were collected. This might be due to:")
            logger.warning("- Rate limiting from target websites")
            logger.warning("- No commercial properties found in specified locations")
            logger.warning("- Network connectivity issues")
            logger.warning("Try running with --demo flag to test the system")
            return
        
        # Get leads from database
        leads = scraper.get_top_leads(limit=args.limit, min_score=args.min_score)
        
        logger.info(f"Retrieved {len(leads)} leads meeting minimum score criteria")
        
        # Export results
        if args.export:
            try:
                scraper.export_leads(args.export, format=args.format, min_score=args.min_score)
                logger.info(f"Exported leads to {args.export}")
            except Exception as e:
                logger.error(f"Error exporting leads: {e}")
        
        # Display summary
        if not args.quiet and leads:
            print(f"\nLead Generation Summary")
            print("=" * 40)
            print(f"Total leads collected: {total_leads}")
            print(f"Leads meeting criteria: {len(leads)}")
            
            # Top 5 leads summary
            top_leads = leads[:5]
            print(f"\nTop {len(top_leads)} Leads:")
            print("-" * 40)
            
            for i, lead in enumerate(top_leads, 1):
                print(f"{i}. {lead.get('address', 'N/A')}")
                print(f"   Score: {lead.get('overall_lead_score', 0):.1f}/100")
                print(f"   Type: {lead.get('building_type', 'N/A').title()}")
                print(f"   Size: {lead.get('square_footage', 0):,} sq ft")
                if lead.get('contact_phone'):
                    print(f"   Phone: {lead['contact_phone']}")
                print()
        
        logger.info("Lead generation completed successfully")
        
    except KeyboardInterrupt:
        logger.info("Lead generation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during lead generation: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()