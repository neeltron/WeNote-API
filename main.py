from flask import Flask
app = Flask('app')

import requests
import os
import sys
import time

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
  print(audio)
  endpoint = "https://api.assemblyai.com/v2/transcript"

  json = {
    "audio_url": audio
  }

  headers = {
    "authorization": os.environ["authorization"],
    "content-type": "application/json"
  }
  response = requests.post(endpoint, json=json, headers=headers)
  return response.json()

def get_transcript(response):
  endpoint = "https://api.assemblyai.com/v2/transcript/" + response
  headers = {
    "authorization": os.environ["authorization"],
  }
  response = requests.get(endpoint, headers=headers)
  return response.json()["text"]

@app.route('/')
def hello_world():
  return 'Hello, World!'

app.run(host='0.0.0.0', port=8080) 