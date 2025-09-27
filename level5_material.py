import os
import sys
import argparse
import json
from pathlib import Path
from compression import *
from formats import *

def process_decompress(file_path):
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found")
        return False
    
    file_path = Path(file_path)
    file_extension = file_path.suffix.lower()
    
    # Check file extension
    if file_extension != '.mtr':
        print(f"Error: Unsupported file extension '{file_extension}'. Only .mtr files are supported.")
        return False
    
    # Read file data
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        return False
    
    # Process MTR file
    try:
        parser = MTRParser(data)
        result = parser.parse()
        
        # Generate output filename
        output_file = file_path.with_suffix('.json')
        
        # Write JSON output
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"Successfully decompressed '{file_path.name}' -> '{output_file.name}'")
        return True
        
    except Exception as e:
        print(f"Error processing file: {e}")
        return False

def process_compress(file_path):
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found")
        return False
    
    file_path = Path(file_path)
    file_extension = file_path.suffix.lower()
    
    if file_extension != '.json':
        print(f"Error: Compression only supports .json files")
        return False
    
    # Read JSON data
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
    except Exception as e:
        print(f"Error reading JSON file: {e}")
        return False
    
    # Process JSON to binary
    try:
        # Check if has MTRData key
        if 'MTRData' in json_data:
            serializer = MTRSerializer(json_data)
            binary_data = serializer.serialize()
            output_file = file_path.with_suffix('.mtr')
        else:
            print(f"Error: JSON file does not contain valid MTR structure (missing MTRData key)")
            return False
        
        # Write binary output
        with open(output_file, 'wb') as f:
            f.write(binary_data)
        
        print(f"Successfully compressed '{file_path.name}' -> '{output_file.name}'")
        return True
        
    except Exception as e:
        print(f"Error processing JSON file: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Level5 MTR File Processor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Decompression:
    python level5_material.py -d materials.mtr
  
  Compression:
    python level5_material.py -c materials.json
        """
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    
    group.add_argument(
        '-d', '--decompress',
        metavar='FILE_PATH',
        help='Path to the .mtr file to decompress to JSON'
    )
    
    group.add_argument(
        '-c', '--compress',
        metavar='JSON_PATH',
        help='Path to the .json file to compress to MTR binary'
    )
    
    args = parser.parse_args()
    
    if args.decompress:
        success = process_decompress(args.decompress)
    elif args.compress:
        success = process_compress(args.compress)
    else:
        parser.print_help()
        success = False
    
    sys.exit(0 if success else 1)