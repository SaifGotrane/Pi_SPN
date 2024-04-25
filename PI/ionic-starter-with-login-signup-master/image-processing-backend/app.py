from flask import Flask, request, jsonify
from PIL import Image
import pytesseract
from langdetect import detect
import traceback
import numpy as np
import cv2
from flask_cors import CORS
from fuzzywuzzy import fuzz
import re
import easyocr
from werkzeug.utils import secure_filename
import os
import imutils 
from datetime import datetime
app = Flask(__name__)
CORS(app)
easyocr_reader = easyocr.Reader(['en', 'fr'])
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
global_list = []
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}
import re
from datetime import datetime

def find_dates(sentence):
    date_patterns = [
        r'\d{2}-\d{1,2}-\d{4}',  # dd-mm-yyyy
        r'\d{1,2} (?:[Jj]an(?:uary|vier)|[Ff]eb(?:ruary|vrier)|[Mm]ar(?:ch|s)|[Aa]pr(?:il)|[Mm]ay|[Mm]ai|[Jj]un(?:e|)|[Jj]ul(?:y)|[Aa]ug(?:ust|)|[Ss]ep(?:tember|t)|[Oo]ct(?:ober|obre)|[Nn]ov(?:ember|embre)|[Dd]ec(?:ember|embre)) \d{4}',  # d month yyyy
        r'\d{1,2}\.\d{1,2}\.\d{4}',  # dd.mm.yyyy
        r'\d{1,2}\-\d{1,2}\-\d{4}',  # dd-mm-yyyy
        r'\d{1,2} (?:Jan(?:uary|anvier|jan(?:uary|vier))|Feb(?:ruary|évrier|feb(?:ruary|vrier))|Mar(?:ch|s)|Apr(?:il)|May|Mai|Jun(?:e|)|Jul(?:y)|Aug(?:ust|)|Sep(?:tember|tembre|t)|Oct(?:ober|obre)|Nov(?:ember|embre)|Dec(?:ember|embre)) \d{4}',
        r'\w+ \d{1,2} (?:Jan(?:uary|vier)|Feb(?:ruary|vrier)|Mar(?:ch|s)|Apr(?:il)|May|Mai|Jun(?:e|)|Jul(?:y)|Aug(?:ust|)|Sep(?:tember|t)|Oct(?:ober|obre)|Nov(?:ember|embre)|Dec(?:ember|embre)) \d{4}',  # weekday d month yyyy
        r'\d{1,2}/\d{1,2}/\d{4}',
        r'\d{1,2} (?:Jan(?:uary|anvier|jan(?:uary|vier))|Feb(?:ruary|évrier|feb(?:ruary|vrier))|Mar(?:ch|s)|Apr(?:il)|May|Mai|Jun(?:e|)|Jul(?:y)|Aug(?:ust|)|Sep(?:tember|tembre|t)|Oct(?:ober|obre)|Nov(?:ember|embre)|Dec(?:ember|embre)) \d{4}',  # d/d/yy or dd/d/yy
        r'\d{1,2} (?:[Jj]anvier|[Ff][ée]vrier|[Mm]ars|[Aa]vril|[Mm]ai|[Jj]uin|[Jj]uillet|[Aa]o[uû]t|[Ss]eptembre|[Oo]ctobre|[Nn]ovembre|[Dd][ée]cembre) \d{4}',  # French month format
        r'(?:Lundi|Mardi|Mercredi|Jeudi|Vendredi|Samedi|Dimanche) \d{1,2} (?:Janvier|F[eé]vrier|Mars|Avril|Mai|Juin|Juillet|Ao[uû]t|Septembre|Octobre|Novembre|D[eé]cembre) \d{4}'  # weekday d month (French) yyyy
    ]

    month_dict = {
        'janvier': '01', 'février': '02', 'mars': '03', 'avril': '04',
        'mai': '05', 'juin': '06', 'juillet': '07', 'août': '08',
        'septembre': '09', 'octobre': '10', 'novembre': '11', 'décembre': '12'
    }

    matches = []
    for pattern in date_patterns:
        for match in re.finditer(pattern, sentence):
            date_str = match.group()
            if ' ' in date_str:
                # Adjust the date string for format d month yyyy to dd-mm-yyyy
                for month_name, month_num in month_dict.items():
                    if month_name in date_str.lower():
                        # Remove spaces and replace with hyphens for dd-mm-yyyy format
                        date_str = date_str.replace(' ', '-')
                        date_str = date_str.replace(month_name, month_num)
                        break
            print("Matched substring:", date_str)

            try:
                # Parse the adjusted date string
                if "." in date_str:
                    date_obj = datetime.strptime(date_str, "%d.%m.%Y")
                elif "-" in date_str:
                    date_obj = datetime.strptime(date_str, "%d-%m-%Y")
                else:
                    date_obj = datetime.strptime(date_str, "%d/%m/%Y")
                
                # Format the date as dd/mm/yyyy
                formatted_date = date_obj.strftime("%d/%m/%Y")
                print("Adjusted and formatted date:", formatted_date)
                
                # Append the formatted date to the matches list
                matches.append(formatted_date)
            except ValueError as e:
                print("Error parsing date:", e)

    return matches




