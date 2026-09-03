import os
import base64

# Get the directory of the current script (modules/)
current_dir = os.path.dirname(os.path.abspath(__file__))

# Go up one level to the main/root folder where Dr.png is located
image_path = os.path.join(current_dir, "..", "Dr.png")

def get_image_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode("utf-8")
    else:
        print(f"Warning: Image not found at {path}")
    return ""

img_base64 = get_image_base64(image_path)