from flask import Flask, request, jsonify
import json
from flask_cors import CORS

from flask import Flask, jsonify
from flask_pymongo import PyMongo

import nltk
from nltk.corpus import words
from nltk.tokenize import word_tokenize

import re
import PyPDF2
import fitz
import pandas as pd
import json
from colory.color import Color
import math 
import numpy as np
from unidecode import unidecode
from bson.json_util import ObjectId

app = Flask(__name__)
CORS(app)

app.config['MONGO_URI']="mongodb://localhost:27017/hackathon"
mongo = PyMongo(app)

class MyEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return super(MyEncoder, self).default(obj)

app.json_encoder = MyEncoder
    
@app.route('/receive_data', methods=['POST'])
def receive_data():
    print("I am here ")
    received_data = request.get_json()
    print(received_data)
    result = get_most_recent_key_value(received_data)
    if is_greeting(received_data["text"]) and "start" not in received_data["text"]:
        response = respond_to_greeting(received_data["text"])
        response = {"text":response}
    else:
        doc = get_doc_internal()
        print(type(doc))
        print(received_data["text"])
        response = chatbot_agent(doc,received_data["text"])
        print(response)
        response = {"text":response}
    final_data = received_data
    return jsonify(response)

def get_most_recent_key_value(dictionary):
    most_recent_key_value = None

    for key, value in dictionary.items():
        if value:
            most_recent_key_value = (key, value[-1])

    return {most_recent_key_value[0]: most_recent_key_value[1]} if most_recent_key_value else {}

def get_topic_response(response):

  if type(response) == dict:
    list_data = ''
    for key, value in response.items():
      list_data += f"{key}:"
      for val in value.split("."):
        list_data += f"\n\t{val.strip()}"
      list_data += '\n'
  elif response:
    list_data = '\n\n'.join(f"{item.strip()}" for i, item in enumerate(response.split(".")))
  else:
    list_data = "No information we have for now. Sorry for the inconvenience. Please ask another question"

  return list_data

def chatbot_agent(input_dict, user_response):

  if 'start' in user_response.lower():
    list_data = '\n'.join(f"{i+1}. {item.strip()}" for i, item in enumerate(list(input_dict.keys())))
    return f"Thanks for starting the chat! \n \nHere are some of the things I can help you with: \n\n{list_data}\n\nSelect the name or number of the topic you want to understand"

  count = 0
  count_dict = {}
  for key in input_dict.keys():
    count += 1
    if user_response.lower() in key.lower():
      count_dict[count] = key

  if len(count_dict) > 1:
    list_data = f"We have {len(count_dict)} topics similar to this. Please select the number from the below list:\n"
    list_data += '\n'.join(f"{item}. {count_dict[item]}" for i, item in enumerate(list(count_dict.keys())))
    return list_data

  for key in input_dict.keys():
    if user_response.lower() in key.lower():
      try:
        res = input_dict[key]
      except:
        return "Please enter a valid topic name or number"


      list_data = get_topic_response(res)

      return list_data

  if user_response.isdigit() and int(user_response) <= len(input_dict):

    user_response = list(input_dict.keys())[int(user_response) - 1]

    if user_response not in input_dict:
      return "Please enter a valid topic name or number"
    res = input_dict[user_response]

    list_data = get_topic_response(res)

    return list_data
  else:
    return "Please enter a valid topic name or number"

def is_greeting(word):
    # Tokenize the word to handle cases like "good morning"
    tokens = word_tokenize(word.lower())
    
    # Check if any token is in the set of English words
    return any(token in english_words for token in tokens)

def respond_to_greeting(greeting):
    # Define responses based on the greeting
    responses = {
        "hello": "Hi there! how can i help you....Just say the magic word start. To start your training",
        "hi": "Hello! Just say the magic word start. To start your training" ,
        "hey": "Hey! Just say the magic word start. To start your training",
        "greetings": "Greetings!",
        "good morning": "Good morning!",
        "good afternoon": "Good afternoon!",
        "good evening": "Good evening!",
        "howdy": "Howdy!",
    }
    
    # Return the appropriate response or a default message
    return responses.get(greeting.lower(), "Nice to meet you!")

#=================================================================================================================================================================================
#PDF PROCESSING AND CODE CREATION STARTS HERE 

def extract_text_from_pdf(pdf_path):
    text = ""
    with open(pdf_path, "rb") as file:
        pdf_reader = PyPDF2.PdfReader(file)
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text()
    return text

def analyze_text_properties(path):
    doc = fitz.open(path)
    properties_list = []
    for page in doc:
        m = (page.get_text("dict", sort=True))
        json_data = json.dumps(m)
        distances = []
        for block in m["blocks"]:
            if block["type"] == 0:
                for line in block['lines']:
                    prev_block= None
                    for span in line["spans"]:
                        some_string = unidecode(span["text"].strip())
                        if some_string:
                            color_code = "#{:x}".format(span['color'])
                            if len(color_code) <= 6:
                                hex_code = color_code.lstrip('#')
                                # Normalize the hex code to six characters
                                color_code = f"#{hex_code:06}"
                            y0, y1 = span["bbox"][1],span['bbox'][3]
                            x0, x1 = span["bbox"][0],span['bbox'][2]
                            distance_covered = int(len(span["text"])*6.0)
                            if prev_block is not None:
                                space_after_sentence = y0 - prev_block["bbox"][3]  # Calculate space after sentence
                            else:
                                space_after_sentence = y0
                            prev_block = span
                            properties = {
                                "text": span["text"],
                                "font": span["font"],
                                "size": span["size"],
                                "color": Color(color_code).name,
                                "space":space_after_sentence,
                                "distance_covered":distance_covered,
                                "upper_case": span["text"].isupper(),
                                "lower_case": span["text"].islower()
                            }
                            distances.append(distance_covered)
                            properties_list.append(properties)

    doc.close()
    return properties_list, distances

