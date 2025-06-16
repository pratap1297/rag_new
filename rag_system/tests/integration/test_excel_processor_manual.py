import sys
import os
import json
import numpy as np
from pathlib import Path
from reportlab.graphics.shapes import Drawing, Circle, Line, Rect, String

# Adjust import path if running manually
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src' / 'ingestion' / 'processors'))

from excel_processor import create_excel_processor

class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder for NumPy types"""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)

# ====== MANUAL TEST FOR EXCEL PROCESSOR ======
# WARNING: This processor only works with Excel files (.xlsx, .xls, .xlsm, .xlsb)
# PDF files are not supported. Please provide a path to an Excel file.
SAMPLE_EXCEL_PATH = r'D:\Projects-D\pepsi-final2\document_generator\test_data\Facility_Managers_2024.xlsx'  # <-- CHANGE THIS to an Excel file path

def main():
    if not os.path.exists(SAMPLE_EXCEL_PATH):
        print(f"Sample Excel file not found: {SAMPLE_EXCEL_PATH}")
        print("Please update SAMPLE_EXCEL_PATH in this script.")
        return

    try:
        processor = create_excel_processor()
        print(f"Processing: {SAMPLE_EXCEL_PATH}")
        result = processor.process(SAMPLE_EXCEL_PATH)

        print("\n=== Processing Result ===")
        if result.get('status') == 'success':
            # Convert result to JSON-serializable format
            result_json = json.loads(json.dumps(result, cls=NumpyEncoder))
            
            print(f"File: {result_json['file_name']}")
            print(f"Sheets: {[s['name'] for s in result_json['sheets']]}")
            print(f"Embedded Objects: {len(result_json['embedded_objects'])}")
            print(f"Images: {len(result_json['images'])}")
            print(f"Charts: {len(result_json['charts'])}")
            print(f"Chunks: {len(result_json['chunks'])}")
            print("\nSample Chunk:")
            if result_json['chunks']:
                print(result_json['chunks'][0]['text'][:500])
        else:
            print(f"Error: {result.get('error')}")
    except Exception as e:
        print(f"Error during processing: {str(e)}")
        import traceback
        print("\nDetailed error:")
        print(traceback.format_exc())

if __name__ == '__main__':
    main() 