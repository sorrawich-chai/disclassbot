import easyocr
import cv2
import matplotlib.pyplot as plt
import os

def read_text_from_image_easyocr(image_path, lang_list=['en', 'th'], gpu=False):
    try:
        reader = easyocr.Reader(lang_list, gpu=gpu)
        result = reader.readtext(image_path)

        extracted_text = ""
        for (bbox, text, prob) in result:
            extracted_text += text + "\n"

        return extracted_text, result

    except Exception as e:
        return f"An error occurred: {e}", []

def timetable_fidner():
    image_file_path = []
    for i in range(0,11):
        for j in range(0,4):
            image_file_path.append(f'{i}{j}.png')
    table = {"monday": [], "tuesday": [], "wednesday": [], "thursday": [], "friday": []}
    days = ["monday", "tuesday", "wednesday", "thursday", "friday"]

    for index,day in enumerate(days):
        for classes in range(0,11):
            image_path = f'{index}{classes}.png'
            text, detections = read_text_from_image_easyocr(image_path, lang_list=['en', 'th'])
            lines = text.split('\n')
            subject = lines[0] if len(lines) > 0 else ""
            teacher = lines[1] if len(lines) > 1 else ""
            room = lines[2] if len(lines) > 2 else ""
            table[day].append({"subject": subject, "teacher": teacher, "room": room})

    os.remove('class_image.jpg')
    for img_path in image_file_path:
        try:
            os.remove(img_path)
        except FileNotFoundError:
            pass
    return table
