import bpy
import os
from datetime import datetime

try:
    from PIL import Image

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
        """Remove all existing texture atlas images from Blender."""
        # Remove any existing texture atlas images from Blender
        for image in bpy.data.images:
            if image.name.startswith("texture_atlas"):
                bpy.data.images.remove(image)

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
            'normal': Image.new("RGBA", (atlas_size, atlas_size), (0, 0, 0, 0)),
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

            # Process each texture type
            try:
                # Debug print
                print(f"\nProcessing textures for {image_name}")
                print(f"Looking in directory: {self.image_dir}")
                print(f"Available files: {os.listdir(self.image_dir)}")

                # Base color
                base_image_files = [f for f in os.listdir(self.image_dir)
                                if os.path.splitext(f)[0] == image_name]
                if base_image_files:
                    print(f"Found base texture: {base_image_files[0]}")
                    with Image.open(os.path.join(self.image_dir, base_image_files[0])) as img:
                        img = img.convert("RGBA")
                        img = img.resize((tile_size, tile_size), Image.Resampling.LANCZOS)
                        atlases['color'].paste(img, (x, y))

                # Emission map
                emission_file = f"{image_name}_emission.png"
                print(f"Looking for emission file: {emission_file}")
                if emission_file in os.listdir(self.image_dir):
                    print(f"Found emission texture: {emission_file}")
                    with Image.open(os.path.join(self.image_dir, emission_file)) as img:
                        img = img.resize((tile_size, tile_size), Image.Resampling.LANCZOS)
                        atlases['emission'].paste(img, (x, y))
                else:
                    print(f"No emission texture found for {image_name}")

                # Roughness map
                roughness_file = f"{image_name}_roughness.png"
                if roughness_file in os.listdir(self.image_dir):
                    with Image.open(os.path.join(self.image_dir, roughness_file)) as img:
                        img = img.resize((tile_size, tile_size), Image.Resampling.LANCZOS)
                        atlases['roughness'].paste(img, (x, y))

            except Exception as e:
                print(f"Error processing {image_name}: {str(e)}")
                continue

        # Debug print for atlases
        print("\nAtlases created:")
        for atlas_type in atlases:
            print(f"Atlas type: {atlas_type}")

        # Save all atlases
        atlas_paths = {}
        for atlas_type, atlas in atlases.items():
            atlas_path = os.path.join(self.image_dir, f"texture_atlas_{atlas_type}.png")
            atlas.save(atlas_path, "PNG")
            atlas_paths[atlas_type] = atlas_path

            # Load into Blender
            if atlas_path in bpy.data.images:
                bpy.data.images[atlas_path].reload()
            else:
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

            # First, sort objects by index to ensure correct order
            sorted_items = []
            for idx, name in enumerate(self.image_order):
                obj_name = f"{name}_sign"
                if obj_name in bpy.data.objects:
                    sorted_items.append((idx, name, bpy.data.objects[obj_name]))
                else:
                    print(f"Warning: Object {obj_name} not found")

            # Process objects in strict order
            for idx, name, obj in sorted_items:
                # Calculate exact atlas position
                row = idx // self.atlas_size[0]
                col = idx % self.atlas_size[0]
                
                print(f"Processing {name} (index {idx}): row {row}, col {col}")  # Debug print

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

                # Fixed UV coordinates for quad faces (swap u_start and u_end)
                uv_coords = [
                    (u_end, v_start),    # bottom-right
                    (u_end, v_end),      # top-right
                    (u_start, v_end),    # top-left
                    (u_start, v_start)   # bottom-left
                ]

                # Apply UVs to Y-facing faces
                for face in obj.data.polygons:
                    if abs(face.normal.y) > 0.9:  # Y-facing face
                        for loop_idx, uv_coord in zip(face.loop_indices, uv_coords):
                            uv_layer.data[loop_idx].uv = uv_coord


def main():
    try:
        print("\n=== Starting Texture Atlas Generation Process ===")
        print("Initializing generator...")
        generator = TextureAtlasGenerator()

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
