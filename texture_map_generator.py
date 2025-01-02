import bpy
import os
from datetime import datetime
from PIL import Image, ImageFilter, ImageOps, ImageEnhance
import numpy as np

class TextureMapGenerator:
    def __init__(self):
        self.blend_dir = os.path.dirname(bpy.data.filepath)
        if not self.blend_dir:
            raise RuntimeError("Blend file must be saved before running this script")

        self.today = datetime.today().strftime("%m-%d-%Y")
        self.image_dir = os.path.join(self.blend_dir, "images", self.today)

        if not os.path.exists(self.image_dir):
            raise FileNotFoundError(f"Image directory not found at {self.image_dir}")

    def create_depth_map(self, image):
        """Create a depth map from the image by converting to grayscale and enhancing contrast"""
        # Convert to grayscale and invert (assuming brighter colors should be "higher")
        depth = ImageOps.grayscale(image)
        depth = ImageOps.invert(depth)
        
        # Enhance contrast to make the depth more pronounced
        enhancer = ImageEnhance.Contrast(depth)
        depth = enhancer.enhance(2.0)
        
        # Smooth the depth map slightly
        depth = depth.filter(ImageFilter.GaussianBlur(radius=1))
        
        return depth

    def create_normal_map(self, depth_map):
        """Create a normal map from the depth map using Sobel operators"""
        # Convert depth map to numpy array
        depth_array = np.array(depth_map)
        
        # Create Sobel operators
        sobel_x = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]])
        sobel_y = np.array([[1, 2, 1], [0, 0, 0], [-1, -2, -1]])
        
        # Calculate gradients
        grad_x = np.zeros_like(depth_array, dtype=float)
        grad_y = np.zeros_like(depth_array, dtype=float)
        
        for i in range(1, depth_array.shape[0] - 1):
            for j in range(1, depth_array.shape[1] - 1):
                grad_x[i, j] = np.sum(depth_array[i-1:i+2, j-1:j+2] * sobel_x)
                grad_y[i, j] = np.sum(depth_array[i-1:i+2, j-1:j+2] * sobel_y)
        
        # Normalize gradients
        strength = 5.0  # Adjust this value to control normal map strength
        grad_x = grad_x * strength / 255.0
        grad_y = grad_y * strength / 255.0
        
        # Create normal map
        normal_map = np.zeros((depth_array.shape[0], depth_array.shape[1], 3))
        normal_map[..., 0] = grad_x
        normal_map[..., 1] = grad_y
        normal_map[..., 2] = 1.0
        
        # Normalize vectors
        norm = np.sqrt(np.sum(normal_map**2, axis=2))
        normal_map /= norm[..., np.newaxis]
        
        # Convert to RGB format (0-255)
        normal_map = ((normal_map + 1.0) * 0.5 * 255).astype(np.uint8)
        
        return Image.fromarray(normal_map)

    def create_emission_map(self, image):
        """Create an emission map by enhancing bright areas and reducing dark areas"""
        # Convert to grayscale
        emission = ImageOps.grayscale(image)
        
        # Enhance contrast
        enhancer = ImageEnhance.Contrast(emission)
        emission = enhancer.enhance(2.0)
        
        # Enhance brightness
        enhancer = ImageEnhance.Brightness(emission)
        emission = enhancer.enhance(1.5)
        
        # Create colored emission based on original image
        colored_emission = Image.new('RGB', image.size)
        for x in range(image.size[0]):
            for y in range(image.size[1]):
                orig_color = image.getpixel((x, y))
                emission_value = emission.getpixel((x, y))
                if isinstance(orig_color, tuple):
                    colored_emission.putpixel((x, y), 
                        tuple(int(c * emission_value / 255) for c in orig_color[:3]))
                
        return colored_emission

    def create_roughness_map(self, image):
        """Create a roughness map based on image intensity"""
        # Convert to grayscale
        roughness = ImageOps.grayscale(image)
        
        # Invert and enhance contrast
        roughness = ImageOps.invert(roughness)
        enhancer = ImageEnhance.Contrast(roughness)
        roughness = enhancer.enhance(1.5)
        
        return roughness

    def process_images(self):
        """Process all images in the directory"""
        for filename in os.listdir(self.image_dir):
            if filename.endswith(('.png', '.jpg', '.jpeg')) and not any(x in filename for x in ['_normal', '_depth', '_emission', '_roughness']):
                try:
                    # Load original image
                    image_path = os.path.join(self.image_dir, filename)
                    with Image.open(image_path) as img:
                        img = img.convert('RGBA')
                        base_name = os.path.splitext(filename)[0]
                        
                        print(f"Processing {filename}...")
                        
                        # Create depth map
                        depth_map = self.create_depth_map(img)
                        depth_path = os.path.join(self.image_dir, f"{base_name}_depth.png")
                        depth_map.save(depth_path)
                        
                        # Create normal map
                        normal_map = self.create_normal_map(depth_map)
                        normal_path = os.path.join(self.image_dir, f"{base_name}_normal.png")
                        normal_map.save(normal_path)
                        
                        # Create emission map
                        emission_map = self.create_emission_map(img)
                        emission_path = os.path.join(self.image_dir, f"{base_name}_emission.png")
                        emission_map.save(emission_path)
                        
                        # Create roughness map
                        roughness_map = self.create_roughness_map(img)
                        roughness_path = os.path.join(self.image_dir, f"{base_name}_roughness.png")
                        roughness_map.save(roughness_path)
                        
                except Exception as e:
                    print(f"Error processing {filename}: {str(e)}")
                    continue

def main():
    try:
        print("\n=== Starting Texture Map Generation Process ===")
        generator = TextureMapGenerator()
        
        print("\n=== Processing Images ===")
        start_time = datetime.now()
        generator.process_images()
        end_time = datetime.now()
        duration = end_time - start_time
        
        print(f"\nProcess completed in {duration.total_seconds():.1f} seconds")
        print(f"Output location: {generator.image_dir}")
        
    except Exception as e:
        print(f"\n!!! ERROR !!!")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")

if __name__ == "__main__":
    main()