def extract_matricules_and_places_from_text(text):
    # Filter words for matricules
    matricule_filters = [
        "l'immatriculation", 'Véhicule:', 'Immatriculation', 'Plaques :', 'Kontrollschild-Nr. :',
        'Targa:', 'Fahrzeug', 'Personenwagen,', 'Plaque', 'contrôle,', 'immatriculé(e)',
        'Kennzeichen', " d'immatriculation:", 'veicolo ', 'PKW', 'vehicle', 'plates',
        'Identifikationscode','Fahrzeug',"véhicule:", r'\b[A-Z]{2} \d{6}\b'  # Added pattern for alphanumeric format
    ]
    places = [
         'Genéve', 'Belgien', 'Genéve', 'CH', 'Carouge', 'Geneve','Zürich', 'Zurich', 'TICINO', 'Zurich', 
    'Fribourg', 'Obwalden', 'Bern', 'vaudoise', 'Autriche', 'Autriche:', 'Genéve', 'GR', 
    'Obwalden', 'TICINO', 'Autriche', 'Luzern', 'Vevey', 'Kehl', 'GR', 'GR', 'GR', 
    'Genéve', 'Carouge', 'FRANCE', 'Genéve', 'Carouge', 'Italie', 'vaudoise', 'Zurich', 
    'Autriche:', 'Deutschland', 'Deutschland'
    ]

    # Extract matricules
    extracted_matricules = []

    # Extract places
    extracted_places = []

    # Define a function to check if two strings are 90% similar
    def is_similar(str1, str2):
        return fuzz.ratio(str1.lower(), str2.lower()) > 75
    
    def is_similar_1(str1, str2):
        return fuzz.ratio(str1.lower(), str2.lower()) > 85

    # Split the text into words
    words = text.split()
    print(words)
    # Loop through each word in the text
    for index, word in enumerate(words):
        # Check if the word is similar to any of the filter words for places
        for filter_word in places:
            if is_similar_1(word, filter_word):
                extracted_places.append(filter_word)
        
        # Check if the word is similar to any of the filter words for matricules
        for filter_word_n in matricule_filters:  
            if is_similar(word, filter_word_n):
                print("filter:", filter_word_n)  
                print("word:", word)
                # Look at the next words for potential matricules
                for next_word_index in range(index + 1, len(words)):
                    next_word = words[next_word_index]
                    if re.match(r'[a-zA-Z]{1,2}-?\d+', next_word):
                        extracted_matricules.append(next_word)
                        break
                    # If the next word is alphabetic and the next next word is a digit, append both to matricules
                    elif next_word.isalpha() and next_word_index + 1 < len(words) and words[next_word_index + 1].isdigit():
                        potential_matricule = next_word + ' ' + words[next_word_index + 1]
                        extracted_matricules.append(potential_matricule)
                        print("Appending potential matricule:", potential_matricule)
                        break

    # Return the extracted matricules and places
    return extracted_matricules, extracted_places


def extract_pairs(extracted_matricules):
    # if len(extracted_matricules) > 2:
#     extracted_pairs = []
#     for i in range(len(extracted_matricules) - 1):
#         current_word = extracted_matricules[i]
#         next_word = extracted_matricules[i + 1]
#         if re.match('[a-zA-Z]{2}-?\d+', current_word):
#             extracted_pairs.append(current_word)
#             break
#         elif len(current_word) == 2 and next_word.isdigit():
#             extracted_pairs.append(current_word + " " + next_word)
#             break
            
