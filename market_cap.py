import bpy
import math
import os
from datetime import datetime

# Get the directory of the blend file
blend_dir = os.path.dirname(bpy.data.filepath)
if not blend_dir:
    blend_dir = os.path.abspath(os.path.curdir)

# Set the path to the data file relative to the blend file directory
today = datetime.today().strftime("%m-%d-%Y")
data_file = os.path.join(blend_dir, "data", f"{today}.txt")

# Define a function to calculate the size of a cube based on its volume
def get_cube_size(volume):
    return math.pow(volume, 1/3)

# Define the dimensions of the dollar bill in meters
dollar_bill_width = 0.156
dollar_bill_height = 0.0665
dollar_bill_depth = 0.0043

# Define logarithmic scaling function
def scale_market_cap(value):
    # Add 1 to handle values less than 1
    log_value = math.log10(value + 3)
    
    # Scale factor can be adjusted to make visualization taller/shorter
    scale_factor = 0.1
    
    return log_value * scale_factor

# Create output folder
output_folder = os.path.join(blend_dir, "files", today)
try:
    os.makedirs(output_folder, exist_ok=True)
except PermissionError:
    print(f"Error: No permission to create directory at {output_folder}")
    raise

# Remove all objects in the scene
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

# Read and process the data file
try:
    with open(data_file, "r") as f:
        lines = f.readlines()
except FileNotFoundError:
    print(f"Error: Data file not found at {data_file}")
    raise
except PermissionError:
    print(f"Error: No permission to read file at {data_file}")
    raise

# Define starting positions
x = 0
y = 0

# Loop through the lines and create cubes
for line in lines:
    try:
        # Parse the value from the line
        name, value = [part.strip() for part in line.split(":")]
        value = float(value)
        
        # Apply logarithmic scaling to the value
        scaled_value = scale_market_cap(value)
        
        # Calculate the z translation based on the scaled value
        z_translation = scaled_value * dollar_bill_depth * 1000  # Multiply by 1000 to make it more visible
        
        # Create a new cube
        bpy.ops.mesh.primitive_cube_add(
            size=0.5, 
            enter_editmode=False, 
            location=(x, y, z_translation/2)  # Divide by 2 to place bottom at ground level
        )
        
        # Get the active cube and set its properties
        cube = bpy.context.active_object
        cube.scale = (dollar_bill_width, dollar_bill_height, z_translation)
        cube.name = name
        
        # Center origin and apply transforms
        bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        
        # Update position for next cube
        x += 1
        if x >= 10:
            x = 0
            y -= 1
            
    except ValueError as e:
        print(f"Error processing line: {line.strip()}")
        print(f"Error details: {e}")
        continue

# Remove any remaining default cube
if "Cube" in bpy.data.objects:
    bpy.data.objects.remove(bpy.data.objects["Cube"], do_unlink=True)