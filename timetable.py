import requests
import json
import os


OCR_SPACE_API_KEY = os.getenv('OCR_SPACE_API_KEY')

def ocr_space_api_call(image_path, api_key="K84394532888957", language='tha', is_overlay_required=False, ocr_engine=2):

    try:
        with open(image_path, 'rb') as f:
            # Files parameter for multipart/form-data
            files = {'file': f}

            # Data payload for other parameters
            data = {
                'apikey': api_key,
                'language': language,
                'isOverlayRequired': str(is_overlay_required).lower(), # Needs to be 'true' or 'false' string
                'OCREngine': ocr_engine
            }

            response = requests.post('https://api.ocr.space/parse/image', files=files, data=data)
            response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)

            return response.json()

    except requests.exceptions.RequestException as e:
        print(f"Network or API error: {e}")
        return {"error": str(e)}
    except FileNotFoundError:
        print(f"Error: Image file not found at '{image_path}'")
        return {"error": "Image file not found"}
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return {"error": str(e)}
    

def extract_and_split_ocr_text(ocr_json_response):
    extracted_full_text = ""

    # Check if 'ParsedResults' exists and is not empty
    if 'ParsedResults' in ocr_json_response and ocr_json_response['ParsedResults']:
        # Access the ParsedText from the first (and usually only) result
        extracted_full_text = ocr_json_response['ParsedResults'][0].get('ParsedText', '')
    else:
        print("Warning: No 'ParsedResults' found or it's empty in the OCR JSON response.")
        if 'ErrorMessage' in ocr_json_response and ocr_json_response['ErrorMessage']:
            print(f"API Error Message: {ocr_json_response['ErrorMessage']}")
        return []

    # Split the extracted text by comma and strip whitespace from each part
    split_text_list = [part.strip() for part in extracted_full_text.split(',')]

    return split_text_list


def timetable_fidner():
    image_file_path = []
    for i in range(0,11):
        for j in range(0,4):
            image_file_path.append(f'{i}{j}.png')
    table = {"monday": [], "tuesday": [], "wednesday": [], "thursday": [], "friday": []}
    days = ["monday", "tuesday", "wednesday", "thursday", "friday"]

    for index,day in enumerate(days):
        for classes in range(0,10):
            image_path = f'{index}{classes}.png'
            ocrjson = ocr_space_api_call(image_path, language='auto')
            text = extract_and_split_ocr_text(ocrjson)
            lines = text[0].split('\n')
            subject = lines[0] if len(lines) > 0 else ""
            teacher = lines[1] if len(lines) > 1 else ""
            room = lines[2] if len(lines) > 2 else ""
            print(f"Subject: {subject}, Teacher: {teacher}, Room: {room}")
            table[day].append({"subject": subject, "teacher": teacher, "room": room})

    os.remove('class_image.jpg')

# image_file_path = []
# for i in range(0,11):
#     for j in range(0,4):
#         image_file_path.append(f'{i}{j}.png')
# table = {"monday": [], "tuesday": [], "wednesday": [], "thursday": [], "friday": []}
# days = ["monday", "tuesday", "wednesday", "thursday", "friday"]

# for index,day in enumerate(days):
#     for classes in range(0,11):
#         image_path = f'{index}{classes}.png'
#         ocrjson = ocr_space_api_call(image_path, language='auto')
#         text = extract_and_split_ocr_text(ocrjson)
#         lines = text[0].split('\n')
#         subject = lines[0] if len(lines) > 0 else ""
#         teacher = lines[1] if len(lines) > 1 else ""
#         room = lines[2] if len(lines) > 2 else ""
#         print(f"Subject: {subject}, Teacher: {teacher}, Room: {room}")
#         table[day].append({"subject": subject, "teacher": teacher, "room": room})

# os.remove('class_image.jpg')
# for img_path in image_file_path:
#     try:
#         os.remove(img_path)
#     except FileNotFoundError:
#         pass