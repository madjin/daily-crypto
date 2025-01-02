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
        print("\nCreating texture atlas using PIL...")
        atlas_size = 1024
        tile_size = atlas_size // self.atlas_size[0]
        print(f"Atlas dimensions: {atlas_size}x{atlas_size} pixels")
        print(f"Individual tile size: {tile_size}x{tile_size} pixels")

        # Create new atlas image
        atlas = Image.new("RGBA", (atlas_size, atlas_size), (0, 0, 0, 0))

        # Process counter for progress tracking
        total_images = len(self.image_order)
        processed = 0

        for idx, image_name in enumerate(self.image_order):
            processed += 1
            if processed % 5 == 0 or processed == 1 or processed == total_images:
                percentage = (processed / total_images) * 100
                print(
                    f"Processing images: {processed}/{total_images} ({percentage:.1f}%)"
                )
                if processed % 25 == 0:
                    print(f"Current image: {image_name}")

            # Find image file
            image_files = [
                f
                for f in os.listdir(self.image_dir)
                if os.path.splitext(f)[0] == image_name
            ]

            if not image_files:
                print(f"Warning: No image file found for {image_name}")
                continue

            # Load and resize source image
            img_path = os.path.join(self.image_dir, image_files[0])
            try:
                with Image.open(img_path) as img:
                    img = img.convert("RGBA")
                    img = img.resize((tile_size, tile_size), Image.Resampling.LANCZOS)

                    # Calculate position
                    row = idx // self.atlas_size[0]
                    col = idx % self.atlas_size[0]
                    x = col * tile_size
                    y = row * tile_size

                    # Paste into atlas
                    atlas.paste(img, (x, y))
            except Exception as e:
                print(f"Error processing {image_name}: {str(e)}")
                continue

        # Save atlas in today's directory
        atlas_path = os.path.join(self.image_dir, "texture_atlas.png")
        atlas.save(atlas_path, "PNG")
        
        # Clean up old atlas images before loading new one
        self.cleanup_texture_atlas()

        # Load into Blender
        if atlas_path in bpy.data.images:
            bpy.data.images[atlas_path].reload()
        else:
            bpy.data.images.load(atlas_path)

        return atlas_path

    def create_texture_atlas(self):
        """Create texture atlas using the best available method."""
        if USE_PIL:
            return self.create_texture_atlas_pil()
        else:
            return self.create_texture_atlas_blender()

    def create_blender_material(self, name, atlas_path):
        """Create a Blender material using the texture atlas."""
        material_name = f"{name}_sign"

        # Remove existing material if it exists
        if material_name in bpy.data.materials:
            bpy.data.materials.remove(bpy.data.materials[material_name])
        
        # Create new material
        mat = bpy.data.materials.new(name=material_name)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        nodes.clear()
        
        # Create nodes
        tex_coord = nodes.new('ShaderNodeTexCoord')
        tex_image = nodes.new('ShaderNodeTexImage')
        principled = nodes.new('ShaderNodeBsdfPrincipled')
        output = nodes.new('ShaderNodeOutputMaterial')

        # Load atlas texture
        atlas_name = os.path.basename(atlas_path)
        tex_image.image = bpy.data.images[atlas_name]  # Should exist because we loaded it in create_texture_atlas_pil

        # Connect nodes
        links = mat.node_tree.links
        links.new(tex_coord.outputs['UV'], tex_image.inputs['Vector'])
        links.new(tex_image.outputs['Color'], principled.inputs['Base Color'])
        links.new(principled.outputs['BSDF'], output.inputs['Surface'])

        return mat

    def apply_materials_to_objects(self, atlas_path):
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
                material = self.create_blender_material(name, atlas_path)
                
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
        atlas_path = generator.create_texture_atlas()
        end_time = datetime.now()
        duration = end_time - start_time
        print(f"\nAtlas creation completed in {duration.total_seconds():.1f} seconds")
        print(f"Atlas saved to: {atlas_path}")

        print("\n=== Applying Materials to Objects ===")
        print("Starting material application and UV mapping...")
        start_time = datetime.now()
        generator.apply_materials_to_objects(atlas_path)
        end_time = datetime.now()
        duration = end_time - start_time
        print(
            f"\nMaterial application completed in {duration.total_seconds():.1f} seconds"
        )

        print("\n=== Process Complete! ===")
        print("Summary:")
        print(f"- Atlas file: {os.path.basename(atlas_path)}")
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
