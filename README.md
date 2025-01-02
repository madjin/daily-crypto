# daily-crypto
[![Fetch Prices](https://github.com/madjin/daily-crypto/actions/workflows/main.yml/badge.svg)](https://github.com/madjin/daily-crypto/actions/workflows/main.yml)

Daily crypto market information data visualization art experiments using Blender and Python. This project fetches cryptocurrency data and creates visual representations using 3D models and textures.

## Core Components

### Data Collection Scripts

#### fetch_prices.sh
Fetches current prices of the top 100 cryptocurrencies from the Coingecko API and saves them to a daily file in the data directory. The data is accessible at: https://madjin.github.io/daily-crypto/data.txt

- Fetches data from Coingecko API
- Saves prices in format: `CryptoName: Price`
- Creates daily files with date format MM-DD-YYYY
- Includes debug output for verification

#### marketcap.sh
Similar to fetch_prices.sh but focuses on market capitalization data:
- Fetches market cap data for top 100 cryptocurrencies
- Saves data in format: `CryptoName: MarketCap`
- Creates daily files with market cap information

#### dl_images.sh
Downloads and processes cryptocurrency icons:
- Creates an images directory if it doesn't exist
- Downloads icons for each cryptocurrency from Coingecko
- Cleans filenames and saves as PNG format


![Screenshot at 2023-03-15 15-40-33](https://user-images.githubusercontent.com/32600939/225433892-1770d224-28d6-4a8b-bd5e-6ebc27317afe.png)

```bash
#!/bin/bash

# Set the API endpoint URL
API_URL="https://api.coingecko.com/api/v3/coins/markets"

# Set the parameters for the API request
PARAMS="?vs_currency=usd&order=market_cap_desc&per_page=100&page=1&sparkline=false"

# Make the API request and save the response to a file
curl -s -o prices.json "${API_URL}${PARAMS}"

# Parse the JSON response and extract the price for each cryptocurrency
for row in $(cat prices.json | jq -r '.[] | @base64'); do
    _jq() {
     echo ${row} | base64 --decode | jq -r ${1}
    }
    name=$(_jq '.name')
    price=$(_jq '.current_price')
    echo "${name}: ${price}"
done
```

Make it executable with the command chmod +x `fetch_prices.sh`. Then, you can add it as a daily cronjob by running the command `crontab -e` and adding the following line:

`0 0 * * * /path/to/fetch_prices.sh`

This will run the script at midnight every day and output the current prices in USD of the top 100 cryptocurrencies to the console.

---
### Visualization Scripts

#### volume.py
Creates 3D representations of cryptocurrency data in Blender:
- Reads daily cryptocurrency data
- Creates cubes with dimensions based on USD value
- Uses dollar bill dimensions as a scale reference
- Organizes cubes in a 10x10 grid layout
- Automatically handles file paths and directory creation

#### ticker.py
Creates 3D signs with cryptocurrency icons:
- Generates a cube for each cryptocurrency
- Applies downloaded cryptocurrency icons as textures
- Organizes signs in a grid layout
- Handles UV mapping for proper texture display

#### atlasgenerator.py
Manages texture creation and mapping:
- Creates a texture atlas from cryptocurrency icons
- Organizes images in a 10x10 grid
- Generates UV mappings for 3D objects
- Creates and applies Blender materials

## Requirements
- Python 3.x
- PIL (Python Imaging Library)
- Blender
- jq (for JSON processing)
- curl (for API requests)
## Create Cubes

![Screenshot at 2023-03-15 15-54-57](https://user-images.githubusercontent.com/32600939/225433937-1b167902-9b44-438a-9501-6bc48fc00b41.png)

Blender Python script that

- reads the values from column 2 (separated by :) in data.txt
- creates and resizes a cube in terms of volume based on that value
- centers the origin to each geometry, applies transforms
- exports a glTF of each cube as a separate file
- renames filename same as the node
- saves the files into new timestamped folder based on MM-DD-YYYY

![Screenshot at 2023-03-15 16-13-14](https://user-images.githubusercontent.com/32600939/225433977-a5c93666-4d1c-4c62-8608-7bb559010f11.png)


```python
import bpy
import math
import os
from datetime import datetime

# Set the path to the data file
data_file = "/path/to/data.txt"

# Define a function to calculate the size of a cube based on its volume
def get_cube_size(volume):
    size = math.pow(volume, 1/3)
    return size

# Get the current date
today = datetime.today().strftime("%m-%d-%Y")

# Create a new folder for the glTF files
output_folder = os.path.join("/path/to/output/folder", today)
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Open the data file and read the values
with open(data_file, "r") as f:
    lines = f.readlines()

# Loop through the lines and create a cube for each value
for line in lines:
    # Parse the value from the line
    parts = line.strip().split(":")
    name = parts[0].strip()
    volume = float(parts[1].strip())
    
    # Calculate the size of the cube based on its volume
    size = get_cube_size(volume)
    
    # Create a new cube
    bpy.ops.mesh.primitive_cube_add(size=size, enter_editmode=False, location=(0, 0, 0))
    cube = bpy.context.active_object
    
    # Rename the cube based on the value
    cube.name = name
    
    # Center the origin to the geometry
    bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")
    
    # Apply transforms
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    
    # Export the cube as a glTF file
    filename = name.replace(" ", "_").replace(".", "").replace(",", "").replace("(", "").replace(")", "") + ".gltf"
    filepath = os.path.join(output_folder, filename)
    bpy.ops.export_scene.gltf(filepath=filepath, export_format="GLTF_SEPARATE", export_apply=True)
    
    # Delete the cube
    bpy.ops.object.delete()
```

---

## Ideas

Create a daily "blockchain"?

![Screenshot at 2023-03-15 16-04-57](https://user-images.githubusercontent.com/32600939/225434181-76f8d8a7-6c69-45b9-b88c-575643d6e309.png)

Separate each cube by distance, use `gltf-transform` to merge into 1 file?

Texture each cube the icon of the coin / create a huge texture atlas for top 100 coins
