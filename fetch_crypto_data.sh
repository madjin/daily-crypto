#!/bin/bash

# Set the API endpoint URL
API_URL="https://api.coingecko.com/api/v3/coins/markets"

# Set the parameters for the API request
PARAMS="?vs_currency=usd&order=market_cap_desc&per_page=100&page=1&sparkline=false"

# Get today's date in the required format
TODAY=$(date +"%m-%d-%Y")

# Create data directory if it doesn't exist
mkdir -p data

# Set output file path
OUTPUT_FILE="data/${TODAY}.txt"

# Make the API request and save the response to a file
curl -s -o crypto_data.json "${API_URL}${PARAMS}"

# Debug: Print the first item's structure
echo "First item structure:"
cat crypto_data.json | jq '.[0]'

# Clear the output file if it exists
> "$OUTPUT_FILE"

# Parse the JSON response and extract both market cap and price for each cryptocurrency
for row in $(cat crypto_data.json | jq -r '.[] | @base64'); do
    _jq() {
     echo ${row} | base64 --decode | jq -r ${1}
    }
    name=$(_jq '.name')
    market_cap=$(_jq '.market_cap')
    price=$(_jq '.current_price')
    
    # Format numbers using awk for better compatibility
    formatted_cap=$(echo $market_cap | awk '{ len=length($0); res=""; for (i=0;i<len;i++) { if (i > 0 && (len-i) % 3 == 0) res = res ","; res = res substr($0,i+1,1) } print res }')
    formatted_price=$(echo $price | awk '{printf "%.2f", $1}')
    
    # Debug: Print to console what we're writing
    echo "Writing to file: ${name}: ${formatted_cap} ${formatted_price}"
    
    # Write to file with the requested format
    echo "${name}: ${formatted_cap} ${formatted_price}**" >> "$OUTPUT_FILE"
done

# Debug: Show the first few lines of the output file
echo "First few lines of output file:"
head -n 5 "$OUTPUT_FILE"

echo "Data has been written to $OUTPUT_FILE"