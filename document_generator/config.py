"""
Configuration file for RAG Test Data Generator
Modify these settings to customize the generated data
"""

# Building Configuration
BUILDINGS_CONFIG = {
    "Building A": {
        "name": "Building A - Main Distribution Center",
        "area": 50000,
        "floors": 2,
        "type": "distribution",
        "special_requirements": [],
        "zones": {
            1: {
                "Main Warehouse": {"area": 30000, "equipment_density": "high"},
                "Loading Docks North": {"area": 5000, "equipment_density": "medium"},
                "Loading Docks South": {"area": 5000, "equipment_density": "medium"},
                "Office Area": {"area": 5000, "equipment_density": "high"},
                "MDF Room": {"area": 200, "equipment_density": "critical"},
                "Break Room": {"area": 300, "equipment_density": "low"}
            },
            2: {
                "Administrative Offices": {"area": 4000, "equipment_density": "high"},
                "Conference Rooms": {"area": 1500, "equipment_density": "high"},
                "IT Department": {"area": 1000, "equipment_density": "critical"},
                "IDF Room": {"area": 100, "equipment_density": "critical"}
            }
        }
    },
    "Building B": {
        "name": "Building B - Cold Storage Facility",
        "area": 35000,
        "floors": 1,
        "type": "cold_storage",
        "special_requirements": ["environmental_hardened", "temperature_monitoring"],
        "zones": {
            1: {
                "Freezer Zone 1": {"area": 4000, "equipment_density": "medium", "temp": -20},
                "Freezer Zone 2": {"area": 4000, "equipment_density": "medium", "temp": -20},
                "Freezer Zone 3": {"area": 4000, "equipment_density": "medium", "temp": -20},
                "Freezer Zone 4": {"area": 4000, "equipment_density": "medium", "temp": -20},
                "Refrigerated Zone 5": {"area": 4000, "equipment_density": "medium", "temp": 4},
                "Refrigerated Zone 6": {"area": 4000, "equipment_density": "medium", "temp": 4},
                "Refrigerated Zone 7": {"area": 4000, "equipment_density": "medium", "temp": 4},
                "Refrigerated Zone 8": {"area": 4000, "equipment_density": "medium", "temp": 4},
                "Staging Area": {"area": 3000, "equipment_density": "high", "temp": 20}
            }
        }
    },
    "Building C": {
        "name": "Building C - Shipping and Receiving",
        "area": 40000,
        "floors": 1,
        "type": "shipping",
        "special_requirements": ["high_throughput", "mobile_device_support"],
        "zones": {
            1: {
                "Loading Bays 1-5": {"area": 5000, "equipment_density": "high"},
                "Loading Bays 6-10": {"area": 5000, "equipment_density": "high"},
                "Loading Bays 11-15": {"area": 5000, "equipment_density": "high"},
                "Loading Bays 16-20": {"area": 5000, "equipment_density": "high"},
                "Conveyor System": {"area": 10000, "equipment_density": "medium"},
                "Package Sorting": {"area": 8000, "equipment_density": "high"},
                "Staging Area": {"area": 2000, "equipment_density": "medium"}
            }
        }
    }
}

# Equipment Database
EQUIPMENT_DATABASE = {
    "access_points": {
        "Cisco 3802I": {
            "type": "indoor",
            "frequency": ["2.4GHz", "5.0GHz"],
            "max_power": "30W PoE+",
            "coverage_area": 5000,
            "max_clients": 200,
            "environment": "standard"
        },
        "Cisco 3802E": {
            "type": "outdoor", 
            "frequency": ["2.4GHz", "5.0GHz"],
            "max_power": "30W PoE+",
            "coverage_area": 7500,
            "max_clients": 150,
            "environment": "outdoor"
        },
        "Cisco 3802I-E": {
            "type": "environmental",
            "frequency": ["2.4GHz", "5.0GHz"], 
            "max_power": "60W PoE++",
            "coverage_area": 4000,
            "max_clients": 200,
            "environment": "harsh",
            "temp_range": "-40C to +65C",
            "special_features": ["heating_element", "sealed_enclosure"]
        }
    },
    "switches": {
        "Cisco 9300": {
            "type": "core",
            "ports": 48,
            "power_budget": "1100W PoE+",
            "throughput": "10Gbps",
            "stacking": True
        },
        "Cisco 2960": {
            "type": "access",
            "ports": 24,
            "power_budget": "370W PoE+", 
            "throughput": "1Gbps",
            "stacking": False
        },
        "Cisco 3850": {
            "type": "distribution",
            "ports": 48,
            "power_budget": "715W PoE+",
            "throughput": "5Gbps", 
            "stacking": True
        }
    }
}

# Manager Templates
MANAGER_TEMPLATES = [
    {
        "title": "Senior Floor Manager",
        "responsibilities": ["overall_operations", "staff_supervision", "safety_compliance"],
        "required_certs": ["OSHA", "Leadership"],
        "shift_preference": "Day"
    },
    {
        "title": "Cold Storage Manager", 
        "responsibilities": ["temperature_control", "food_safety", "equipment_monitoring"],
        "required_certs": ["HACCP", "Cold Chain", "Food Safety"],
        "shift_preference": "Day"
    },
    {
        "title": "Shipping Manager",
        "responsibilities": ["logistics", "carrier_coordination", "dock_operations"], 
        "required_certs": ["DOT", "Hazmat", "Logistics"],
        "shift_preference": "Day"
    },
    {
        "title": "IT Infrastructure Manager",
        "responsibilities": ["network_operations", "equipment_maintenance", "security"],
        "required_certs": ["CCNA", "ITIL", "CompTIA Security+"],
        "shift_preference": "Day"
    },
    {
        "title": "Night Shift Supervisor",
        "responsibilities": ["security", "emergency_response", "basic_operations"],
        "required_certs": ["OSHA", "Emergency Response", "Security"],
        "shift_preference": "Night"
    },
    {
        "title": "Evening Shift Coordinator", 
        "responsibilities": ["operations_continuity", "handoff_procedures", "basic_maintenance"],
        "required_certs": ["OSHA", "Equipment Operation"],
        "shift_preference": "Evening"
    }
]

