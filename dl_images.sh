#!/bin/bash

# Get today's date in the same format as the data file
today=$(date +"%m-%d-%Y")

# Create images directory and subdirectory for today if they don't exist
mkdir -p "images/$today"

# Extract coin names and image URLs together
jq -r '.[] | "\(.name)|\(.image)"' crypto_data.json | while IFS='|' read -r name image; do
    # Clean the name (remove spaces and special characters)
    clean_name=$(echo "$name" | tr ' ' '_' | tr -cd '[:alnum:]_-')
    
    # Get clean file extension (typically .png)
    extension=".png"
    
    # Download image with clean filename into today's subdirectory
    wget -q "$image" -O "images/$today/${clean_name}${extension}"
done

echo "All images have been downloaded and renamed into the folder: images/$today"