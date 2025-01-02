import bpy
import os
from datetime import datetime

def cleanup_old_data():
    """Remove all existing signs and their materials."""
    # Remove existing signs
    for obj in bpy.data.objects:
        if obj.name.endswith('_sign'):
            # Remove materials associated with this object
            for material_slot in obj.material_slots:
                if material_slot.material:
                    bpy.data.materials.remove(material_slot.material)
            # Remove the object
            bpy.data.objects.remove(obj, do_unlink=True)

    # Clean up any orphaned materials with '_sign' in their name
    for material in bpy.data.materials:
        if '_sign' in material.name:
            bpy.data.materials.remove(material)

def clean_name(name):
    """Clean name by removing special characters."""
    name = name.replace(' ', '_')
    cleaned = ''.join(char for char in name if char.isalnum() or char in '_-')
    return cleaned

# Get the directory of the blend file
blend_dir = os.path.dirname(bpy.data.filepath)
if not blend_dir:
    blend_dir = os.path.abspath(os.path.curdir)

# Set paths
today = datetime.today().strftime("%m-%d-%Y")
data_file = os.path.join(blend_dir, "data", f"{today}.txt")

# Clean up existing signs and materials
cleanup_old_data()

# Read and process the data file
try:
    with open(data_file, "r") as f:
        lines = f.readlines()
        
        # Initialize position
        x = 0
        y = 0
        
        # Create signs
        for line in lines:
            try:
                # Parse the value from the line
                name, value = [part.strip() for part in line.split(":")]
                name = clean_name(name)
                value = float(value)
                
                # Create base cube for sign
                # Add 0.2 to y and z coordinates for offset
                bpy.ops.mesh.primitive_cube_add(
                    size=0.5,
                    enter_editmode=False,
                    location=(x, y + 0.2, 0.2)  # Added offsets here
                )
                
                # Get the sign and set its properties
                sign = bpy.context.active_object
                sign.name = f"{name}_sign"
                
                # Set dimensions (height same as width, depth 1/4 of width)
                sign.scale = (0.5, 0.125, 0.5)
                
                # Center origin and apply transforms
                bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")
                bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
                
                # Update position for next sign
                x += 1
                if x >= 10:
                    x = 0
                    y -= 1
                    
            except ValueError as e:
                print(f"Error processing line: {line.strip()}")
                print(f"Error details: {e}")
                continue

except FileNotFoundError:
    print(f"Error: Data file not found at {data_file}")
    raise
except PermissionError:
    print(f"Error: No permission to read file at {data_file}")
    raise