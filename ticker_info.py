import bpy
import os
from datetime import datetime, timedelta

def create_materials():
    """Create materials for different states."""
    materials = {}
    
    # Positive change material (green)
    green_mat = bpy.data.materials.new(name="Positive_Change")
    green_mat.use_nodes = True
    nodes = green_mat.node_tree.nodes
    nodes.clear()
    
    # Create emission node
    emission = nodes.new('ShaderNodeEmission')
    emission.inputs[0].default_value = (0.0, 1.0, 0.0, 1.0)  # Green
    emission.inputs[1].default_value = 5.0  # Strength
    
    # Create glossy node
    glossy = nodes.new('ShaderNodeBsdfGlossy')
    glossy.inputs[0].default_value = (0.0, 1.0, 0.0, 1.0)  # Green
    glossy.inputs[1].default_value = 0.3  # Roughness
    
    # Create mix shader
    mix = nodes.new('ShaderNodeMixShader')
    mix.inputs[0].default_value = 0.7  # Mix factor
    
    # Create output node
    output = nodes.new('ShaderNodeOutputMaterial')
    
    # Link nodes
    links = green_mat.node_tree.links
    links.new(emission.outputs[0], mix.inputs[1])
    links.new(glossy.outputs[0], mix.inputs[2])
    links.new(mix.outputs[0], output.inputs[0])
    
    materials['positive'] = green_mat
    
    # Negative change material (red)
    red_mat = bpy.data.materials.new(name="Negative_Change")
    red_mat.use_nodes = True
    nodes = red_mat.node_tree.nodes
    nodes.clear()
    
    # Create emission node
    emission = nodes.new('ShaderNodeEmission')
    emission.inputs[0].default_value = (1.0, 0.0, 0.0, 1.0)  # Red
    emission.inputs[1].default_value = 5.0  # Strength
    
    # Create glossy node
    glossy = nodes.new('ShaderNodeBsdfGlossy')
    glossy.inputs[0].default_value = (1.0, 0.0, 0.0, 1.0)  # Red
    glossy.inputs[1].default_value = 0.3  # Roughness
    
    # Create mix shader
    mix = nodes.new('ShaderNodeMixShader')
    mix.inputs[0].default_value = 0.7  # Mix factor
    
    # Create output node
    output = nodes.new('ShaderNodeOutputMaterial')
    
    # Link nodes
    links = red_mat.node_tree.links
    links.new(emission.outputs[0], mix.inputs[1])
    links.new(glossy.outputs[0], mix.inputs[2])
    links.new(mix.outputs[0], output.inputs[0])
    
    materials['negative'] = red_mat
    
    # Name material (bright blue)
    name_mat = bpy.data.materials.new(name="Name_Material")
    name_mat.use_nodes = True
    nodes = name_mat.node_tree.nodes
    nodes.clear()
    
    # Create emission node
    emission = nodes.new('ShaderNodeEmission')
    emission.inputs[0].default_value = (0.3, 0.7, 1.0, 1.0)  # Light blue
    emission.inputs[1].default_value = 3.0  # Strength
    
    # Create glossy node
    glossy = nodes.new('ShaderNodeBsdfGlossy')
    glossy.inputs[0].default_value = (0.3, 0.7, 1.0, 1.0)  # Light blue
    glossy.inputs[1].default_value = 0.2  # Roughness
    
    # Create mix shader
    mix = nodes.new('ShaderNodeMixShader')
    mix.inputs[0].default_value = 0.6  # Mix factor
    
    # Create output node
    output = nodes.new('ShaderNodeOutputMaterial')
    
    # Link nodes
    links = name_mat.node_tree.links
    links.new(emission.outputs[0], mix.inputs[1])
    links.new(glossy.outputs[0], mix.inputs[2])
    links.new(mix.outputs[0], output.inputs[0])
    
    materials['name'] = name_mat
    
    return materials

