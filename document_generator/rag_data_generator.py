#!/usr/bin/env python3
"""
RAG Test Data Generator
Generates realistic warehouse facility data including PDFs, Excel files, and ServiceNow tickets
for testing RAG systems with cross-referenced, interconnected data.
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
import pandas as pd
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import Color, green, yellow, red, blue, black, white
from reportlab.graphics.shapes import Drawing, Circle, Line, Rect, String
from reportlab.graphics.charts.legends import Legend
from reportlab.graphics import renderPDF
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.colors import LinearSegmentedColormap
import numpy as np
from io import BytesIO


class WarehouseDataGenerator:
    """Main class for generating warehouse test data"""
    
    def __init__(self, output_dir: str = "test_data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize data structures
        self.buildings = self._init_buildings()
        self.managers = self._init_managers()
        self.tickets = []
        self.equipment_db = self._init_equipment()
        
    def _init_buildings(self) -> Dict[str, Dict]:
        """Initialize building configurations"""
        return {
            "Building A": {
                "name": "Building A - Main Distribution Center",
                "area": 50000,
                "floors": 2,
                "type": "distribution",
                "zones": {
                    1: ["Main Warehouse", "Loading Docks North", "Loading Docks South", "Office Area", "MDF Room", "Break Room"],
                    2: ["Administrative Offices", "Conference Rooms", "IT Department", "IDF Room"]
                },
                "equipment": {
                    1: ["AP-A1-WH-01", "AP-A1-WH-02", "AP-A1-WH-03", "AP-A1-LD-North-01", "AP-A1-LD-South-01", 
                        "AP-A1-Office-01", "AP-A1-MDF-01", "SW-A1-MDF-01", "SW-A1-MDF-02"],
                    2: ["AP-A2-Admin-01", "AP-A2-Admin-02", "AP-A2-Conf-01", "AP-A2-IT-01", "SW-A2-IDF-01"]
                }
            },
            "Building B": {
                "name": "Building B - Cold Storage Facility", 
                "area": 35000,
                "floors": 1,
                "type": "cold_storage",
                "zones": {
                    1: ["Freezer Zone 1", "Freezer Zone 2", "Freezer Zone 3", "Freezer Zone 4", 
                        "Refrigerated Zone 5", "Refrigerated Zone 6", "Refrigerated Zone 7", 
                        "Refrigerated Zone 8", "Staging Area"]
                },
                "equipment": {
                    1: [f"AP-B1-FZ{i}-01" for i in range(1,5)] + [f"AP-B1-RZ{i}-01" for i in range(5,9)] + 
                       ["AP-B1-Staging-01", "SW-B1-MDF-01"]
                }
            },
            "Building C": {
                "name": "Building C - Shipping and Receiving",
                "area": 40000, 
                "floors": 1,
                "type": "shipping",
                "zones": {
                    1: ["Loading Bays 1-5", "Loading Bays 6-10", "Loading Bays 11-15", "Loading Bays 16-20",
                        "Conveyor System", "Package Sorting", "Staging Area"]
                },
                "equipment": {
                    1: [f"AP-C1-Bay{i:02d}-01" for i in range(1,21,5)] + ["AP-C1-Conv-01", "AP-C1-Sort-01", "SW-C1-MDF-01"]
                }
            }
        }
    
    def _init_managers(self) -> List[Dict]:
        """Initialize manager data"""
        managers = [
            {"id": "EMP001", "name": "John Smith", "title": "Senior Floor Manager", 
             "building": "Building A", "floor": 1, "area": "Main Warehouse, Loading Docks",
             "phone": "555-0101", "email": "jsmith@company.com", "start_date": "2019-03-15",
             "certifications": "OSHA, Forklift", "shift": "Day"},
            
            {"id": "EMP002", "name": "Maria Garcia", "title": "Floor Manager",
             "building": "Building A", "floor": 2, "area": "Administrative Offices", 
             "phone": "555-0102", "email": "mgarcia@company.com", "start_date": "2020-07-22",
             "certifications": "Six Sigma", "shift": "Day"},
            
            {"id": "EMP003", "name": "David Chen", "title": "Cold Storage Manager",
             "building": "Building B", "floor": 1, "area": "Freezer Zones 1-4",
             "phone": "555-0103", "email": "dchen@company.com", "start_date": "2018-11-10", 
             "certifications": "HACCP, Cold Chain", "shift": "Day"},
            
            {"id": "EMP004", "name": "Sarah Johnson", "title": "Shipping Manager",
             "building": "Building C", "floor": 1, "area": "Loading Bays 1-10",
             "phone": "555-0104", "email": "sjohnson@company.com", "start_date": "2021-02-28",
             "certifications": "DOT, Hazmat", "shift": "Day"},
             
            {"id": "EMP005", "name": "Michael Brown", "title": "IT Infrastructure Manager",
             "building": "Building A", "floor": 2, "area": "IT Department, MDF/IDF",
             "phone": "555-0105", "email": "mbrown@company.com", "start_date": "2017-09-05",
             "certifications": "CCNA, ITIL", "shift": "Day"},
             
            # Additional managers for comprehensive coverage
            {"id": "EMP006", "name": "Lisa Wong", "title": "Night Shift Supervisor",
             "building": "Building A", "floor": 1, "area": "All Areas",
             "phone": "555-0106", "email": "lwong@company.com", "start_date": "2020-01-15",
             "certifications": "OSHA, Emergency Response", "shift": "Night"},
             
            {"id": "EMP007", "name": "Robert Taylor", "title": "Cold Storage Specialist", 
             "building": "Building B", "floor": 1, "area": "Refrigerated Zones 5-8",
             "phone": "555-0107", "email": "rtaylor@company.com", "start_date": "2019-08-12",
             "certifications": "HACCP, Temperature Control", "shift": "Evening"},
             
            {"id": "EMP008", "name": "Amanda Rodriguez", "title": "Receiving Manager",
             "building": "Building C", "floor": 1, "area": "Loading Bays 11-20", 
             "phone": "555-0108", "email": "arodriguez@company.com", "start_date": "2021-06-03",
             "certifications": "Inventory Management", "shift": "Day"}
        ]
        return managers
    
    def _init_equipment(self) -> Dict[str, Dict]:
        """Initialize network equipment database"""
        equipment_types = {
            "AP": {
                "models": ["Cisco 3802I", "Cisco 3802E", "Cisco 3802I-E"],
                "specs": {
                    "frequency": ["2.4GHz", "5.0GHz"],
                    "power": "30W PoE+",
                    "coverage": "5000 sq ft",
                    "concurrent_clients": 200
                }
            },
            "SW": {
                "models": ["Cisco 9300", "Cisco 2960", "Cisco 3850"],
                "specs": {
                    "ports": [24, 48],
                    "power": "PoE+",
                    "throughput": "1Gbps"
                }
            }
        }
        return equipment_types

    def generate_all_data(self):
        """Generate all test data files"""
        print("Generating RAG test data...")
        
        # Generate PDFs for each building
        for building_name, building_data in self.buildings.items():
            self.generate_building_pdf(building_name, building_data)
        
        # Generate Excel file with manager data
        self.generate_manager_excel()
        
        # Generate ServiceNow tickets
        self.generate_servicenow_tickets()
        
        print(f"Test data generation complete! Files saved to {self.output_dir}")

    def generate_building_pdf(self, building_name: str, building_data: Dict):
        """Generate PDF for building layout and network equipment matching the wireless survey format"""
        filename = f"{building_name.replace(' ', '')}_Network_Layout.pdf"
        filepath = self.output_dir / filename
        
        doc = SimpleDocTemplate(str(filepath), pagesize=letter, 
                              topMargin=0.5*inch, bottomMargin=0.5*inch,
                              leftMargin=0.5*inch, rightMargin=0.5*inch)
        styles = getSampleStyleSheet()
        story = []
        
        # Create custom styles matching the survey format
        header_style = ParagraphStyle(
            'SurveyHeader',
            parent=styles['Normal'],
            fontSize=12,
            textColor=Color(0.2, 0.2, 0.2),
            alignment=0
        )
        
        title_style = ParagraphStyle(
            'SurveyTitle',
            parent=styles['Heading1'],
            fontSize=16,
            fontName='Helvetica-Bold',
            textColor=Color(0, 0, 0),
            alignment=0,
            spaceAfter=12
        )
        
        # Generate pages for each floor matching the survey format
        for floor_num in range(1, building_data['floors'] + 1):
            # Floor title page
            story.append(Paragraph(f"{building_data['name']}", title_style))
            story.append(Paragraph(f"Floor {floor_num} - Pre-Deployment Signal Map", header_style))
            story.append(Spacer(1, 20))
            
            # 5.0 GHz Coverage Page
            self._add_coverage_page(story, building_name, floor_num, "5.0 GHz", building_data)
            
            # 2.4 GHz Coverage Page  
            self._add_coverage_page(story, building_name, floor_num, "2.4 GHz", building_data)
            
            # Site Plan with AP Placement
            self._add_site_plan_page(story, building_name, floor_num, building_data)
        
        doc.build(story)
        print(f"Generated {filename}")

    def _add_coverage_page(self, story: list, building_name: str, floor_num: int, frequency: str, building_data: Dict):
        """Add coverage heat map page matching the survey format"""
        from reportlab.lib.pagesizes import letter
        from reportlab.graphics.shapes import Drawing, Rect, String, Circle
        from reportlab.graphics import renderPDF
        
        # Page header
        header_table_data = [
            ['PRE-DEPLOYMENT', f'{building_name} - Floor {floor_num}', 'ToC'],
            ['SIGNAL MAP', f'{frequency} Signal (RSSI) -65 dBm threshold', '']
        ]
        
        header_table = Table(header_table_data, colWidths=[1.5*inch, 4*inch, 0.5*inch])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 1), Color(0.4, 0.4, 0.4)),
            ('TEXTCOLOR', (0, 0), (0, 1), white),
            ('FONTNAME', (0, 0), (0, 1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (0, 1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, black)
        ]))
        
        story.append(header_table)
        story.append(Spacer(1, 20))
        
        # Create heat map drawing
        heat_map = self._create_heat_map_drawing(building_name, floor_num, frequency, building_data)
        story.append(heat_map)
        story.append(Spacer(1, 20))
        
        # Add legend
        legend_data = [
            ['Signal Strength (RSSI)', 'Coverage Quality'],
            ['-30 to -50 dBm', 'Excellent (Dark Green)'],
            ['-51 to -65 dBm', 'Good (Green)'],
            ['-66 to -75 dBm', 'Fair (Yellow)'],
            ['-76 to -85 dBm', 'Poor (Orange)'],
            ['Below -85 dBm', 'Unusable (Red)']
        ]
        
        legend_table = Table(legend_data, colWidths=[2*inch, 2.5*inch])
        legend_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), Color(0.8, 0.8, 0.8)),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, black),
            ('FONTSIZE', (0, 0), (-1, -1), 9)
        ]))
        
        story.append(legend_table)
        story.append(Spacer(1, 30))

    def _create_heat_map_drawing(self, building_name: str, floor_num: int, frequency: str, building_data: Dict) -> Drawing:
        """Create a heat map drawing matching the survey format"""
        from reportlab.graphics.shapes import Drawing, Rect, String, Circle, Line
        from reportlab.lib.colors import Color, green, yellow, red, orange
        
        # Create drawing canvas
        d = Drawing(6*inch, 4*inch)
        
        # Background floor plan outline
        d.add(Rect(50, 50, 350, 250, strokeColor=black, fillColor=Color(0.95, 0.95, 0.95)))
        
        # Add room divisions based on building type
        if building_data['type'] == 'distribution':
            # Warehouse layout
            d.add(Line(50, 200, 400, 200, strokeColor=black))  # Horizontal division
            d.add(Line(250, 50, 250, 300, strokeColor=black))  # Vertical division
            
        elif building_data['type'] == 'cold_storage':
            # Cold storage zones
            for i in range(4):
                x = 50 + i * 87.5
                d.add(Line(x, 50, x, 300, strokeColor=black))
                
        # Add heat map colors (simulate coverage)
        coverage_zones = [
            {'x': 75, 'y': 75, 'color': green, 'size': 60},    # Excellent
            {'x': 200, 'y': 150, 'color': green, 'size': 80},  # Good  
            {'x': 325, 'y': 225, 'color': yellow, 'size': 70}, # Fair
            {'x': 150, 'y': 250, 'color': orange, 'size': 50}, # Poor
        ]
        
        for zone in coverage_zones:
            d.add(Rect(zone['x']-zone['size']//2, zone['y']-zone['size']//2, 
                          zone['size'], zone['size'], 
                          fillColor=zone['color'], fillOpacity=0.4, strokeColor=None))
        
        # Add access points
        equipment_list = building_data.get('equipment', {}).get(floor_num, [])
        ap_count = len([eq for eq in equipment_list if eq.startswith('AP')])
        
        ap_positions = [
            {'x': 100, 'y': 100, 'id': '06'},
            {'x': 200, 'y': 180, 'id': '05'}, 
            {'x': 320, 'y': 250, 'id': '04'},
            {'x': 150, 'y': 280, 'id': '09'},
            {'x': 350, 'y': 120, 'id': '03'}
        ]
        
        for i, pos in enumerate(ap_positions[:min(ap_count, 5)]):
            # AP circle
            d.add(Circle(pos['x'], pos['y'], 15, fillColor=Color(0, 0.7, 1), strokeColor=white, strokeWidth=2))
            # AP ID
            d.add(String(pos['x']-5, pos['y']-3, pos['id'], fontSize=8, fillColor=white))
        
        # Add compass arrow
        d.add(Line(30, 280, 30, 300, strokeColor=black, strokeWidth=2))
        d.add(Line(30, 300, 25, 295, strokeColor=black, strokeWidth=2))
        d.add(Line(30, 300, 35, 295, strokeColor=black, strokeWidth=2))
        d.add(String(10, 270, 'N', fontSize=10, fillColor=black))
        
        return d

    def _add_site_plan_page(self, story: list, building_name: str, floor_num: int, building_data: Dict):
        """Add site plan page with AP placement details"""
        from reportlab.graphics.shapes import Drawing, Rect, Circle, String
        
        # Page header
        header_table_data = [
            ['SITE PLAN', f'{building_name} - Floor {floor_num}', 'ToC'],
            ['', 'AP PLACEMENT', '']
        ]
        
        header_table = Table(header_table_data, colWidths=[1.5*inch, 4*inch, 0.5*inch])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 1), Color(0.4, 0.4, 0.4)),
            ('TEXTCOLOR', (0, 0), (0, 1), white),
            ('FONTNAME', (0, 0), (0, 1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (0, 1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, black)
        ]))
        
        story.append(header_table)
        story.append(Spacer(1, 20))
        
        # AP Model legend
        ap_legend_data = [
            ['AP MODEL', 'AP/ANTENNA TYPE', 'MDF/IDF'],
            ['Cisco 3802I', 'Internal ●', 'MDF'],
            ['Cisco 3802E', 'Ext. Sector ●', 'IDF'],
            ['Cisco 1562E', 'Ext. Omni ●', 'IDF']
        ]
        
        ap_legend_table = Table(ap_legend_data, colWidths=[1.5*inch, 2*inch, 1*inch])
        ap_legend_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), Color(0.8, 0.8, 0.8)),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, black),
            ('FONTSIZE', (0, 0), (-1, -1), 9)
        ]))
        
        story.append(ap_legend_table)
        story.append(Spacer(1, 20))
        
        # Site plan drawing
        site_plan = self._create_site_plan_drawing(building_name, floor_num, building_data)
        story.append(site_plan)
        story.append(Spacer(1, 20))

    def _create_site_plan_drawing(self, building_name: str, floor_num: int, building_data: Dict) -> Drawing:
        """Create detailed site plan with AP placement"""
        from reportlab.graphics.shapes import Drawing, Rect, Circle, String, Line
        
        d = Drawing(6*inch, 4*inch)
        
        # Building outline
        d.add(Rect(50, 50, 350, 250, strokeColor=black, fillColor=white, strokeWidth=2))
        
        # Room layout based on building type
        if building_data['type'] == 'distribution':
            # Office areas
            d.add(Rect(300, 200, 100, 100, strokeColor=black, fillColor=Color(0.9, 0.9, 0.9)))
            d.add(String(320, 240, 'Offices', fontSize=8))
            
            # Warehouse floor
            d.add(Rect(50, 50, 250, 150, strokeColor=black, fillColor=Color(0.95, 0.95, 0.95)))
            d.add(String(150, 120, 'Warehouse Floor', fontSize=10))
            
            # Loading docks
            d.add(Rect(50, 200, 100, 100, strokeColor=black, fillColor=Color(0.8, 0.8, 0.8)))
            d.add(String(70, 240, 'Loading', fontSize=8))
            
        elif building_data['type'] == 'cold_storage':
            # Freezer zones
            for i in range(4):
                x = 50 + i * 87.5
                d.add(Rect(x, 50, 87.5, 100, strokeColor=black, fillColor=Color(0.7, 0.9, 1)))
                d.add(String(x+20, 90, f'Zone {i+1}', fontSize=8))
        
        # Add access points with different types
        equipment_list = building_data.get('equipment', {}).get(floor_num, [])
        ap_positions = [
            {'x': 100, 'y': 100, 'type': 'Cisco 3802I', 'color': green},
            {'x': 200, 'y': 180, 'type': 'Cisco 3802I', 'color': green}, 
            {'x': 320, 'y': 250, 'type': 'Cisco 3802E', 'color': yellow},
            {'x': 150, 'y': 280, 'type': 'Cisco 3802I', 'color': green}
        ]
        
        for i, pos in enumerate(ap_positions[:len([eq for eq in equipment_list if eq.startswith('AP')])]):
            d.add(Circle(pos['x'], pos['y'], 12, fillColor=pos['color'], strokeColor=black, strokeWidth=1))
            d.add(String(pos['x']-8, pos['y']-3, f'{i+6:02d}', fontSize=8))
        
        return d

    def _generate_coverage_text(self, building_name: str, floor_num: int) -> str:
        """Generate realistic signal coverage text"""
        base_coverage = {
            "Building A": {
                1: "Main warehouse area shows excellent 5.0 GHz coverage (-35 to -50 dBm) with minor dead zones near metal racking. Loading dock areas maintain good coverage (-45 to -65 dBm) with some interference during peak truck traffic. Office areas have optimal coverage across both frequency bands.",
                2: "Administrative offices maintain strong signal strength (-30 to -45 dBm) throughout. Conference rooms equipped with dedicated APs for video conferencing requirements. IT department has redundant coverage for critical infrastructure monitoring."
            },
            "Building B": {
                1: "Cold storage zones present unique challenges with environmental enclosures required for sub-zero operations. Freezer zones 1-4 utilize Cisco 3802I-E models with heating elements. Metal shelving causes localized interference requiring additional APs for full coverage. Temperature-sensitive equipment monitored continuously."
            },
            "Building C": {
                1: "Loading bay coverage optimized for handheld scanner operations with minimum -55 dBm throughout operational areas. Conveyor system areas have elevated APs to avoid interference from moving equipment. Package sorting area requires high-density coverage for simultaneous device connections."
            }
        }
        
        return base_coverage.get(building_name, {}).get(floor_num, "Standard coverage deployment with good signal strength across operational areas.")

    def generate_manager_excel(self):
        """Generate Excel file with manager information"""
        filename = "Facility_Managers_2024.xlsx"
        filepath = self.output_dir / filename
        
        with pd.ExcelWriter(str(filepath), engine='openpyxl') as writer:
            # Manager Roster Sheet
            df_managers = pd.DataFrame(self.managers)
            df_managers.to_excel(writer, sheet_name='Manager Roster', index=False)
            
            # Area Coverage Schedule Sheet
            schedule_data = self._generate_coverage_schedule()
            df_schedule = pd.DataFrame(schedule_data)
            df_schedule.to_excel(writer, sheet_name='Area Coverage Schedule', index=False)
            
            # Contact Matrix Sheet
            contact_data = self._generate_contact_matrix()
            df_contacts = pd.DataFrame(contact_data)
            df_contacts.to_excel(writer, sheet_name='Contact Matrix', index=False)
        
        print(f"Generated {filename}")

    def _generate_coverage_schedule(self) -> List[Dict]:
        """Generate weekly coverage schedule"""
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        shifts = ['Day (6AM-2PM)', 'Evening (2PM-10PM)', 'Night (10PM-6AM)']
        
        schedule = []
        for day in days:
            for shift in shifts:
                # Assign managers based on their primary shift and building
                primary_managers = [m for m in self.managers if shift.split()[0].lower() in m['shift'].lower()]
                if not primary_managers:
                    primary_managers = [m for m in self.managers if m['shift'] == 'Day']
                
                manager = random.choice(primary_managers)
                
                schedule.append({
                    'Day': day,
                    'Shift': shift,
                    'Primary Manager': manager['name'],
                    'Building': manager['building'],
                    'Contact': manager['phone'],
                    'Backup': random.choice([m['name'] for m in self.managers if m['name'] != manager['name']])
                })
        
        return schedule

    def _generate_contact_matrix(self) -> List[Dict]:
        """Generate emergency contact matrix"""
        contacts = []
        
        # Internal contacts
        for manager in self.managers:
            contacts.append({
                'Contact Type': 'Internal',
                'Name': manager['name'],
                'Title': manager['title'],
                'Area': f"{manager['building']} - {manager['area']}",
                'Primary Phone': manager['phone'],
                'Email': manager['email'],
                'Escalation Level': 'Primary'
            })
        
        # Vendor contacts
        vendor_contacts = [
            {'Contact Type': 'Vendor', 'Name': 'Cisco TAC', 'Title': 'Technical Support',
             'Area': 'Network Equipment', 'Primary Phone': '1-800-553-2447', 
             'Email': 'tac@cisco.com', 'Escalation Level': 'L1 Support'},
            
            {'Contact Type': 'Vendor', 'Name': 'DataCenter Solutions', 'Title': 'Field Engineer',
             'Area': 'Infrastructure', 'Primary Phone': '555-DATACTR', 
             'Email': 'support@dcsi.com', 'Escalation Level': 'Emergency'},
             
            {'Contact Type': 'Emergency', 'Name': 'Facilities Emergency', 'Title': 'Emergency Response',
             'Area': 'All Buildings', 'Primary Phone': '911', 
             'Email': 'emergency@company.com', 'Escalation Level': 'Critical'}
        ]
        
        contacts.extend(vendor_contacts)
        return contacts

    def generate_servicenow_tickets(self):
        """Generate realistic ServiceNow incident tickets"""
        base_date = datetime.now() - timedelta(days=30)
        
        ticket_templates = [
            {
                "category": "Network",
                "subcategory": "Wireless Connectivity", 
                "priority": "High",
                "title": "No WiFi signal at loading dock - scanners not working",
                "description": "Multiple handheld scanners unable to connect to WiFi at the {location}. Workers cannot process shipments.",
                "resolution": "Faulty PoE injector replaced. Signal restored to normal levels."
            },
            {
                "category": "Network",
                "subcategory": "Signal Quality",
                "priority": "Medium", 
                "title": "Intermittent WiFi drops during video calls",
                "description": "{location} experiencing frequent disconnections during Teams calls. Signal shows full bars but drops every 10-15 minutes.",
                "resolution": "Channel optimization and power adjustment completed"
            },
            {
                "category": "Infrastructure", 
                "subcategory": "Environmental",
                "priority": "Critical",
                "title": "Network equipment failure in freezer - temperature alarm system offline",
                "description": "Access point in {location} has failed. Temperature monitoring system cannot communicate. Risk of product loss.",
                "resolution": "Emergency replacement completed. Environmental enclosure heating element repaired."
            },
            {
                "category": "Network",
                "subcategory": "Coverage Extension", 
                "priority": "Low",
                "title": "Request WiFi coverage for new expansion area",
                "description": "New area ({location}) coming online next month. Need network coverage for additional devices.",
                "resolution": "Site survey completed. Installation scheduled."
            },
            {
                "category": "Security",
                "subcategory": "Access Control",
                "priority": "High", 
                "title": "Unauthorized access attempt to network equipment",
                "description": "Security alert: Unknown device attempted connection to management VLAN in {location}. Investigation needed.",
                "resolution": "False alarm - contractor access credentials updated"
            }
        ]
        
        tickets = []
        
        for i, template in enumerate(ticket_templates, 1):
            # Select appropriate location and manager based on ticket type
            if "freezer" in template["title"].lower():
                building = "Building B"
                location = "Freezer Zone 2" 
                manager = next(m for m in self.managers if "Cold Storage" in m['title'])
            elif "loading dock" in template["title"].lower():
                building = random.choice(["Building A", "Building C"])
                location = "Loading Dock North" if building == "Building A" else "Loading Bays 1-5"
                manager = next(m for m in self.managers if m['building'] == building and 'Manager' in m['title'])
            elif "conference" in template["description"].lower():
                building = "Building A"
                location = "Second Floor Conference Room C"
                manager = next(m for m in self.managers if m['building'] == building and m['floor'] == 2)
            else:
                building = random.choice(list(self.buildings.keys()))
                location = random.choice(list(self.buildings[building]['zones'].values())[0])
                manager = random.choice([m for m in self.managers if m['building'] == building])
            
            created_date = base_date + timedelta(days=i*2, hours=random.randint(0, 23))
            resolved_date = created_date + timedelta(hours=random.randint(1, 48))
            
            ticket_num = f"INC{30000 + i:06d}"
            
            ticket = {
                "number": ticket_num,
                "priority": template["priority"],
                "category": template["category"], 
                "subcategory": template["subcategory"],
                "created": created_date.strftime("%Y-%m-%d %H:%M:%S"),
                "reporter": random.choice(["Tom Wilson", "Jane Doe", "Security Team", "Night Shift Supervisor"]),
                "assigned_to": manager["name"],
                "location": f"{building} - {location}",
                "short_description": template["title"],
                "description": template["description"].format(location=location),
                "resolution": template["resolution"],
                "resolved": resolved_date.strftime("%Y-%m-%d %H:%M:%S"),
                "work_notes": self._generate_work_notes(created_date, resolved_date),
                "related_manager": manager["id"],
                "related_building": building
            }
            
            tickets.append(ticket)
        
        # Save tickets as JSON
        tickets_file = self.output_dir / "ServiceNow_Incidents_Last30Days.json"
        with open(tickets_file, 'w') as f:
            json.dump(tickets, f, indent=2)
        
        print(f"Generated {len(tickets)} ServiceNow tickets")

    def _generate_work_notes(self, created: datetime, resolved: datetime) -> List[str]:
        """Generate realistic work notes for tickets"""
        notes = []
        current = created + timedelta(minutes=15)
        
        work_steps = [
            "Initial investigation started",
            "On-site inspection completed", 
            "Equipment status checked",
            "Identified root cause",
            "Replacement parts ordered",
            "Configuration changes applied",
            "Solution implemented", 
            "Testing completed",
            "Monitoring for stability"
        ]
        
        while current < resolved and len(notes) < 6:
            step = random.choice(work_steps)
            work_steps.remove(step)  # Don't repeat steps
            notes.append(f"{current.strftime('%H:%M')} - {step}")
            current += timedelta(minutes=random.randint(15, 120))
        
        return notes


def main():
    """Main execution function"""
    generator = WarehouseDataGenerator()
    generator.generate_all_data()
    
    # Print summary
    print("\n" + "="*50)
    print("RAG TEST DATA GENERATION SUMMARY")
    print("="*50)
    print(f"Output directory: {generator.output_dir}")
    print(f"Buildings: {len(generator.buildings)}")
    print(f"Managers: {len(generator.managers)}")
    print(f"Generated files:")
    for file in generator.output_dir.glob("*"):
        print(f"  - {file.name}")
    print("\nTest queries to try:")
    print("1. 'Which manager handles Building B freezer issues?'")
    print("2. 'Show network equipment in Building A loading dock'") 
    print("3. 'List all critical incidents from last month'")
    print("4. 'What's the contact info for cold storage emergencies?'")


if __name__ == "__main__":
    main()