# Incident Templates
INCIDENT_TEMPLATES = {
    "network_connectivity": [
        {
            "title": "WiFi connectivity failure in {location}",
            "description": "Multiple devices unable to connect to wireless network. {impact_description}",
            "common_causes": ["power_failure", "equipment_failure", "configuration_error"],
            "priority_factors": ["business_impact", "area_criticality", "affected_devices"],
            "resolution_time": {"min": 1, "max": 4}  # hours
        },
        {
            "title": "Intermittent network connectivity in {location}",
            "description": "Users experiencing periodic disconnections and slow performance. {impact_description}",
            "common_causes": ["interference", "overutilization", "hardware_degradation"],
            "priority_factors": ["frequency", "user_count", "business_hours"],
            "resolution_time": {"min": 2, "max": 24}
        }
    ],
    "infrastructure": [
        {
            "title": "Environmental control system failure affecting network equipment",
            "description": "Temperature/humidity outside acceptable range for network equipment in {location}. {impact_description}",
            "common_causes": ["hvac_failure", "sensor_failure", "power_issue"],
            "priority_factors": ["equipment_value", "business_criticality", "recovery_time"],
            "resolution_time": {"min": 0.5, "max": 8}
        },
        {
            "title": "Power supply issue affecting network infrastructure", 
            "description": "Network equipment experiencing power-related problems in {location}. {impact_description}",
            "common_causes": ["ups_failure", "power_supply_failure", "electrical_issue"],
            "priority_factors": ["equipment_affected", "backup_systems", "business_impact"],
            "resolution_time": {"min": 1, "max": 12}
        }
    ],
    "security": [
        {
            "title": "Unauthorized device detected on network",
            "description": "Unknown device attempting to access network resources in {location}. {impact_description}",
            "common_causes": ["rogue_device", "contractor_equipment", "compromised_device"],
            "priority_factors": ["security_level", "access_attempted", "location_sensitivity"],
            "resolution_time": {"min": 0.25, "max": 2}
        }
    ],
    "performance": [
        {
            "title": "Network performance degradation in {location}",
            "description": "Users reporting slow network speeds and application timeouts. {impact_description}", 
            "common_causes": ["bandwidth_saturation", "equipment_overload", "configuration_issue"],
            "priority_factors": ["user_count", "business_applications", "degradation_level"],
            "resolution_time": {"min": 1, "max": 8}
        }
    ]
}

# Signal Strength Standards
SIGNAL_STANDARDS = {
    "excellent": {"min": -30, "max": -50, "color": "green"},
    "good": {"min": -51, "max": -65, "color": "yellow"}, 
    "fair": {"min": -66, "max": -75, "color": "orange"},
    "poor": {"min": -76, "max": -85, "color": "red"},
    "unusable": {"min": -86, "max": -100, "color": "darkred"}
}

# Business Impact Descriptions
BUSINESS_IMPACT = {
    "critical": [
        "Operations completely halted in affected area",
        "Safety systems offline - immediate risk",
        "Revenue-generating activities stopped",
        "Customer service severely impacted"
    ],
    "high": [
        "Significant operational delays",
        "Productivity reduced by 50% or more", 
        "Customer service degraded",
        "Inventory management affected"
    ],
    "medium": [
        "Minor operational impact",
        "Workarounds available",
        "Productivity slightly reduced",
        "Administrative functions affected"
    ],
    "low": [
        "No immediate operational impact",
        "Convenience features unavailable",
        "Future planning affected",
        "Non-critical systems impacted"
    ]
}

# Output Configuration
OUTPUT_CONFIG = {
    "pdf_settings": {
        "page_size": "letter",
        "margins": {"top": 72, "bottom": 72, "left": 72, "right": 72},
        "font_family": "Helvetica",
        "include_diagrams": True,
        "include_heatmaps": True
    },
    "excel_settings": {
        "auto_fit_columns": True,
        "freeze_header_row": True,
        "add_filters": True,
        "conditional_formatting": True
    },
    "json_settings": {
        "pretty_print": True,
        "include_metadata": True,
        "timestamp_format": "%Y-%m-%d %H:%M:%S"
    }
}

# Test Scenarios
TEST_SCENARIOS = [
    {
        "name": "Emergency Response Test",
        "description": "Test RAG system's ability to provide emergency contact information",
        "queries": [
            "Who should I call for a network emergency in Building B?",
            "What's the escalation procedure for critical incidents?",
            "Find the night shift supervisor contact information"
        ]
    },
    {
        "name": "Technical Troubleshooting",
        "description": "Test technical knowledge and cross-document references",
        "queries": [
            "Which access points are installed in cold storage areas?",
            "What equipment failed in recent ticket INC0031089?",
            "Show signal strength requirements for warehouse operations"
        ]
    },
    {
        "name": "Operational Planning",
        "description": "Test business context understanding",
        "queries": [
            "Which areas have had the most network incidents?",
            "Who manages the shipping areas during evening shift?",
            "What certifications are required for cold storage managers?"
        ]
    }
]