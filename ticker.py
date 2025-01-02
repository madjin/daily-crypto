import bpy
import os
from datetime import datetime

# Get the directory of the blend file
blend_dir = os.path.dirname(bpy.data.filepath)
if not blend_dir:
    blend_dir = os.path.abspath(os.path.curdir)

# Set paths
today = datetime.today().strftime("%m-%d-%Y")
data_file = os.path.join(blend_dir, "data", f"{today}.txt")
image_dir = os.path.join(blend_dir, "image")

def create_material_from_image(image_path, name):
    """Create a new material with the given image as texture"""
    # Create new material
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    
    # Get the node tree
    nodes = mat.node_tree.nodes
    bsdf = nodes["Principled BSDF"]
    
    # Create texture node
    tex = nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(image_path)
    
    # Link texture to base color
    mat.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    
    return mat

# Remove existing signs first
for obj in bpy.data.objects:
    if obj.name.endswith('_sign'):
        bpy.data.objects.remove(obj, do_unlink=True)

# Read and process the data file
try:
    with open(data_file, "r") as f:
        # Read all lines and sort by value
        lines = []
        for line in f:
            name, value = [part.strip() for part in line.split(":")]
            lines.append((name, float(value)))
        
        # Sort lines by value
        lines.sort(key=lambda x: x[1])
        
        # Initialize position
        x = 0
        y = 0
        
        # Create signs
        for name, value in lines:
            # Create base cube for sign
            bpy.ops.mesh.primitive_cube_add(
                size=0.5,
                enter_editmode=False,
                location=(x, y, 0)
            )
            
            # Get the sign and set its properties
            sign = bpy.context.active_object
            sign.name = f"{name}_sign"
            
            # Set dimensions (height same as width, depth 1/4 of width)
            sign.scale = (0.5, 0.125, 0.5)
            
            # Load and apply texture
            image_path = os.path.join(image_dir, f"{name}.png")
            if os.path.exists(image_path):
                # Create and assign material
                material = create_material_from_image(image_path, name)
                
                # Clear existing materials and add new one
                sign.data.materials.clear()
                sign.data.materials.append(material)
                
                # UV unwrapping
                bpy.context.view_layer.objects.active = sign
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.uv.smart_project()
                bpy.ops.object.mode_set(mode='OBJECT')
            
            # Update position for next sign
            x += 1
            if x >= 10:
                x = 0
                y -= 1

except FileNotFoundError:
    print(f"Error: Data file not found at {data_file}")
    raise
except PermissionError:
    print(f"Error: No permission to read file at {data_file}")
    raise