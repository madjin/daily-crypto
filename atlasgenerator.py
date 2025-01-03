import bpy
import os
from datetime import datetime
import numpy as np

try:
    from PIL import Image, ImageFilter, ImageOps, ImageEnhance
    USE_PIL = True
except ImportError:
    USE_PIL = False
    print("PIL not found. To speed up atlas creation, install PIL: pip install Pillow")


class TextureAtlasGenerator:
    def __init__(self):
        self.blend_dir = os.path.dirname(bpy.data.filepath)
        if not self.blend_dir:
            raise RuntimeError("Blend file must be saved before running this script")

        self.data_dir = os.path.join(self.blend_dir, "data")
        self.base_image_dir = os.path.join(self.blend_dir, "images")
        self.today = datetime.today().strftime("%m-%d-%Y")
        self.image_dir = os.path.join(self.base_image_dir, self.today)

        if not os.path.exists(self.data_dir):
            raise FileNotFoundError(f"Data directory not found at {self.data_dir}")
        if not os.path.exists(self.image_dir):
            raise FileNotFoundError(f"Image directory not found at {self.image_dir}")

        self.atlas_size = (10, 10)  # 10x10 grid for 100 images
        self.image_order = []

    def clean_name(self, name):
        """Clean name following the same rules as the bash download script."""
        name = name.replace(" ", "_")
        cleaned = "".join(char for char in name if char.isalnum() or char in "_-")
        return cleaned

    def get_current_order_file(self):
        """Get today's order file from the data directory."""
        order_file = os.path.join(self.data_dir, f"{self.today}.txt")

        if not os.path.exists(order_file):
            raise FileNotFoundError(f"Order file for today ({order_file}) not found!")

        return order_file

    def read_image_order(self):
        """Read and process the image order from today's file."""
        with open(self.get_current_order_file(), "r") as f:
            self.image_order = []
            for line in f.readlines():
                if ":" in line:
                    # Parse the name and values from the line
                    name = line.split(":")[0].strip()
                    name = self.clean_name(name)
                    self.image_order.append(name)
                else:
                    name = line.strip()
                    if name:
                        name = self.clean_name(name)
                        self.image_order.append(name)

        if not self.image_order:
            raise ValueError("No valid names found in order file")

        print("First few processed names:")
        for name in self.image_order[:5]:
            print(f"  {name}_sign")

    def cleanup_texture_atlas(self):
        """Remove all existing texture atlas images and related materials from Blender."""
        # Define all possible atlas types to clean
        atlas_types = ['color', 'normal', 'emission', 'roughness', 'depth']
        
        # First pass: remove images with exact names
        for atlas_type in atlas_types:
            image_name = f"texture_atlas_{atlas_type}.png"
            if image_name in bpy.data.images:
                image = bpy.data.images[image_name]
                print(f"Removing atlas image: {image.name}")
                bpy.data.images.remove(image)
        
        # Second pass: remove any images that start with texture_atlas
        # This catches variations like texture_atlas_color.001, etc.
        for image in list(bpy.data.images):  # Create a list to avoid modification during iteration
            if image.name.startswith("texture_atlas"):
                print(f"Removing additional atlas image: {image.name}")
                bpy.data.images.remove(image)
        
        # Clean up materials
        for material in list(bpy.data.materials):  # Create a list to avoid modification during iteration
            if material.name.endswith('_sign'):
                print(f"Removing material: {material.name}")
                bpy.data.materials.remove(material)
        
        # Force Blender to remove unused data
        bpy.ops.outliner.orphans_purge(do_recursive=True)

    def create_texture_atlas_pil(self):
        """Create texture atlas using PIL (faster method)."""
        print("\nCreating texture atlases using PIL...")
        atlas_size = 4096
        tile_size = atlas_size // self.atlas_size[0]
        print(f"Atlas dimensions: {atlas_size}x{atlas_size} pixels")
        print(f"Individual tile size: {tile_size}x{tile_size} pixels")

        # Create new atlas images for each type
        atlases = {
            'color': Image.new("RGBA", (atlas_size, atlas_size), (0, 0, 0, 0)),
            'normal': Image.new("RGBA", (atlas_size, atlas_size), (128, 128, 255, 255)),
            'emission': Image.new("RGBA", (atlas_size, atlas_size), (0, 0, 0, 0)),
            'roughness': Image.new("RGBA", (atlas_size, atlas_size), (0, 0, 0, 0))
        }

        total_images = len(self.image_order)
        processed = 0

        for idx, image_name in enumerate(self.image_order):
            processed += 1
            if processed % 5 == 0 or processed == 1 or processed == total_images:
                percentage = (processed / total_images) * 100
                print(f"Processing images: {processed}/{total_images} ({percentage:.1f}%)")

            # Calculate position
            row = idx // self.atlas_size[0]
            col = idx % self.atlas_size[0]
            x = col * tile_size
            y = row * tile_size

            try:
                # Base color
                base_image_files = [f for f in os.listdir(self.image_dir)
                                if os.path.splitext(f)[0] == image_name]
                if base_image_files:
                    with Image.open(os.path.join(self.image_dir, base_image_files[0])) as img:
                        img = img.convert("RGBA")
                        img = img.resize((tile_size, tile_size), Image.Resampling.LANCZOS)
                        img = ImageOps.mirror(img)  # Flip horizontally
                        atlases['color'].paste(img, (x, y))

                # Normal map
                normal_file = f"{image_name}_normal.png"
                if normal_file in os.listdir(self.image_dir):
                    with Image.open(os.path.join(self.image_dir, normal_file)) as img:
                        img = img.resize((tile_size, tile_size), Image.Resampling.LANCZOS)
                        if img.mode != "RGBA":
                            img = img.convert("RGBA")
                        img = ImageOps.mirror(img)  # Flip horizontally
                        atlases['normal'].paste(img, (x, y))
                else:
                    # If no normal map exists, create one from the base color image
                    if base_image_files:
                        with Image.open(os.path.join(self.image_dir, base_image_files[0])) as img:
                            img = img.convert("RGBA")
                            img = ImageOps.mirror(img)  # Flip the base image before processing
                            # Rest of normal map generation...
                            depth_map = ImageOps.grayscale(img)
                            depth_map = ImageOps.invert(depth_map)
                            enhancer = ImageEnhance.Contrast(depth_map)
                            depth_map = enhancer.enhance(2.0)
                            depth_map = depth_map.filter(ImageFilter.GaussianBlur(radius=1))
                            
                            depth_array = np.array(depth_map)
                            # ... [rest of normal map generation code remains the same]
                            
                            normal_img = Image.fromarray(normal_map)
                            normal_img = normal_img.resize((tile_size, tile_size), Image.Resampling.LANCZOS)
                            
                            if normal_img.mode != "RGBA":
                                normal_img = normal_img.convert("RGBA")
                                
                            atlases['normal'].paste(normal_img, (x, y))

                # Emission map
                emission_file = f"{image_name}_emission.png"
                if emission_file in os.listdir(self.image_dir):
                    with Image.open(os.path.join(self.image_dir, emission_file)) as img:
                        img = img.resize((tile_size, tile_size), Image.Resampling.LANCZOS)
                        img = ImageOps.mirror(img)  # Flip horizontally
                        atlases['emission'].paste(img, (x, y))

                # Roughness map
                roughness_file = f"{image_name}_roughness.png"
                if roughness_file in os.listdir(self.image_dir):
                    with Image.open(os.path.join(self.image_dir, roughness_file)) as img:
                        img = img.resize((tile_size, tile_size), Image.Resampling.LANCZOS)
                        img = ImageOps.mirror(img)  # Flip horizontally
                        atlases['roughness'].paste(img, (x, y))

            except Exception as e:
                print(f"Error processing {image_name}: {str(e)}")
                continue

        # Save all atlases
        atlas_paths = {}
        for atlas_type, atlas in atlases.items():
            atlas_path = os.path.join(self.image_dir, f"texture_atlas_{atlas_type}.png")
            atlas.save(atlas_path, "PNG")
            atlas_paths[atlas_type] = atlas_path

            # Remove existing atlas if it exists
            atlas_name = f"texture_atlas_{atlas_type}.png"
            if atlas_name in bpy.data.images:
                bpy.data.images.remove(bpy.data.images[atlas_name])
            
            # Load new atlas
            bpy.data.images.load(atlas_path)

        return atlas_paths

    def create_texture_atlas(self):
        """Create texture atlas using the best available method."""
        if USE_PIL:
            return self.create_texture_atlas_pil()
        else:
            return self.create_texture_atlas_blender()

    def create_blender_material(self, name, atlas_paths):
        """Create a Blender material using all texture atlases."""
        material_name = f"{name}_sign"

        # Remove existing material if it exists
        if material_name in bpy.data.materials:
            bpy.data.materials.remove(bpy.data.materials[material_name])
        
        # Create new material
        mat = bpy.data.materials.new(name=material_name)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        nodes.clear()
        
        # Create and position nodes
        tex_coord = nodes.new('ShaderNodeTexCoord')
        tex_coord.location = (-800, 0)

        # Create texture nodes for each map
        tex_nodes = {}
        
        # Color texture
        if 'color' in atlas_paths:
            tex_nodes['color'] = nodes.new('ShaderNodeTexImage')
            tex_nodes['color'].location = (-400, 200)
            tex_nodes['color'].image = bpy.data.images[os.path.basename(atlas_paths['color'])]
        
        # Normal texture
        normal_map = None
        if 'normal' in atlas_paths:
            try:
                tex_nodes['normal'] = nodes.new('ShaderNodeTexImage')
                tex_nodes['normal'].location = (-400, -100)
                tex_nodes['normal'].image = bpy.data.images[os.path.basename(atlas_paths['normal'])]
                normal_map = nodes.new('ShaderNodeNormalMap')
                normal_map.location = (-200, -100)
            except Exception as e:
                print(f"Warning: Could not set up normal map for {name}: {str(e)}")
        
        # Emission texture
        if 'emission' in atlas_paths:
            try:
                tex_nodes['emission'] = nodes.new('ShaderNodeTexImage')
                tex_nodes['emission'].location = (-400, -300)
                tex_nodes['emission'].image = bpy.data.images[os.path.basename(atlas_paths['emission'])]
            except Exception as e:
                print(f"Warning: Could not set up emission map for {name}: {str(e)}")
        
        # Roughness texture
        if 'roughness' in atlas_paths:
            try:
                tex_nodes['roughness'] = nodes.new('ShaderNodeTexImage')
                tex_nodes['roughness'].location = (-400, -500)
                tex_nodes['roughness'].image = bpy.data.images[os.path.basename(atlas_paths['roughness'])]
            except Exception as e:
                print(f"Warning: Could not set up roughness map for {name}: {str(e)}")

        # Create main shader
        principled = nodes.new('ShaderNodeBsdfPrincipled')
        principled.location = (0, 0)
        
        output = nodes.new('ShaderNodeOutputMaterial')
        output.location = (300, 0)

        # Connect nodes
        links = mat.node_tree.links
        
        # Connect all texture coordinates
        for tex_node in tex_nodes.values():
            links.new(tex_coord.outputs['UV'], tex_node.inputs['Vector'])

        # Connect color
        if 'color' in tex_nodes:
            links.new(tex_nodes['color'].outputs['Color'], principled.inputs['Base Color'])
        
        # Connect normal map if it exists
        if 'normal' in tex_nodes and normal_map:
            links.new(tex_nodes['normal'].outputs['Color'], normal_map.inputs['Color'])
            links.new(normal_map.outputs['Normal'], principled.inputs['Normal'])
        
        if 'emission' in tex_nodes:
            try:
                links.new(tex_nodes['emission'].outputs['Color'], principled.inputs['Emission Color'])
                # Also connect to emission strength with a default value
                principled.inputs['Emission Strength'].default_value = 1.0
            except Exception as e:
                print(f"Warning: Could not connect emission map for {name}: {str(e)}")
        
        # Connect roughness if it exists
        if 'roughness' in tex_nodes:
            try:
                links.new(tex_nodes['roughness'].outputs['Color'], principled.inputs['Roughness'])
            except Exception as e:
                print(f"Warning: Could not connect roughness map for {name}: {str(e)}")

        # Connect output
        links.new(principled.outputs['BSDF'], output.inputs['Surface'])

        return mat

    def apply_materials_to_objects(self, atlas_paths):
        """Apply materials to objects with proper UV mapping."""
        print("Applying materials to objects...")

        # First, create a mapping of object names to their indices
        object_indices = {f"{name}_sign": idx for idx, name in enumerate(self.image_order)}

        # Process each object
        for obj_name, idx in object_indices.items():
            if obj_name not in bpy.data.objects:
                print(f"Warning: Object {obj_name} not found")
                continue

            obj = bpy.data.objects[obj_name]
            name = obj_name.replace('_sign', '')

            # Calculate atlas position
            row = idx // self.atlas_size[0]
            col = idx % self.atlas_size[0]
            
            print(f"Processing {name} (index {idx}): row {row}, col {col}")

            # Calculate UV coordinates
            u_start = col / self.atlas_size[0]
            u_end = (col + 1) / self.atlas_size[0]
            v_start = 1 - ((row + 1) / self.atlas_size[1])
            v_end = 1 - (row / self.atlas_size[1])

            # Create material
            material = self.create_blender_material(name, atlas_paths)
            
            # Clear existing materials
            obj.data.materials.clear()
            obj.data.materials.append(material)

            # Clear and create new UV layer
            while len(obj.data.uv_layers) > 0:
                obj.data.uv_layers.remove(obj.data.uv_layers[0])
            uv_layer = obj.data.uv_layers.new()

            # UV coordinates for quad faces
            uv_coords = [
                (u_start, v_start),  # bottom-left
                (u_start, v_end),    # top-left
                (u_end, v_end),      # top-right
                (u_end, v_start)     # bottom-right
            ]

            # Apply UVs
            for face in obj.data.polygons:
                if abs(face.normal.y) > 0.9:  # Y-facing face
                    for loop_idx, uv_coord in zip(face.loop_indices, uv_coords):
                        uv_layer.data[loop_idx].uv = uv_coord


