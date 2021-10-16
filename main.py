from flask import Flask
app = Flask('app')

import requests
import os

endpoint = "https://api.assemblyai.com/v2/transcript"

json = {
  "audio_url": "https://s3-us-west-2.amazonaws.com/blog.assemblyai.com/audio/8-7-2018-post/7510.mp3"
}

headers = {
    "authorization": os.environ['authorization'],
    "content-type": "application/json"
}

response = requests.post(endpoint, json=json, headers=headers)

print(response.json())



@app.route('/')
def hello_world():
  return 'Hello, World!'

app.run(host='0.0.0.0', port=8080) 