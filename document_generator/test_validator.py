#!/usr/bin/env python3
"""
Test Data Validator for RAG Test Data Generator
Validates the generated data files and tests cross-references
"""

import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any
import re


class DataValidator:
    """Validates generated test data for completeness and consistency"""
    
    def __init__(self, data_dir: str = "test_data"):
        self.data_dir = Path(data_dir)
        self.validation_results = []
        
    def validate_all(self) -> Dict[str, Any]:
        """Run all validation tests"""
        print("Validating generated test data...\n")
        
        results = {
            "files_present": self.check_files_present(),
            "excel_validation": self.validate_excel_data(),
            "json_validation": self.validate_json_data(), 
            "cross_references": self.validate_cross_references(),
            "data_consistency": self.validate_data_consistency()
        }
        
        self.print_validation_summary(results)
        return results
    
    def check_files_present(self) -> Dict[str, bool]:
        """Check if all expected files were generated"""
        expected_files = [
            "BuildingA_Network_Layout.pdf",
            "BuildingB_Network_Layout.pdf", 
            "BuildingC_Network_Layout.pdf",
            "Facility_Managers_2024.xlsx",
            "ServiceNow_Incidents_Last30Days.json"
        ]
        
        results = {}
        for filename in expected_files:
            filepath = self.data_dir / filename
            results[filename] = filepath.exists()
            
        print("File Presence Check:")
        for filename, exists in results.items():
            status = "✓" if exists else "✗"
            print(f"  {status} {filename}")
        print()
        
        return results
    
    def validate_excel_data(self) -> Dict[str, Any]:
        """Validate Excel file structure and content"""
        excel_file = self.data_dir / "Facility_Managers_2024.xlsx"
        
        if not excel_file.exists():
            return {"error": "Excel file not found"}
        
        try:
            # Check sheets exist
            xl_file = pd.ExcelFile(excel_file)
            expected_sheets = ["Manager Roster", "Area Coverage Schedule", "Contact Matrix"]
            sheets_present = {sheet: sheet in xl_file.sheet_names for sheet in expected_sheets}
            
            # Validate Manager Roster
            managers_df = pd.read_excel(excel_file, sheet_name="Manager Roster")
            required_columns = ["id", "name", "title", "building", "phone", "email"]
            columns_present = {col: col in managers_df.columns for col in required_columns}
            
            # Check data quality
            manager_count = len(managers_df)
            unique_ids = managers_df["id"].nunique() if "id" in managers_df.columns else 0
            unique_emails = managers_df["email"].nunique() if "email" in managers_df.columns else 0
            
            results = {
                "sheets_present": sheets_present,
                "columns_present": columns_present,
                "manager_count": manager_count,
                "unique_ids": unique_ids,
                "unique_emails": unique_emails,
                "data_quality": {
                    "duplicate_ids": manager_count - unique_ids,
                    "duplicate_emails": manager_count - unique_emails
                }
            }
            
            print("Excel Validation:")
            print(f"  Sheets present: {sum(sheets_present.values())}/{len(expected_sheets)}")
            print(f"  Required columns: {sum(columns_present.values())}/{len(required_columns)}")
            print(f"  Manager records: {manager_count}")
            print(f"  Data quality: {results['data_quality']}")
            print()
            
            return results
            
        except Exception as e:
            return {"error": str(e)}
    
    def validate_json_data(self) -> Dict[str, Any]:
        """Validate JSON ticket data structure"""
        json_file = self.data_dir / "ServiceNow_Incidents_Last30Days.json"
        
        if not json_file.exists():
            return {"error": "JSON file not found"}
        
        try:
            with open(json_file, 'r') as f:
                tickets = json.load(f)
            
            if not isinstance(tickets, list):
                return {"error": "JSON should contain a list of tickets"}
            
            # Check ticket structure
            required_fields = ["number", "priority", "category", "created", "assigned_to", "location"]
            ticket_count = len(tickets)
            
            field_coverage = {}
            priorities = {}
            categories = {}
            
            for ticket in tickets:
                for field in required_fields:
                    if field in field_coverage:
                        field_coverage[field] += (1 if field in ticket else 0)
                    else:
                        field_coverage[field] = (1 if field in ticket else 0)
                
                # Analyze priorities and categories
                if "priority" in ticket:
                    priority = ticket["priority"]
                    priorities[priority] = priorities.get(priority, 0) + 1
                    
                if "category" in ticket:
                    category = ticket["category"]
                    categories[category] = categories.get(category, 0) + 1
            
            results = {
                "ticket_count": ticket_count,
                "field_coverage": {field: count/ticket_count for field, count in field_coverage.items()},
                "priority_distribution": priorities,
                "category_distribution": categories
            }
            
            print("JSON Validation:")
            print(f"  Ticket count: {ticket_count}")
            print(f"  Field coverage: {len([f for f, c in results['field_coverage'].items() if c == 1.0])}/{len(required_fields)} complete")
            print(f"  Priority types: {list(priorities.keys())}")
            print(f"  Category types: {list(categories.keys())}")
            print()
            
            return results
            
        except Exception as e:
            return {"error": str(e)}
    
    def validate_cross_references(self) -> Dict[str, Any]:
        """Validate cross-references between documents"""
        results = {
            "building_references": self.check_building_references(),
            "manager_references": self.check_manager_references(),
            "equipment_references": self.check_equipment_references()
        }
        
        print("Cross-Reference Validation:")
        for ref_type, ref_results in results.items():
            if isinstance(ref_results, dict) and "matches" in ref_results:
                print(f"  {ref_type}: {ref_results['matches']} valid references found")
            else:
                print(f"  {ref_type}: {ref_results}")
        print()
        
        return results
    
    def check_building_references(self) -> Dict[str, Any]:
        """Check if building names are consistent across documents"""
        building_names = ["Building A", "Building B", "Building C"]
        
        # Check Excel file
        excel_file = self.data_dir / "Facility_Managers_2024.xlsx"
        excel_buildings = set()
        
        if excel_file.exists():
            try:
                managers_df = pd.read_excel(excel_file, sheet_name="Manager Roster")
                if "building" in managers_df.columns:
                    excel_buildings = set(managers_df["building"].unique())
            except:
                pass
        
        # Check JSON file
        json_file = self.data_dir / "ServiceNow_Incidents_Last30Days.json"
        json_buildings = set()
        
        if json_file.exists():
            try:
                with open(json_file, 'r') as f:
                    tickets = json.load(f)
                for ticket in tickets:
                    if "location" in ticket:
                        # Extract building name from location
                        for building in building_names:
                            if building in ticket["location"]:
                                json_buildings.add(building)
            except:
                pass
        
        matches = len(set(building_names) & excel_buildings & json_buildings)
        
        return {
            "expected": building_names,
            "excel_buildings": list(excel_buildings),
            "json_buildings": list(json_buildings), 
            "matches": matches
        }
    
    def check_manager_references(self) -> Dict[str, Any]:
        """Check if manager assignments are consistent"""
        excel_file = self.data_dir / "Facility_Managers_2024.xlsx"
        json_file = self.data_dir / "ServiceNow_Incidents_Last30Days.json"
        
        managers = set()
        ticket_assignees = set()
        
        # Get managers from Excel
        if excel_file.exists():
            try:
                managers_df = pd.read_excel(excel_file, sheet_name="Manager Roster")
                if "name" in managers_df.columns:
                    managers = set(managers_df["name"].tolist())
            except:
                pass
        
        # Get assignees from tickets
        if json_file.exists():
            try:
                with open(json_file, 'r') as f:
                    tickets = json.load(f)
                for ticket in tickets:
                    if "assigned_to" in ticket:
                        ticket_assignees.add(ticket["assigned_to"])
            except:
                pass
        
        matches = len(managers & ticket_assignees)
        
        return {
            "managers_count": len(managers),
            "assignees_count": len(ticket_assignees),
            "matches": matches,
            "coverage": matches / len(ticket_assignees) if ticket_assignees else 0
        }
    
    def check_equipment_references(self) -> Dict[str, Any]:
        """Check equipment naming consistency"""
        # This would ideally parse PDF content, but for now we'll simulate
        # In a real implementation, you'd use PDF parsing libraries
        equipment_patterns = [
            r"AP-[ABC]\d+-\w+-\d+",  # Access point naming
            r"SW-[ABC]\d+-\w+-\d+",  # Switch naming
            r"Cisco \d{4}[IE]?"      # Equipment models
        ]
        
        return {
            "patterns_defined": len(equipment_patterns),
            "note": "PDF parsing required for full validation"
        }
    
    def validate_data_consistency(self) -> Dict[str, Any]:
        """Check overall data consistency"""
        issues = []
        
        # Check file sizes (basic sanity check)
        file_sizes = {}
        for file in self.data_dir.glob("*"):
            file_sizes[file.name] = file.stat().st_size
        
        # PDFs should be substantial (>10KB)
        pdf_files = [f for f in file_sizes.keys() if f.endswith('.pdf')]
        small_pdfs = [f for f in pdf_files if file_sizes[f] < 10000]
        
        if small_pdfs:
            issues.append(f"Small PDF files (may be incomplete): {small_pdfs}")
        
        # Excel should have multiple sheets worth of data
        excel_files = [f for f in file_sizes.keys() if f.endswith('.xlsx')]
        small_excel = [f for f in excel_files if file_sizes[f] < 5000]
        
        if small_excel:
            issues.append(f"Small Excel files: {small_excel}")
        
        results = {
            "file_sizes": file_sizes,
            "issues": issues,
            "total_size": sum(file_sizes.values())
        }
        
        print("Data Consistency:")
        print(f"  Total data size: {results['total_size']:,} bytes")
        print(f"  Issues found: {len(issues)}")
        for issue in issues:
            print(f"    - {issue}")
        print()
        
        return results
    
    def print_validation_summary(self, results: Dict[str, Any]):
        """Print overall validation summary"""
        print("="*50)
        print("VALIDATION SUMMARY")
        print("="*50)
        
        total_tests = 0
        passed_tests = 0
        
        # File presence
        file_results = results.get("files_present", {})
        total_tests += len(file_results)
        passed_tests += sum(file_results.values())
        
        # Excel validation
        excel_results = results.get("excel_validation", {})
        if "error" not in excel_results:
            sheets = excel_results.get("sheets_present", {})
            columns = excel_results.get("columns_present", {})
            total_tests += len(sheets) + len(columns)
            passed_tests += sum(sheets.values()) + sum(columns.values())
        
        # Cross-references
        cross_ref = results.get("cross_references", {})
        if "building_references" in cross_ref:
            building_refs = cross_ref["building_references"]
            if "matches" in building_refs:
                total_tests += 1
                passed_tests += (1 if building_refs["matches"] >= 2 else 0)
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Tests passed: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        if success_rate >= 90:
            print("✓ Data generation SUCCESSFUL - Ready for RAG testing")
        elif success_rate >= 75:
            print("⚠ Data generation MOSTLY SUCCESSFUL - Minor issues detected") 
        else:
            print("✗ Data generation ISSUES DETECTED - Review errors above")
        
        print("\nRecommended test queries:")
        print("1. 'Who manages Building B cold storage areas?'")
        print("2. 'Show all network incidents in loading dock areas'")
        print("3. 'What equipment is installed in Building A second floor?'")
        print("4. 'Find contact information for emergency network issues'")


def main():
    """Run validation on generated test data"""
    validator = DataValidator()
    results = validator.validate_all()
    
    # Save detailed results
    output_file = validator.data_dir / "validation_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\nDetailed results saved to: {output_file}")


if __name__ == "__main__":
    main()