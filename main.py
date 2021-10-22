from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from flask_cors import CORS
from replit import db
import requests
import os
import random
import json
import time
from datetime import datetime
from nltk.corpus import stopwords
from nltk.cluster.util import cosine_distance
import numpy as np
import networkx as nx
import nltk

nltk.download('stopwords')
db.clear()
def read_article(text):
  textdata = text.splitlines()
  article = textdata[0].split(".")
  sentences = []
  for sentence in article:
    # print(sentence)
    sentences.append(sentence.replace("[^a-zA-Z]", " ").split(" "))
  sentences.pop()
  return sentences

def sentence_similarity(sent1, sent2, stopwords=None):
  if stopwords is None:
    stopwords = []
 
  sent1 = [w.lower() for w in sent1]
  sent2 = [w.lower() for w in sent2]
  all_words = list(set(sent1 + sent2))
  vector1 = [0] * len(all_words)
  vector2 = [0] * len(all_words)
  for w in sent1:
    if w in stopwords:
      continue
    vector1[all_words.index(w)] += 1

  for w in sent2:
    if w in stopwords:
      continue
    vector2[all_words.index(w)] += 1
  return 1 - cosine_distance(vector1, vector2)
 
def build_similarity_matrix(sentences, stop_words):
  similarity_matrix = np.zeros((len(sentences), len(sentences)))
  for idx1 in range(len(sentences)):
    for idx2 in range(len(sentences)):
      if idx1 == idx2:
        continue 
      similarity_matrix[idx1][idx2] = sentence_similarity(sentences[idx1], sentences[idx2], stop_words)

  return similarity_matrix


def generate_summary(text, top_n=5):
  stop_words = stopwords.words('english')
  summarize_text = []
  sentences =  read_article(text)
  sentence_similarity_martix = build_similarity_matrix(sentences, stop_words)
  sentence_similarity_graph = nx.from_numpy_array(sentence_similarity_martix)
  scores = nx.pagerank(sentence_similarity_graph, max_iter = 1000000)
  ranked_sentence = sorted(((scores[i],s) for i,s in enumerate(sentences)), reverse=True)    
  print("Indexes of top ranked_sentence order are ", ranked_sentence)    
  for i in range(top_n):
    summarize_text.append(" ".join(ranked_sentence[i][1]))
  summ =  ". ".join(summarize_text)
  return summ

app = Flask('app')
cors = CORS(app, resources={r"/input": {"origins": "*"}, r"/display": {"origins": "*"}})
app.config['CORS_HEADERS'] = 'Content-Type'

app.secret_key = "jhgjhguy7iuh98h78989h976f756"
app.config['UPLOAD_FOLDER'] = "uploads/"
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

ALLOWED_EXTENSIONS = set(['mp4', 'mp3', 'wav', 'webm'])

def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def upload_audio(path):
  filename = path
  def read_file(filename, chunk_size=5242880):
    with open(filename, 'rb') as _file:
      while True:
        data = _file.read(chunk_size)
        if not data:
          break
        yield data
  
  headers = {'authorization': os.environ["authorization"]}
  response = requests.post('https://api.assemblyai.com/v2/upload', headers=headers, data=read_file(filename))

  audio = response.json()["upload_url"]
  # print(audio)
  endpoint = "https://api.assemblyai.com/v2/transcript"

  json = {
    "audio_url": audio
  }

  headers = {
    "authorization": os.environ["authorization"],
    "content-type": "application/json"
  }
  response = requests.post(endpoint, json=json, headers=headers)
  ts = time.time()
  dt_object = datetime.fromtimestamp(ts)
  info = [filename, response.json()['id'], str(dt_object)]
  num = random.randint(0, 1000)
  db[str(num)] = info
  return str(num)

def get_transcript(num):
  a = db[str(num)][1]
  endpoint = "https://api.assemblyai.com/v2/transcript/" + a
  headers = {
    "authorization": os.environ["authorization"],
  }
  response = requests.get(endpoint, headers=headers)
  return response.json()['text']

@app.route('/')
def hello_world():
  return 'Hello, World!'

@app.route('/output')
def output():
  a = upload_audio("uploads/a.mp3")
  # print(a)
  b = get_transcript(a)
  # print(b)
  return b

@app.route('/display')
def display():
  notes = []
  for i in db:
    b = get_transcript(i)
    dict = {"note": b, "time": db[i][2]}
    notes.append(dict)
  data = json.dumps(notes)
  return data

@app.route('/summarize', methods = ["GET"])
def summarize():
  text = request.args.get('summ')
  note = generate_summary(text, 2)
  data = json.dumps(note)
  return data

@app.route('/input', methods = ['POST'])
def input():
  if 'file' not in request.files:
    resp = jsonify({'message' : 'No file part in the request'})
    # return resp
  file = request.files['file']
  if file.filename == '':
    resp = jsonify({'message' : 'No file selected for uploading'})
    resp.status_code = 400
  if file and allowed_file(file.filename):
    filename = secure_filename(file.filename)
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    resp = jsonify({'message' : 'File successfully uploaded'})
    resp.status_code = 201
    # return resp
  else:
    resp = jsonify({'message' : 'Allowed file types are mp3, mp4, wav'})
    resp.status_code = 400
    # return resp
  a = upload_audio("uploads/" + filename)
  print(filename)
  return a

a = upload_audio("uploads/a.mp3")
# print(a)
b = get_transcript(a)
# print(b)

app.run(host='0.0.0.0', port=8080) 
