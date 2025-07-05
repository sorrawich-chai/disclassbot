from PIL import Image
import os
import numpy as np

def crop_image_from_two_points(image_path, point1, point2, output_path=None):

    try:
        # Open the image file
        img = Image.open(image_path)
        print(f"Successfully opened image: {image_path}")

        # Auto-orient image using EXIF data
        try:
            from PIL import ImageOps
            img = ImageOps.exif_transpose(img)
        except Exception as exif_e:
            print(f"Warning: Could not auto-orient image: {exif_e}")

        left = min(point1[0], point2[0])
        upper = min(point1[1], point2[1])
        right = max(point1[0], point2[0])
        lower = max(point1[1], point2[1])

        # Ensure coordinates are within image bounds (optional, but good practice)
        img_width, img_height = img.size
        left = max(0, left)
        upper = max(0, upper)
        right = min(img_width, right)
        lower = min(img_height, lower)

        # Validate if the crop box is valid (width and height > 0)
        if right <= left or lower <= upper:
            print("Error: The specified points do not form a valid cropping rectangle (width or height is zero or negative).")
            return None

        # Define the cropping box
        crop_box = (left, upper, right, lower)
        print(f"Cropping box calculated: {crop_box}")

        # Perform the crop operation
        cropped_img = img.crop(crop_box)
        print("Image cropped successfully.")

        # Generate a default output path if not provided
        if output_path is None:
            base_name, ext = os.path.splitext(image_path)
            output_path = f"{base_name}_cropped{ext}"

        # Save the cropped image
        cropped_img.save(output_path)
        print(f"Cropped image saved to: {output_path}")
        return output_path

    except FileNotFoundError:
        print(f"Error: Image file not found at '{image_path}'")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None


def create_cropped_image(image):

    input_image_file = image

    list_x = [590,814,1047,1279,1506,1728,1965,2201,2428,2654,2883]
    list_y = [502,705,914,1121,1328,1535]
    coordinated = np.ndarray(shape=(5,10,2,2))

    for i in range(len(list_x)-1):
        for j in range(len(list_y)-1):
            coordinated[j,i,0] = (list_x[i], list_y[j])
            coordinated[j,i,1] = (list_x[i+1], list_y[j+1])

    for i in range(len(coordinated)):
        for j in range(len(coordinated[i])):
            print(f"Cropping from {coordinated[i,j,0]} to {coordinated[i,j,1]}")
            crop_image_from_two_points(
                image_path=input_image_file,
                point1=coordinated[i,j,0],
                point2=coordinated[i,j,1],
                output_path=f'{i}{j}.png'
            )