#     if extracted_pairs:
#         print("Extracted pairs:", extracted_pairs)
#     else:
#         print("No extracted pairs found.")
# elif len(extracted_matricules) == 2:
#     extracted_pairs = [extracted_matricules[0]] + [extracted_matricules[1]]
#     print("Extracted pairs:", extracted_pairs)
# else:
#     extracted_pairs = [extracted_matricules[0]]
#     print("Extracted pairs:", extracted_pairs)



    formats = {
    "Zurich": r"\bZH [0-9]{1,7}\b",
    "Berne": r"\bBE [0-9]{1,7}\b",
    "Lucerne": r"\bLU [0-9]{,7}\b",
    "Uri": r"\bUR [0-9]{1,7}\b",
    "Schwytz": r"\bSZ [0-9]{1,7}\b",
    "Obwald": r"\bOW [0-9]{1,7}\b",
    "Nidwald": r"\bNW [0-9]{1,7}\b",
    "Glaris": r"\bGL [0-9]{1,7}\b",
    "Zoug": r"\bZG [0-9]{1,7}\b",
    "Fribourg": r"\bFR [0-9]{1,7}\b",
    "Soleure": r"\bSO [0-9]{1,7}\b",
    "Bâle-Ville": r"\bBS [0-9]{1,7}\b",
    "Bâle-Campagne": r"\bBL [0-9]{1,7}\b",
    "Schaffhouse": r"\bSH [0-9]{1,7}\b",
    "Appenzell Rhodes-Extérieures": r"\bAR [0-9]{1,7}\b",
    "Appenzell Rhodes-Intérieures": r"\bAI [0-9]{1,7}\b",
    "Saint-Gall": r"\bSG [0-9]{1,7}\b",
    "Grisons": r"\bGR [0-9]{1,7}\b",
    "Argovie": r"\bAG [0-9]{1,7}\b",
    "Thurgovie": r"\bTG [0-9]{1,7}\b",
    "Tessin": r"\bTI [0-9]{1,7}\b",
    "Vaud": r"\bVD [0-9]{1,7}\b",
    "Valais": r"\bVS [0-9]{1,7}\b",
    "Neuchâtel": r"\bNE [0-9]{1,7}\b",
    "Genève": r"\bGE [0-9]{1,7}\b",
    "Jura": r"\bJU [0-9]{1,7}\b",
    "GE numbers": r"\bGE [0-9]{2,7}\b",
    "Ge-numbers": r"\bGE-[0-9]{2,7}\b",
    "GEnumbers": r"\bGE[0-9]{2,7}\b",
     "Île-de-France (Paris)": r"\b[A-Z]{2} [0-9]{3} [A-Z]{2}\b",
    "Auvergne-Rhône-Alpes (Lyon)": r"\b[A-Z]{2} [0-9]{3} [A-Z]{2}\b",
    "Provence-Alpes-Côte d'Azur (Marseille, Nice)": r"\b[A-Z]{2} [0-9]{3} [A-Z]{2}\b",
    "Occitanie (Toulouse, Montpellier)": r"\b[A-Z]{2} [0-9]{3} [A-Z]{2}\b",
    "Nouvelle-Aquitaine (Bordeaux)": r"\b[A-Z]{2} [0-9]{3} [A-Z]{2}\b",
    "Grand Est (Strasbourg, Nancy)": r"\b[A-Z]{2} [0-9]{3} [A-Z]{2}\b",
    "Hauts-de-France (Lille)": r"\b[A-Z]{2} [0-9]{3} [A-Z]{2}\b",
    "Normandie (Rouen, Caen)": r"\b[A-Z]{2} [0-9]{3} [A-Z]{2}\b",
    "Bretagne (Rennes)": r"\b[A-Z]{2} [0-9]{3} [A-Z]{2}\b",
    "Pays de la Loire (Nantes, Angers)": r"\b[A-Z]{2} [0-9]{3} [A-Z]{2}\b",
    "Centre-Val de Loire (Tours, Orléans)": r"\b[A-Z]{2} [0-9]{3} [A-Z]{2}\b",
    "Bourgogne-Franche-Comté (Dijon, Besançon)": r"\b[A-Z]{2} [0-9]{3} [A-Z]{2}\b",
    "Nouvelle-Calédonie (Nouméa)": r"\b[0-9]{3} [A-Z]{2}\b",
    "La Réunion (Saint-Denis)": r"\b[0-9]{3} [A-Z]{3}\b",
    "Guadeloupe (Pointe-à-Pitre)": r"\b[A-Z]{2} [0-9]{3} [A-Z]\b",
    "Martinique (Fort-de-France)": r"\b[A-Z]{2} [0-9]{3} [A-Z]\b",
    "Guyane (Cayenne)": r"\b[A-Z]{2} [0-9]{3} [A-Z]\b",
     "Vienna (Vienne)": r"\b[A-Z]{1,2} [0-9]{1,4}\b",
    "Graz": r"\b[A-Z]{1,2} [0-9]{1,4}\b",
    "Linz": r"\b[A-Z]{1,2} [0-9]{1,4}\b",
    "Salzburg": r"\b[A-Z]{1,2} [0-9]{1,4}\b",
    "Innsbruck": r"\b[A-Z]{1,2} [0-9]{1,4}\b",
    "Klagenfurt": r"\b[A-Z]{1,2} [0-9]{1,4}\b",
    "Villach": r"\b[A-Z]{1,2} [0-9]{1,4}\b",
    "Wels": r"\b[A-Z]{1,2} [0-9]{1,4}\b",
    "St. Pölten": r"\b[A-Z]{1,2} [0-9]{1,4}\b",
    "Dornbirn": r"\b[A-Z]{1,2} [0-9]{1,4}\b",
    "Wiener Neustadt": r"\b[A-Z]{1,2} [0-9]{1,4}\b",
    "Steyr": r"\b[A-Z]{1,2} [0-9]{1,4}\b",
    "Feldkirch": r"\b[A-Z]{1,2} [0-9]{1,4}\b",
    "Bregenz": r"\b[A-Z]{1,2} [0-9]{1,4}\b",
    "Leoben": r"\b[A-Z]{1,2} [0-9]{1,4}\b",
    "Krems an der Donau": r"\b[A-Z]{1,2} [0-9]{1,4}\b",
    "Baden": r"\b[A-Z]{1,2} [0-9]{1,4}\b",
    "Wolfsberg": r"\b[A-Z]{1,2} [0-9]{1,4}\b",
    "Klosterneuburg": r"\b[A-Z]{1,2} [0-9]{1,4}\b",
    "Leonding": r"\b[A-Z]{1,2} [0-9]{1,4}\b",
    "Traun": r"\b[A-Z]{1,2} [0-9]{1,4}\b",
    "Amstetten": r"\b[A-Z]{1,2} [0-9]{1,4}\b",
    "Kapfenberg": r"\b[A-Z]{1,2} [0-9]{1,4}\b",
    "Lustenau": r"\b[A-Z]{1,2} [0-9]{1,4}\b",
    "Hallein": r"\b[A-Z]{1,2} [0-9]{1,4}\b",
    "Mödling": r"\b[A-Z]{1,2} [0-9]{1,4}\b",
    "Kufstein": r"\b[A-Z]{1,2} [0-9]{1,4}\b",
    "Traiskirchen": r"\b[A-Z]{1,2} [0-9]{1,4}\b",
    "Schwechat": r"\b[A-Z]{1,2} [0-9]{1,4}\b",
    "Ternitz": r"\b[A-Z]{1,2} [0-9]{1,4}\b",
    "Ansfelden": r"\b[A-Z]{1,2} [0-9]{1,4}\b",
    "Stockerau": r"\b[A-Z]{1,2} [0-9]{1,4}\b",
    "Saalfelden am Steinernen Meer": r"\b[A-Z]{1,2} [0-9]{1,4}\b",
    "Tulln": r"\b[A-Z]{1,2} [0-9]{1,4}\b",
    "Hohenems": r"\b[A-Z]{1,2} [0-9]{1,4}\b",
    "Spittal an der Drau": r"\b[A-Z]{1,2} [0-9]{1,4}\b",
    "Telfs": r"\b[A-Z]{1,2} [0-9]{1,4}\b",
    "Feldkirchen in Kärnten": r"\b[A-Z]{1,2} [0-9]{1,4}\b",
    "Bruck an der Mur": r"\b[A-Z]{1,2} [0-9]{1,4}\b",
    "Bludenz": r"\b[A-Z]{1,2} [0-9]{1,4}\b",
    "Gmunden": r"\b[A-Z]{1,2} [0-9]{1,4}\b",
    "Bad Ischl": r"\b[A-Z]{1,2} [0-9]{1,4}\b",
    "Eisenstadt": r"\b[A-Z]{1,2} [0-9]{1,4}\b",
    "Schwaz": r"\b[A-Z]{1,2} [0-9]{1,4}\b",
    "Hall in Tirol": r"\b[A-Z]{1,2} [0-9]{1,4}\b",
    "Wörgl": r"\b[A-Z]{1,2} [0-9]{1,4}\b",
    "Lienz": r"\b[A-Z]{1,2} [0-9]{1,4}\b",
    "Ried im Innkreis": r"\b[A-Z]{1,2} [0-9]{1,4}\b",
    "Vöcklabruck": r"\b[A-Z]{1,2} [0-9]{1,4}\b",
    "Wals-Siezenheim": r"\b[A-Z]{1,2} [0-9]{1,4}\b",
    "Marchtrenk": r"\b[A-Z]{1,2} [0-9]{1,4}\b",
    "Gänserndorf": r"\b[A-Z]{1,2} [0-9]{1,4}\b",
    "Neunkirchen": r"\b[A-Z]{1,2} [0-9]{1,4}\b",
    "Korneuburg": r"\b[A-Z]{1,2} [0-9]{1,4}\b",
    "Rankweil": r"\b[A-Z]{1,2} [0-9]{1,4}\b",
    "Neusiedl am See": r"\b[A-Z]{1,2} [0-9]{1,4}\b",
    "Hollabrunn": r"\b[A-Z]{1,2} [0-9]{1,4}\b",
    "Enns": r"\b[A-Z]{1,2} [0-9]{1,4}\b",
    "Rottenmann": r"\b[A-Z]{1,2} [0-9]{1,4}\b",
    "Zwettl": r"\b[A-Z]{1,2} [0-9]{1,4}\b",
    "Mistelbach": r"\b[A-Z]{1,2} [0-9]{1,4}\b",
    "Waidhofen an der Ybbs": r"\b[A-Z]{1,2} [0-9]{1,4}\b",
    "Braunau am Inn": r"\b[A-Z]{1,2} [0-9]{1,4}\b"
    
}

    extracted_pairs = []
    
    # Parcourir chaque format et rechercher dans les matricules extraits
    for regex_pattern in formats.values():
        match = re.search(regex_pattern, extracted_matricules)
        if match:
            print("Match found:", match.group(0))
            extracted_pairs.append(match.group(0))
        else:
            print("No match found for pattern:", regex_pattern)
    return extracted_pairs


