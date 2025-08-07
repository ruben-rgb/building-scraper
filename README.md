# Building Lead Generation Agent for Energy Efficiency Solutions

A comprehensive Python-based agent that scrapes building information from multiple data sources to identify potential commercial and industrial real estate leads for energy efficiency solutions, particularly HVAC systems.

## 🎯 Overview

This agent helps energy efficiency companies identify the most promising commercial and industrial buildings for HVAC upgrades and energy efficiency improvements. It combines data from multiple sources, applies sophisticated scoring algorithms, and generates prioritized lead lists with contact information and savings estimates.

## 🏢 Target Applications

- **Commercial Buildings**: Offices, retail spaces, mixed-use developments
- **Industrial Facilities**: Manufacturing plants, warehouses, distribution centers
- **Institutional Buildings**: Healthcare facilities, educational institutions
- **High-Energy Users**: Data centers, hospitality venues

## ✨ Key Features

### 🔍 Multi-Source Data Collection
- **Government Databases**: County assessor records, building permits
- **Commercial Real Estate**: LoopNet, Crexi, and other CRE platforms
- **Business Directories**: Google Places API, manufacturing directories
- **Energy Databases**: EPA ENERGY STAR certified buildings

### 📊 Intelligent Lead Scoring
- **Energy Savings Potential**: Based on building size, age, type, and usage patterns
- **Accessibility Score**: Contact information availability and decision-maker accessibility
- **Project Size Score**: Revenue potential based on building characteristics
- **Urgency Score**: Equipment age estimates and timing factors
- **Market Factors**: Local utility programs, climate, and regulations

### 🎯 Advanced Filtering
- Building size and age criteria
- Geographic targeting (city, state, county)
- Building type focus
- Contact information requirements
- Custom scoring thresholds

### 💾 Data Management
- SQLite database for lead storage
- Export to CSV, JSON, and Excel formats
- Deduplication and data quality checks
- Configurable retention and updates

## 🚀 Quick Start

### Prerequisites
- Python 3.7 or higher
- Internet connection for data scraping
- Optional: Google Places API key for enhanced data

### Installation

1. **Clone or download the project files**
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run demo mode** to test the system:
   ```bash
   python cli.py --demo
   ```

### Basic Usage

1. **Target specific locations**:
   ```bash
   python cli.py --locations "Chicago,IL" "Houston,TX" --min-score 60
   ```

2. **Filter by building types**:
   ```bash
   python cli.py --locations "Phoenix,AZ" --building-types manufacturing warehouse --min-sqft 50000
   ```

3. **Export results**:
   ```bash
   python cli.py --locations "Seattle,WA" --export leads.csv --format csv --min-score 70
   ```

## 📋 Command Line Options

### Location Targeting
```bash
--locations "City,State" "City,State,County"  # Target locations
```

### Filtering Options
```bash
--building-types office retail warehouse manufacturing healthcare
--min-sqft 10000              # Minimum building size
--max-age 50                  # Maximum building age
--min-score 50.0              # Minimum lead score
```

### Export Options
```bash
--export filename.csv         # Export file
--format csv|json|excel       # Export format
--limit 1000                  # Maximum leads to export
```

### Scoring Weights (Advanced)
```bash
--energy-weight 0.40          # Energy savings importance
--accessibility-weight 0.25   # Contact accessibility importance
--size-weight 0.20           # Project size importance
--urgency-weight 0.10        # Timing factors importance
--market-weight 0.05         # Market conditions importance
```

## 📁 File Structure

```
building-lead-agent/
├── building_lead_agent.py    # Main agent class and data structures
├── data_sources.py          # Specialized scrapers for different sources
├── lead_scoring.py          # Lead scoring algorithms and filters
├── cli.py                   # Command-line interface
├── requirements.txt         # Python dependencies
├── README.md               # This file
├── config.json             # Configuration file (auto-generated)
├── building_leads.db       # SQLite database (auto-generated)
└── building_agent.log      # Log file (auto-generated)
```

## 🧮 Scoring Algorithm

The agent uses a weighted scoring system to prioritize leads:

### Energy Savings Potential (40% weight)
- Building energy intensity by type
- HVAC energy consumption percentage
- Equipment age and efficiency improvement potential
- Annual energy cost estimates

### Accessibility Score (25% weight)
- Contact information availability (phone, email)
- Owner information quality
- Data source reliability
- Decision-maker accessibility

### Project Size Score (20% weight)
- Building square footage
- Construction complexity
- Revenue potential estimates

### Urgency Score (10% weight)
- HVAC equipment replacement timing
- Recent building activity
- Critical facility types

### Market Factors (5% weight)
- Local utility rebate programs
- Climate considerations
- Municipal efficiency requirements

## 💡 Energy Efficiency Opportunities

The agent identifies buildings with high potential for:

### HVAC System Upgrades
- **Heat Pumps**: High-efficiency air-source and ground-source systems
- **VRF Systems**: Variable refrigerant flow for precise climate control
- **Smart Controls**: Building automation and demand response systems
- **Heat Recovery**: Energy recovery ventilation systems

