import bpy
import math
import os
from datetime import datetime, timedelta

# Get the directory of the blend file
blend_dir = os.path.dirname(bpy.data.filepath)
if not blend_dir:
    blend_dir = os.path.abspath(os.path.curdir)

# Function to find the most recent data file
def find_latest_data_file():
    data_dir = os.path.join(blend_dir, "data")
    if not os.path.exists(data_dir):
        raise FileNotFoundError(f"Data directory not found at {data_dir}")
    
    # Try today's date first
    today = datetime.today().strftime("%m-%d-%Y")
    today_file = os.path.join(data_dir, f"{today}.txt")
    
    if os.path.exists(today_file):
        return today_file
    
    # If today's file doesn't exist, find the most recent file
    files = [f for f in os.listdir(data_dir) if f.endswith('.txt')]
    if not files:
        raise FileNotFoundError("No .txt files found in data directory")
    
    # Sort files by modification time
    files.sort(key=lambda x: os.path.getmtime(os.path.join(data_dir, x)), reverse=True)
    return os.path.join(data_dir, files[0])

# Define the dimensions of a US dollar bill in Blender units
BILL_WIDTH = 0.0663
BILL_HEIGHT = 0.156

# Define a function to calculate the size of a cube based on its volume
def get_cube_size(volume):
    # Calculate the cube size based on the desired dimensions of a US dollar bill
    size = math.pow((volume * BILL_WIDTH * BILL_HEIGHT) / (2.61 * 6.14), 1/3)
    return size

# Get the current date
today = datetime.today().strftime("%m-%d-%Y")

# Create a new folder for the GLB files
output_folder = os.path.join(blend_dir, "files", today)
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Find and open the most recent data file
try:
    data_file = find_latest_data_file()
    print(f"Using data file: {data_file}")
    with open(data_file, "r") as f:
        lines = f.readlines()
except Exception as e:
    print(f"Error reading data file: {e}")
    raise

# Loop through the lines and create a cube for each value
for line in lines:
    try:
        # Parse the value from the line
        parts = line.strip().split(":")
        name = parts[0].strip()
        volume = float(parts[1].strip())
        
        # Calculate the size of the cube based on its volume and the desired dimensions of a US dollar bill
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
        
        # Export the cube as a GLB file
        filename = name.replace(" ", "_").replace(".", "").replace(",", "").replace("(", "").replace(")", "") + ".glb"
        filepath = os.path.join(output_folder, filename)
        bpy.ops.export_scene.gltf(
            filepath=filepath,
            export_format='GLB',
            export_apply=True,
            use_selection=True
        )
        
        # Delete the cube
        bpy.ops.object.delete()
        
    except Exception as e:
        print(f"Error processing line: {line.strip()}")
        print(f"Error details: {e}")
        continue