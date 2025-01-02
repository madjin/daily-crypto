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

![Screenshot at 2023-03-15 15-40-33](https://user-images.githubusercontent.com/32600939/225433892-1770d224-28d6-4a8b-bd5e-6ebc27317afe.png)

Make it executable with the command chmod +x `fetch_prices.sh`. Then, you can add it as a daily cronjob by running the command `crontab -e` and adding the following line:

`0 0 * * * /path/to/fetch_prices.sh`

This will run the script at midnight every day and output the current prices in USD of the top 100 cryptocurrencies to the console.

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

---

## Ideas/To Do

- make it look cooler
- unify scripts
- display name, price, market-cap (likely create this as extruded 3d objects so it's not just some boring flat image applied to a cube)
- export all in a single object (?) - this is mostly where I had questions, what was the end deployment (like is it going to be walkable in 3d, or are they still just looking at it on a flat screen)
- fix ticker and stack distribution
- add gitignore
- rename texture atlas to correlate with date

Create a daily "blockchain"?

![Screenshot at 2023-03-15 16-04-57](https://user-images.githubusercontent.com/32600939/225434181-76f8d8a7-6c69-45b9-b88c-575643d6e309.png)

Separate each cube by distance, use `gltf-transform` to merge into 1 file?