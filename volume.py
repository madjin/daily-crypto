import bpy
import math
import os
from datetime import datetime

# Set the path to the data file
data_file = "/path/to/data.txt"

# Define a function to calculate the size of a cube based on its volume
def get_cube_size(volume):
    size = math.pow(volume, 1/3)
    return size

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

# Define starting positions
x = 0
y = 0

# Loop through the lines and duplicate the dollar bill for each value
for line in lines:
    # Parse the value from the line
    parts = line.strip().split(":")
    name = parts[0].strip()
    value = float(parts[1].strip())
    
    
    # add a 1-meter cube
    bpy.ops.mesh.primitive_cube_add(size=1.0, enter_editmode=False, location=(0, 0, 0))

    # resize the cube to match the dimensions of a dollar bill
    scale_factor_x = 155.956 / 1000.0  # convert mm to meters
    scale_factor_y = 66.294 / 1000.0
    scale_factor_z = 0.109 / 1000.0
    bpy.context.object.scale = (scale_factor_x, scale_factor_y, scale_factor_z)


    # Calculate the volume based on the value
    volume = value / 1000  # Convert value to milliliters

    # Calculate the z translation based on the volume
    z_translation = value * dollar_bill_depth

    # Create a new cube and resize it to the dimensions of the dollar bill
    # (size 0.5 cuz blender spawns at 2^3 meters by default)
    bpy.ops.mesh.primitive_cube_add(size=0.5, enter_editmode=False, location=(x, y, 0))
    cube = bpy.context.active_object
    cube.scale = (dollar_bill_width, dollar_bill_height, z_translation)

    # Rename the cube based on the value
    cube.name = name
    
    # Center the origin to the geometry
    bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")
    
    # Apply transforms
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    

    # Move to the right by 1 meter for the next cube
    x += 1
    
    # If we've reached the end of the row, move down 1 meter and reset x to 0
    if x >= 10:
        x = 0
        y -= 1        
        
    # find the object named "Cube"
    cube_object = bpy.data.objects.get("Cube")

    # delete the object if it exists
    if cube_object:
        bpy.data.objects.remove(cube_object, do_unlink=True)
