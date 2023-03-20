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
