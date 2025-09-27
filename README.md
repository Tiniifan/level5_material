# level5_material

A Python tool to convert .mtr to .json and back.

### Command Line Interface

The tool uses a simple command-line interface with two main operations:

```bash
# Display help
python level5_material.py -h

# Decompress MTR to JSON
python level5_material.py -d <mtr_file>

# Compress JSON to MTR
python level5_material.py -c <json_file>
```

### Examples

**Decompressing an MTR file:**
```bash
python level5_material.py -d 000.mtr
```
This will create `000.json` in the same directory.

**Compressing a JSON file:**
```bash
python level5_material.py -c 000.json
```
This will create `000.mtr` in the same directory.
