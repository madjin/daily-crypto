#!/bin/bash

# Make sure dependencies are installed
packages=("blender")

for package in "${packages[@]}"; do
    if ! dpkg-query -W --showformat='${Status}\n' "$package" | grep -q "install ok installed"; then
        echo "Package '$package' is not installed, installing now..."
        sudo apt-get update && sudo apt-get install -y "$package"
    else
        echo "Package '$package' is already installed."
    fi
done

blender -b -P create_cubes.py
