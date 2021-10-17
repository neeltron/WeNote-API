from flask import Flask, request, redirect, jsonify
from werkzeug.utils import secure_filename
from flask_cors import CORS, cross_origin
from replit import db
import requests
import os
import random

app = Flask('app')
cors = CORS(app, resources={r"/input": {"origins": "*"}})
app.config['CORS_HEADERS'] = 'Content-Type'

app.secret_key = "jhgjhguy7iuh98h78989h976f756"
app.config['UPLOAD_FOLDER'] = "uploads/"
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

ALLOWED_EXTENSIONS = set(['mp4', 'mp3', 'wav'])

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
  info = [filename, response.json()['id']]
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
  return response.json()

@app.route('/')
def hello_world():
  return 'Hello, World!'

@app.route('/output')
def output():
  a = upload_audio("uploads/a.mp3")
  print(a)
  b = get_transcript(a)
  print(b)
  return b

@app.route('/input', methods = ['POST'])
def input():
  if 'file' not in request.files:
    resp = jsonify({'message' : 'No file part in the request'})
    return resp
  file = request.files['file']
  if file.filename == '':
    resp = jsonify({'message' : 'No file selected for uploading'})
    resp.status_code = 400
    return resp
  if file and allowed_file(file.filename):
    filename = secure_filename(file.filename)
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    resp = jsonify({'message' : 'File successfully uploaded'})
    resp.status_code = 201
    return resp
  else:
    resp = jsonify({'message' : 'Allowed file types are mp3, mp4, wav'})
    resp.status_code = 400
    return resp

app.run(host='0.0.0.0', port=8080) 
