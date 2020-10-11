
from flask import Flask, render_template, request, redirect, jsonify
import requests
import json
import string
import random
import os
#from google.auth.transport import requests
#from google.cloud import datastore, storage

#datastore_client = datastore.Client()
app = Flask(__name__)

def randomStringDigits(stringLength=6):

    lettersAndDigits = string.ascii_letters + string.digits

    return ''.join(random.choice(lettersAndDigits) for i in range(stringLength))

def top_headlines_in_the_us():

    url = "https://newsapi.org/v2/top-headlines?country=us&apiKey={}".format(os.environ.get('NEWS_CRED'))

    payload = {}
    headers = {
      'Cookie': '__cfduid=d98e181a0aa46675c6bbdfcb1c90504731600977573'
    }

    response = requests.request("GET", url, headers=headers, data = payload).json()
    return response


def find_news_about_topic(query): #YYYY-MM-DD
    url = "https://newsapi.org/v2/everything?q={}&apiKey={}".fomat(query, os.environ.get('NEWS_CRED'))

    payload = {}
    headers = {
      'Cookie': '__cfduid=d98e181a0aa46675c6bbdfcb1c90504731600977573'
    }

    response = requests.request("GET", url, headers=headers, data = payload).json()
    return response


def get_stonks(symbol):
    url = "https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={}&apikey={}".format(symbol, os.environ.get('STONKS'))

    payload = {}
    headers= {}

    response = requests.request("GET", url, headers=headers, data = payload).json()
    return response

def scrape_content(url):
    querystring = {"timeout":"15000","paging":"false","fields":"text","url":url,"token":os.environ.get('SUPER_SCRAPER')}

    headers = {'x-rapidapi-host': "diffbot-diffbot.p.rapidapi.com",'x-rapidapi-key': os.environ.get('RAPID_API')}

    response = requests.request("GET", "https://api.diffbot.com/v3/article", headers=headers, params=querystring).json()

    if response.get("objects"):
        return response.get("objects")[0]['text']

    return ""

@app.route('/')
def root():
    return render_template("index.html")
    #jsonify({"status":"200"})


if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    # Flask's development server will automatically serve static files in
    # the "static" directory. See:
    # http://flask.pocoo.org/docs/1.0/quickstart/#static-files. Once deployed,
    # App Engine itself will serve those files as configured in app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
# [START gae_python37_render_template]