def get_heading(path):
    pdf_path = path
    text_properties, distances = analyze_text_properties(pdf_path)

    df = pd.DataFrame(text_properties)
    # Set a threshold for small values
    small_value_threshold = 35

    # Filter small values
    filtered_data = [value for value in distances if value >= small_value_threshold]

    # Remove outliers using the IQR method
    q1 = np.percentile(filtered_data, 25)
    q3 = np.percentile(filtered_data, 75)
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr

    # Filter outliers
    final_data = [value for value in filtered_data if lower_bound <= value <= upper_bound]

    q2 = np.median(final_data)
    condition = df['distance_covered'] < q2

    condition2 = df['font'].str.contains("Bold")
    df_fil = df[(condition)&(condition2)]

    #sequence_column = 'order'

    is_in_sequence = (df_fil.index.to_series().diff() == 1)

    # Initialize an empty list to store arrays of indices
    result = []
    current_sequence = []

    # Iterate through the DataFrame's index and group consecutive indices
    for idx, in_sequence in zip(df_fil.index, is_in_sequence):
        if in_sequence:
            current_sequence.append(idx)
        else:
            # If not in sequence, append the current_sequence to the result and start a new sequence
            if current_sequence and len(current_sequence)>1:
                result.append([min(current_sequence), max(current_sequence)])
            elif current_sequence:
                result.append(current_sequence)
            current_sequence = [idx]

    
    if current_sequence and len(current_sequence)>1:
        result.append([min(current_sequence), max(current_sequence)])
    elif current_sequence:
        result.append(current_sequence)

    no_para = []
    for arr in result:
        if len(arr)>1:
            no_para.append(min(arr))
            
    merged_array = [item for sublist in result for item in sublist]
    final_headings = []
    for idx in merged_array:
        if idx in no_para:
            headin = df_fil.loc[idx]["text"] + "!NO_PARA"
            final_headings.append(headin)
        else:
            final_headings.append(df_fil.loc[idx]["text"])
    return final_headings

def extract_text_between_texts(pdf_path, start_text, end_text):
    doc = fitz.open(pdf_path)
    extracted_text = ""

    for page_num in range(doc.page_count):
        page = doc[page_num]
        text = page.get_text()

        # Find the starting and ending indices of the desired text
        start_index = text.find(start_text)
        end_index = text.find(end_text)

        # If both start_text and end_text are found on the page, extract the content
        if start_index != -1 and end_index != -1:
            content_between_texts = text[start_index:end_index]
            extracted_text += content_between_texts
            
    if not extracted_text:
        
        for page_num in range(doc.page_count):
            page = doc[page_num]
            text = page.get_text()
            pattern = re.compile(f'{re.escape(start_text)}(.*)', re.DOTALL)
            match = pattern.search(text)

            if match:
                extracted_text = match.group(1).strip()
                return extracted_text
            else:
                return None


    return extracted_text

@app.route('/pdf_data', methods=['POST'])
def pdf_data():
    # Replace 'your_document.pdf' with the actual path to your PDF document
    if 'pdfFile' in request.files:
        file = request.files['pdfFile']
    else:
        file = r"C:\Users\Hemanth_SnowRaider\Downloads\Computer_and_Health_docx.pdf"
    pdf_path = file 
    collection_name = 'computer_and_health'
    final_headings = get_heading(pdf_path)
    print(final_headings)
    final_story = {}
    test = {}
    for i in range(0,len(final_headings)):
        if i != len(final_headings)-1:
            # Specify the start and end texts for extraction
            start_text = final_headings[i].replace("!NO_PARA","")
            end_text = final_headings[i+1].replace("!NO_PARA","")
            
            # Extract the text between the specified texts
            extracted_text = extract_text_between_texts(pdf_path, start_text, end_text).replace("\n","")
            
            if "!NO_PARA" in final_headings[i]:
                final_story[extracted_text] = ""
            else:
                final_story[final_headings[i]] = extracted_text.replace(final_headings[i],"")
    if final_story:
        story = json.dumps(final_story)
        print(story)
        try:
            mongo.db[collection_name].insert_one(story)
        except Exception as e:
            print(f"Error inserting data: {e}")

        return jsonify(final_story)
    else:
         return {"No data":"please check your pdf path"}
def get_doc_internal():
    print("im in get_doc_internal")
    # Specify the name of the collection
    collection_name = 'computer_and_health'
    # Fetch all documents from the collection
    cursor = mongo.db[collection_name].find({})
    # Convert cursor to a list of dictionaries
    documents = list(cursor)
    documet = documents[0]
    if "_id" in documet:
        # Delete the key-value pair
        del documet["_id"]
    print(documet)
    data = json.dumps(documet)
    return documet

if __name__ == '__main__':
    
    # Check if NLTK corpora are downloaded, and download if necessary
    try:
        nltk.data.find('corpora/words.zip')
    except LookupError:
        nltk.download('words')
    
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt')
    
    # Get the set of English words from NLTK's words corpus
    english_words = set(words.words())
    
    app.run(debug=True)
