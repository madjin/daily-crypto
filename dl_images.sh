#!/bin/bash

# Create images directory if it doesn't exist
mkdir -p images

# Extract coin names and image URLs together
jq -r '.[] | "\(.name)|\(.image)"' prices.json | while IFS='|' read -r name image; do
    # Clean the name (remove spaces and special characters)
    clean_name=$(echo "$name" | tr ' ' '_' | tr -cd '[:alnum:]_-')
    
    # Get clean file extension (typically .png)
    extension=".png"
    
    # Download image with clean filename
    wget -q "$image" -O "images/${clean_name}${extension}"
done

echo "All images have been downloaded and renamed"