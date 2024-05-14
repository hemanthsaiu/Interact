# -*- coding: utf-8 -*-
"""
Created on Wed Jan 17 09:40:39 2024

@author: Hemanth_SnowRaider
"""

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


@app.route('/get_data', methods=['GET'])
def get_data():
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
    
    return jsonify(documet)

if __name__ == '__main__':
    app.run(debug=True,port=2500)