def main():
    try:
        print("\n=== Starting Texture Atlas Generation Process ===")
        print("Initializing generator...")
        generator = TextureAtlasGenerator()

        print("\n=== Cleaning up existing atlases and materials ===")
        generator.cleanup_texture_atlas()

        print("\n=== Reading Order File ===")
        print(f"Looking for order file in: {generator.data_dir}")
        generator.read_image_order()
        print(f"Successfully loaded {len(generator.image_order)} names from order file")

        print("\n=== Creating Texture Atlas ===")
        print(f"Method: {'PIL (fast)' if USE_PIL else 'Blender (slower)'}")
        print(f"Atlas configuration:")
        print(f"- Grid size: {generator.atlas_size[0]}x{generator.atlas_size[1]}")
        print(f"- Looking for images in: {generator.image_dir}")
        start_time = datetime.now()
        atlas_paths = generator.create_texture_atlas()
        end_time = datetime.now()
        duration = end_time - start_time
        print(f"\nAtlas creation completed in {duration.total_seconds():.1f} seconds")
        print(f"Atlas saved to: {atlas_paths['color']}")  # Use color atlas as main reference

        print("\n=== Applying Materials to Objects ===")
        print("Starting material application and UV mapping...")
        start_time = datetime.now()
        generator.apply_materials_to_objects(atlas_paths)
        end_time = datetime.now()
        duration = end_time - start_time
        print(
            f"\nMaterial application completed in {duration.total_seconds():.1f} seconds"
        )

        print("\n=== Process Complete! ===")
        print("Summary:")
        print(f"- Atlas files created:")
        for atlas_type, path in atlas_paths.items():
            print(f"  - {atlas_type}: {os.path.basename(path)}")
        print(f"- Images processed: {len(generator.image_order)}")
        print(f"- Location: {generator.blend_dir}")

    except Exception as e:
        print(f"\n!!! ERROR !!!")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print("\nPlease check:")
        print("1. Blend file is saved")
        print("2. Data and image directories exist")
        print("3. Order file exists for today's date")
        print("4. All referenced images exist")


if __name__ == "__main__":
    main()