def cleanup_old_data():
    """Remove all existing text objects and materials."""
    # Remove objects
    for obj in bpy.data.objects:
        if any(suffix in obj.name for suffix in ['_name', '_cap', '_price']):
            bpy.data.objects.remove(obj, do_unlink=True)

    # Clean up materials
    for mat in bpy.data.materials:
        if mat.name in ["Positive_Change", "Negative_Change", "Name_Material"]:
            bpy.data.materials.remove(mat)

    # Clean up orphaned text data
    for text in bpy.data.curves:
        if text.name.startswith('Text.'):
            bpy.data.curves.remove(text)

def clean_name(name):
    """Clean name by removing special characters."""
    name = name.replace(' ', '_')
    cleaned = ''.join(char for char in name if char.isalnum() or char in '_-')
    return cleaned

def create_3d_text(text, location, name_suffix, coin_name, material):
    """Create 3D text object with given text and location."""
    bpy.ops.object.text_add(location=location)
    text_obj = bpy.context.active_object
    
    # Use coin name as prefix for all objects
    text_obj.name = f"{clean_name(coin_name)}_{name_suffix}"
    text_obj.data.body = text
    
    # Set text properties
    text_obj.data.size = 0.075 * 0.7
    text_obj.data.extrude = 0.01
    text_obj.data.align_x = 'CENTER'
    text_obj.data.align_y = 'CENTER'
    
    # Apply rotation to face forward
    text_obj.rotation_euler = (1.5708, 0, 3.14159)
    
    # Apply material
    text_obj.data.materials.clear()
    text_obj.data.materials.append(material)
    
    return text_obj

def get_yesterday_data():
    """Read yesterday's data file and return a dictionary of values."""
    yesterday = (datetime.today() - timedelta(days=1)).strftime("%m-%d-%Y")
    yesterday_file = os.path.join(blend_dir, "data", f"{yesterday}.txt")
    
    data = {}
    try:
        with open(yesterday_file, "r") as f:
            for line in f:
                try:
                    name, values = [part.strip() for part in line.split(":")]
                    values = values.strip('*').strip()
                    market_cap, price = values.split()
                    # Remove commas and convert to float for comparison
                    market_cap = float(market_cap.replace(',', ''))
                    price = float(price)
                    data[clean_name(name)] = {'market_cap': market_cap, 'price': price}
                except:
                    continue
    except FileNotFoundError:
        print(f"Yesterday's file not found: {yesterday_file}")
    
    return data

# Get the directory of the blend file
blend_dir = os.path.dirname(bpy.data.filepath)
if not blend_dir:
    blend_dir = os.path.abspath(os.path.curdir)

# Set paths
today = datetime.today().strftime("%m-%d-%Y")
data_file = os.path.join(blend_dir, "data", f"{today}.txt")

# Clean up existing objects and create materials
cleanup_old_data()
materials = create_materials()

# Get yesterday's data for comparison
yesterday_data = get_yesterday_data()

# Read and process today's data file
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
                values = values.strip('*').strip()
                market_cap, price = values.split()
                
                # Clean numeric values for comparison
                clean_market_cap = float(market_cap.replace(',', ''))
                clean_price = float(price)
                
                # Get yesterday's values
                yesterday_values = yesterday_data.get(clean_name(name))
                
                # Determine materials based on comparison
                price_material = materials['positive']
                cap_material = materials['positive']
                
                if yesterday_values:
                    if clean_price < yesterday_values['price']:
                        price_material = materials['negative']
                    if clean_market_cap < yesterday_values['market_cap']:
                        cap_material = materials['negative']
                
                # Calculate text positions
                name_pos = (x, y + 0.2, 0.5)
                cap_pos = (x, y + 0.2, 0.45)
                price_pos = (x, y + 0.2, 0.4)
                
                # Create text objects with materials
                name_obj = create_3d_text(name, name_pos, 'name', name, materials['name'])
                cap_obj = create_3d_text(market_cap, cap_pos, 'market_cap', name, cap_material)
                price_obj = create_3d_text(price, price_pos, 'price', name, price_material)
                
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