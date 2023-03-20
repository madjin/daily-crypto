import bpy
import math
import os
from datetime import datetime

# Set the path to the data file
data_file = "data.txt"

# Define a function to calculate the size of a cube based on its volume
def get_cube_size(volume):
    size = math.pow(volume, 1/3)
    return size

# Get the current date
today = datetime.today().strftime("%m-%d-%Y")

# Create a new folder for the glTF files
output_folder = os.path.join("files/", today)
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
