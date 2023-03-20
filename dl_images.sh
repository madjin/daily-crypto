#!/bin/bash


IMAGES=(jq -c '.[] | .image' prices.json)

for i in $(cat prices.json | jq -r '.[] | .image'); do
  image=$(echo $i | sed 's/\?.*//')
  wget -nc $image -P images/
done