def remove_symbols(extracted_pairs):
    extracted_sentence = ' '.join(extracted_pairs)
    start_index = 0
    end_index = len(extracted_sentence)
    
    for i, char in enumerate(extracted_sentence):
        if char.isalnum():
            start_index = i
            break
    
    for i in range(len(extracted_sentence) - 1, -1, -1):
        if extracted_sentence[i].isalnum():
            end_index = i + 1
            break
    
    return extracted_sentence[start_index:end_index]

# Function to process image with EasyOCR using the specified language


import os

def clean_text(text):
    # Remove leading and trailing non-alphanumeric characters from each word
    cleaned_words = [re.sub(r'^\W+|\W+$', '', word) for word in text.split()]
    return ' '.join(cleaned_words)
import os

@app.route('/process_image_easyocr', methods=['POST'])
def process_image_easyocr():
    try:
        # Get the list of files in the uploads directory
        files = os.listdir(app.config['UPLOAD_FOLDER'])
        print("Files in uploads directory:", files)
        
        # Check if any files exist in the directory
        if not files:
            print("No files found in the uploads directory")
            return jsonify({'error': 'No files found in the uploads directory'}), 400
        
        # Assuming only one file is present, select the first file
        filename = files[0]
        print("Processing file:", filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        print("Filepath:", filepath)
        
        # Read the image from the filepath
        img = cv2.imread(filepath)
        
        # Get the submitted language from the request JSON
        submitLanguage = request.json.get('submitLanguage')
        print("Submit language:", submitLanguage)

        # Ensure that the submitLanguage value is provided
        if not submitLanguage:
            print("Submit language is missing")
            return jsonify({'error': 'submitLanguage is missing'}), 400
        
        # Process the image with EasyOCR using the specified language
        reader = easyocr.Reader([submitLanguage])

        # Perform OCR on the image
        results = reader.readtext(img)
        print(results)

        # Extract detected texts
        detected_text = ' '.join(result[1] for result in results)
        print("Detected Text:", detected_text)
        cleaned_text = clean_text(detected_text)
        print("Detected Text:", cleaned_text)
        easyocr_global_list = find_dates(cleaned_text)
        print("EasyOCR Global List:", easyocr_global_list)

        # Extend global_list with EasyOCR dates
        global global_list
        global_list.extend(easyocr_global_list)

        # Extract matricules and places from the concatenated text
        extracted_matricules, extracted_places = extract_matricules_and_places_from_text(cleaned_text)
        print("Extracted Matricules:", extracted_matricules)
        print("Extracted Places:", extracted_places)
        matricules_sentence = " ".join(["Matricules extracted:", " ".join(extracted_matricules)])
        print(matricules_sentence)
        # Extract pairs from matricules
        extracted_pairs = extract_pairs( matricules_sentence)
        print("Extracted Pairs:", extracted_pairs)
        extracted_pairs=extracted_pairs[0]
        # Remove symbols from extracted pairs
        cleaned_matricule = remove_symbols(extracted_pairs)
        print("Cleaned Matricule:", cleaned_matricule)
       
        

        # Return the extracted matricule and places
        return jsonify({'global_list': global_list, 'matricule': cleaned_matricule, 'places': extracted_places}), 200

    except Exception as e:
        # Handle any errors that may occur during processing
        print(f"Error processing image with EasyOCR: {e}")
        return jsonify({'error': 'Error processing image with EasyOCR'}), 500


@app.route('/process_image', methods=['POST'])
def process_image():
    try:
        if 'image' not in request.files:
            print("No file part in the request.")
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['image']
        
        if file.filename == '':
            print("No selected file.")
            return jsonify({'error': 'No selected file'}), 400

        if file and allowed_file(file.filename):
            img = Image.open(file)
            uploaded_file_extension = os.path.splitext(file.filename)[1].lower()
        
        ratio = img.size[0] / 500.0
        img_np = np.array(img)
        original_img = img_np.copy()
        # converting image into grayscale
        gray = cv2.cvtColor(img_np, cv2.COLOR_BGR2GRAY)

        # blurring and finding edges of the image
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edged = cv2.Canny(gray, 75, 200)

        # applying threshold to grayscale image
        thresh = cv2.threshold(gray, 225, 255, cv2.THRESH_BINARY_INV)[1]

        # find contours
        contours = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = imutils.grab_contours(contours)

        # draw contours on image
        cv2.drawContours(img_np, contours, -1, (240, 0, 159), 3)

        H, W = img_np.shape[:2]
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            if cv2.contourArea(cnt) > 100 and (0.7 < w/h < 1.3) and (W/4 < x + w//2 < W*3/4) and (H/4 < y + h//2 < H*3/4):
                break

        # creating mask and performing bitwise-op
        mask = np.zeros(img_np.shape[:2], np.uint8)
        cv2.drawContours(mask, [cnt], -1, 255, -1)
        dst = cv2.bitwise_and(img_np, img_np, mask=mask)

        # displaying image and saving in the directory
        gray = cv2.cvtColor(dst, cv2.COLOR_BGR2GRAY)
        gray = cv2.medianBlur(gray, 3)
        gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
        scanned_file_name = "test"+ uploaded_file_extension
        cv2.imwrite(scanned_file_name, dst)

        file_text = pytesseract.image_to_string(scanned_file_name)
        print('resultat with pytseract',file_text)
        pytesseract_global_list = find_dates(file_text)
        print("Pytesseract Global List:", pytesseract_global_list)

        # Extend global_list with Tesseract OCR dates
        global global_list
        global_list.extend(pytesseract_global_list)
      
        # Assuming `detect` function is defined elsewhere
        detected_language = detect(file_text)
        print("Detected language:", detected_language)

        processed_filename = scanned_file_name
        processed_filepath = os.path.join(app.config['UPLOAD_FOLDER'], processed_filename)
        cv2.imwrite(processed_filepath, dst)
        print("Processed image saved at:", processed_filepath)
        
        return jsonify({'message': 'Image processed successfully', 'detected_language': detected_language}), 200
        
    except Exception as e:
        print(f"Error processing image: {e}")
        return jsonify({'error': 'Error processing image'}), 500

if __name__ == "__main__":
    app.run(debug=True)