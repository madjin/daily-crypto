#!/bin/bash


wget https://anata.dev/blender.tar.xz
tar xvf blender.tar.xz --strip 1 -C blender
./blender/blender -b -P create_cubes.py
echo "Cleaning up files"
rm blender.tar.xz
find ./blender -type f ! -name "README.md" -delete && find ./blender -mindepth 1 -type d ! -name "README.md" -exec rm -r {} +
