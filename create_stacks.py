import bpy
import math
import os
from datetime import datetime

# Set the path to the data file
data_file = "data.txt"

# Define the dimensions of the dollar bill in milimeters
dollar_bill_width = 0.156
dollar_bill_height = 0.0665
dollar_bill_depth = 0.0043

# Get the current date
today = datetime.today().strftime("%m-%d-%Y")

# Create a new folder for the glTF files
output_folder = os.path.join("files/", today)
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Remove the default cube
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

# Open the data file and read the values
with open(data_file, "r") as f:
    lines = f.readlines()


# Loop through the lines and duplicate the dollar bill for each value
for line in lines:
    # Parse the value from the line
    parts = line.strip().split(":")
    name = parts[0].strip()
    value = float(parts[1].strip())

    # Calculate the z translation based on the value
    z_translation = value * dollar_bill_depth

    # Create a new cube and resize it to the dimensions of the dollar bill
    # (size 0.5 cuz blender spawns at 2^3 meters by default)
    bpy.ops.mesh.primitive_cube_add(size=0.5, enter_editmode=False, location=(0, 0, 0))
    cube = bpy.context.active_object
    cube.scale = (dollar_bill_width, dollar_bill_height, z_translation)

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

    # Delete all objects in the scene
    for obj in bpy.context.scene.objects:
        bpy.data.objects.remove(obj)
    
    # Delete all mesh data in the data block
    for mesh in bpy.data.meshes:
        bpy.data.meshes.remove(mesh)

    # Remove the default cube
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
