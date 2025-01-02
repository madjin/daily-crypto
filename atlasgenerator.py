import bpy
import os
from datetime import datetime
from PIL import Image
import numpy as np

class TextureAtlasGenerator:
    def __init__(self, image_dir, data_dir):
        self.image_dir = image_dir
        self.data_dir = data_dir
        self.atlas_size = (10, 10)  # 10x10 grid for 100 images
        self.image_order = []
        self.tile_size = None
        
    def get_current_order_file(self):
        """Get today's order file from the data directory."""
        today = datetime.now().strftime("%m-%d-%Y")
        order_file = os.path.join(self.data_dir, f"{today}.txt")
        
        if not os.path.exists(order_file):
            raise FileNotFoundError(f"Order file for today ({order_file}) not found!")
        
        return order_file
    
    def read_image_order(self):
        """Read the image order from today's file."""
        with open(self.get_current_order_file(), 'r') as f:
            self.image_order = [line.strip() for line in f.readlines()]
            
        if len(self.image_order) != 100:
            raise ValueError(f"Expected 100 image names in order file, got {len(self.image_order)}")
    
    def create_atlas(self):
        """Create the texture atlas from the ordered images."""
        # Get the size of the first image to determine tile size
        first_image = Image.open(os.path.join(self.image_dir, self.image_order[0]))
        self.tile_size = first_image.size
        
        # Create the atlas with appropriate size
        atlas_width = self.tile_size[0] * self.atlas_size[0]
        atlas_height = self.tile_size[1] * self.atlas_size[1]
        atlas = Image.new('RGBA', (atlas_width, atlas_height))
        
        # Place each image in the atlas
        for idx, image_name in enumerate(self.image_order):
            row = idx // self.atlas_size[0]
            col = idx % self.atlas_size[0]
            
            image_path = os.path.join(self.image_dir, image_name)
            img = Image.open(image_path)
            
            # Ensure consistent size
            if img.size != self.tile_size:
                img = img.resize(self.tile_size)
            
            x = col * self.tile_size[0]
            y = row * self.tile_size[1]
            atlas.paste(img, (x, y))
        
        # Save the atlas
        atlas_path = os.path.join(self.image_dir, "texture_atlas.png")
        atlas.save(atlas_path)
        return atlas_path

    def create_blender_material(self, atlas_path):
        """Create a Blender material using the texture atlas."""
        # Create new material
        mat = bpy.data.materials.new(name="AtlasMaterial")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        
        # Clear default nodes
        nodes.clear()
        
        # Create necessary nodes
        tex_coord = nodes.new('ShaderNodeTexCoord')
        mapping = nodes.new('ShaderNodeMapping')
        tex_image = nodes.new('ShaderNodeTexImage')
        principled = nodes.new('ShaderNodeBsdfPrincipled')
        output = nodes.new('ShaderNodeOutputMaterial')
        
        # Load and assign the atlas texture
        tex_image.image = bpy.data.images.load(atlas_path)
        
        # Connect nodes
        links = mat.node_tree.links
        links.new(tex_coord.outputs['UV'], mapping.inputs['Vector'])
        links.new(mapping.outputs['Vector'], tex_image.inputs['Vector'])
        links.new(tex_image.outputs['Color'], principled.inputs['Base Color'])
        links.new(principled.outputs['BSDF'], output.inputs['Surface'])
        
        return mat

    def apply_materials_to_objects(self, material):
        """Apply materials to objects with proper UV mapping for each section."""
        for idx, _ in enumerate(self.image_order):
            # Get the object (assuming names are in order obj_0, obj_1, etc.)
            obj_name = f"obj_{idx}"
            if obj_name not in bpy.data.objects:
                continue
                
            obj = bpy.data.objects[obj_name]
            
            # Assign material
            if obj.data.materials:
                obj.data.materials[0] = material
            else:
                obj.data.materials.append(material)
            
            # Calculate UV coordinates for this section of the atlas
            row = idx // self.atlas_size[0]
            col = idx % self.atlas_size[0]
            
            u_start = col / self.atlas_size[0]
            u_end = (col + 1) / self.atlas_size[0]
            v_start = 1 - (row + 1) / self.atlas_size[1]  # Flip V coordinate
            v_end = 1 - row / self.atlas_size[1]
            
            # Create new UV layer if needed
            if not obj.data.uv_layers:
                obj.data.uv_layers.new()
            
            # Set UV coordinates for front and back faces (assuming cube)
            for face_idx, face in enumerate(obj.data.polygons):
                if face_idx in [0, 5]:  # Assuming these are the front/back faces
                    for loop_idx in face.loop_indices:
                        uv = obj.data.uv_layers.active.data[loop_idx]
                        vert_idx = face.vertices[face.loop_indices.index(loop_idx)]
                        
                        # Map vertices to UV coordinates
                        if face_idx == 0:  # Front face
                            if vert_idx % 4 in [0, 1]:
                                uv.uv.x = u_start
                            else:
                                uv.uv.x = u_end
                            if vert_idx % 4 in [0, 3]:
                                uv.uv.y = v_start
                            else:
                                uv.uv.y = v_end
                        else:  # Back face (mirrored)
                            if vert_idx % 4 in [0, 1]:
                                uv.uv.x = u_end
                            else:
                                uv.uv.x = u_start
                            if vert_idx % 4 in [0, 3]:
                                uv.uv.y = v_start
                            else:
                                uv.uv.y = v_end

def main():
    # Initialize the generator
    generator = TextureAtlasGenerator(
        image_dir="/images",
        data_dir="/data"
    )
    
    # Generate the atlas
    generator.read_image_order()
    atlas_path = generator.create_atlas()
    
    # Create and apply materials
    material = generator.create_blender_material(atlas_path)
    generator.apply_materials_to_objects(material)

if __name__ == "__main__":
    main()