### Target Building Characteristics
- **Age**: 15+ years (older HVAC equipment)
- **Size**: 10,000+ sq ft (substantial energy usage)
- **Type**: Manufacturing, office, retail, healthcare (high HVAC loads)
- **Location**: Extreme climates (high heating/cooling demands)

### Estimated Savings Potential
The agent calculates:
- Annual HVAC energy costs
- Efficiency improvement percentages
- Annual savings estimates
- Lifetime savings projections (15-year equipment life)

## 🔧 Configuration

### config.json Example
```json
{
  "target_locations": [
    {"city": "Chicago", "state": "IL", "county": "Cook County"}
  ],
  "building_types": ["office", "retail", "warehouse", "manufacturing"],
  "min_square_footage": 10000,
  "max_building_age": 50,
  "rate_limit_delay": 2.0,
  "database_path": "building_leads.db",
  "export_formats": ["csv", "json", "excel"]
}
```

### Environment Variables (Optional)
```bash
export GOOGLE_PLACES_API_KEY="your_api_key_here"
```

## 📊 Sample Output

### Demo Mode Results
```
Building: 456 Industrial Way, Seattle, WA 98101
Type: Manufacturing
Size: 150,000 sq ft
Year Built: 1985
Overall Score: 78.2/100
Energy Potential: 85.5/100
Accessibility: 70.0/100
Est. Annual HVAC Savings: $45,000
Est. Lifetime Savings: $675,000
Contact: (206) 555-0456
```

### CSV Export Columns
- property_id, address, city, state, building_type
- square_footage, year_built, owner_name
- contact_phone, contact_email
- energy_savings_potential, accessibility_score, overall_lead_score
- estimated_annual_hvac_savings, estimated_lifetime_savings
- data_source, last_updated

## 🚨 Important Considerations

### Legal and Ethical Usage
- **Respect robots.txt** and website terms of service
- **Rate limiting** is implemented to avoid overwhelming servers
- **Public data only** - no private or restricted information
- **Commercial use compliance** with data source terms

### Data Quality
- Information accuracy depends on source data quality
- Contact information may be outdated
- Building characteristics are estimates
- Savings calculations are projections

### Rate Limiting
- Built-in delays between requests
- Respectful scraping practices
- May take time for large location lists
- Some sites may block automated access

## 🔧 Advanced Usage

### Custom Scoring Weights
Adjust scoring weights based on your business priorities:
```bash
# Prioritize energy savings potential
python cli.py --locations "Denver,CO" --energy-weight 0.6 --accessibility-weight 0.15 --size-weight 0.15 --urgency-weight 0.05 --market-weight 0.05

# Prioritize easy-to-reach contacts
python cli.py --locations "Austin,TX" --energy-weight 0.3 --accessibility-weight 0.4 --size-weight 0.2 --urgency-weight 0.05 --market-weight 0.05
```

### Batch Processing
Process multiple markets:
```bash
# Create a script for multiple runs
python cli.py --locations "Chicago,IL" --export chicago_leads.csv --min-score 65
python cli.py --locations "Houston,TX" --export houston_leads.csv --min-score 65
python cli.py --locations "Phoenix,AZ" --export phoenix_leads.csv --min-score 65
```

### Integration with CRM
The exported CSV files can be directly imported into most CRM systems:
- **Salesforce**: Use Data Import Wizard
- **HubSpot**: Import contacts and companies
- **Pipedrive**: Import deals and organizations

## 🐛 Troubleshooting

### Common Issues

1. **No leads found**:
   - Try different locations or broader criteria
   - Check internet connectivity
   - Some areas may have limited public data

2. **Rate limiting errors**:
   - Increase `rate_limit_delay` in config
   - Try smaller location lists
   - Run during off-peak hours

3. **Missing dependencies**:
   ```bash
   pip install --upgrade -r requirements.txt
   ```

4. **Permission errors**:
   - Ensure write permissions in project directory
   - Check database file permissions

### Debug Mode
Run with verbose logging:
```bash
python cli.py --locations "YourCity,ST" --verbose
```

## 🤝 Contributing

This project is designed to be extensible:

1. **Add new data sources** in `data_sources.py`
2. **Enhance scoring algorithms** in `lead_scoring.py`
3. **Improve parsing logic** for different website structures
4. **Add new export formats** or CRM integrations

## 📜 License

This project is provided for educational and commercial use. Users are responsible for complying with all applicable laws, website terms of service, and data usage policies.

## ⚡ Performance Tips

- Use specific counties for faster assessor searches
- Run during off-peak hours to avoid rate limiting
- Start with small location lists to test effectiveness
- Focus on markets with active commercial real estate
- Consider API keys for enhanced data quality

## 📈 Business Impact

This agent helps energy efficiency companies:
- **Identify qualified prospects** before cold outreach
- **Prioritize sales efforts** on highest-value opportunities
- **Estimate project value** for proposal development
- **Track market opportunities** across multiple regions
- **Reduce prospecting time** through automation

---

**Ready to find your next energy efficiency opportunity?** Start with the demo mode and then target your key markets!

```bash
python cli.py --demo
```