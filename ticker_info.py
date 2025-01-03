import bpy
import os
from datetime import datetime

def cleanup_old_data():
    """Remove all existing text objects."""
    for obj in bpy.data.objects:
        if any(suffix in obj.name for suffix in ['_name', '_cap', '_price']):
            bpy.data.objects.remove(obj, do_unlink=True)

    # Clean up orphaned text data
    for text in bpy.data.curves:
        if text.name.startswith('Text.'):
            bpy.data.curves.remove(text)

def clean_name(name):
    """Clean name by removing special characters."""
    name = name.replace(' ', '_')
    cleaned = ''.join(char for char in name if char.isalnum() or char in '_-')
    return cleaned

def create_3d_text(text, location, name_suffix, coin_name):
    """Create 3D text object with given text and location."""
    bpy.ops.object.text_add(location=location)
    text_obj = bpy.context.active_object
    
    # Use coin name as prefix for all objects
    text_obj.name = f"{clean_name(coin_name)}_{name_suffix}"
    text_obj.data.body = text
    
    # Set text properties
    text_obj.data.size = 0.075 * 0.7  # Incorporate scale into size directly
    text_obj.data.extrude = 0.01
    text_obj.data.align_x = 'CENTER'
    text_obj.data.align_y = 'CENTER'
    
    # Apply rotation to face forward
    text_obj.rotation_euler = (1.5708, 0, 3.14159)  # 90 degrees X, 180 degrees Z
    
    # Instead of scaling the object, we scale the text size
    # No need for scale property as it's built into the size
    
    return text_obj


# Get the directory of the blend file
blend_dir = os.path.dirname(bpy.data.filepath)
if not blend_dir:
    blend_dir = os.path.abspath(os.path.curdir)

# Set paths
today = datetime.today().strftime("%m-%d-%Y")
data_file = os.path.join(blend_dir, "data", f"{today}.txt")

# Clean up existing text objects
cleanup_old_data()

# Read and process the data file
try:
    with open(data_file, "r") as f:
        lines = f.readlines()
        
        # Initialize position
        x = 0
        y = 0
        
        # Create text objects
        for line in lines:
            try:
                # Parse the line
                name, values = [part.strip() for part in line.split(":")]
                # Extract market cap and price from the values (between **)
                values = values.strip('*').strip()
                market_cap, price = values.split()
                
                # Calculate text positions (vertically stacked)
                name_pos = (x, y + 0.2, 0.5)    # Name at top
                cap_pos = (x, y + 0.2, 0.45)    # Market cap in middle
                price_pos = (x, y + 0.2, 0.4)   # Price at bottom
                
                # Create text objects
                name_obj = create_3d_text(name, name_pos, 'name', name)
                cap_obj = create_3d_text(market_cap, cap_pos, 'market_cap', name)
                price_obj = create_3d_text(price, price_pos, 'price', name)
                
                # Update position for next set
                x += 1
                if x >= 10:
                    x = 0
                    y -= 1
                    
            except Exception as e:
                print(f"Error processing line: {line.strip()}")
                print(f"Error details: {e}")
                continue

except FileNotFoundError:
    print(f"Error: Data file not found at {data_file}")
    raise
except PermissionError:
    print(f"Error: No permission to read file at {data_file}")
    raise