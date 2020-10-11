
from flask import Flask, render_template, request, redirect, jsonify
import requests
import json
import string
import random
import os
from google.cloud import language
from google.cloud.language import enums
from google.cloud.language import types
from google.cloud import automl_v1beta1 as automl
import yfinance as yf

# Instantiates a client
client = language.LanguageServiceClient()

#from google.cloud import datastore, storage

#datastore_client = datastore.Client()
app = Flask(__name__)

def predict_model(object_with_all_inputs):
    # TODO(developer): Uncomment and set the following variables
    project_id = 'newsbank-knight'
    compute_region = 'us-central1'
    model_display_name = 'stonknews'
    inputs = object_with_all_inputs #{'value': 3, ...}

    client = automl.TablesClient(project=project_id, region=compute_region)
    feature_importance = False
    if feature_importance:
        response = client.predict(
            model_display_name=model_display_name,
            inputs=inputs,
            feature_importance=True,
        )
    else:
        response = client.predict(
            model_display_name=model_display_name, inputs=inputs
        )

    print("Prediction results:")
    correct_label = ""
    confidence = 0
    for result in response.payload:
        if result.tables.score > confidence:
            confidence = result.tables.score
            correct_label = result.tables.value.string_value
        print("Predicted class name: {}".format(result.tables.value))
        print("Predicted class score: {}".format(result.tables.score))

    return [correct_label, confidence]

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
    url = "https://newsapi.org/v2/everything?q={}&from=2020-10-01&language=en&sortBy=relevancy&apiKey={}&excludeDomains=reuters.com".format(query, os.environ.get('NEWS_CRED'))

    payload = {}
    headers = {
      'Cookie': '__cfduid=d98e181a0aa46675c6bbdfcb1c90504731600977573'
    }

    response = requests.request("GET", url, headers=headers, data = payload).json()
    return response


def get_stonks(symbol):
    api = ["5256OPPTA7UOSJJW","U8NDN89P92V2FZ51","HS4NIZGQRTMHYFUA", "9BRL22J8LE1CSUQE"]

    url = "https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={}&apikey={}".format(symbol, random.choice(api))

    payload = {}
    headers= {}

    response = requests.request("GET", url, headers=headers, data = payload).json()
    return response

def scrape_content(url):
    querystring = {"timeout":"15000","paging":"false","fields":"text","url":url,"token":os.environ.get('SUPER_SCRAPER')}

    headers = {'x-rapidapi-host': "diffbot-diffbot.p.rapidapi.com",'x-rapidapi-key': os.environ.get('RAPID_API')}

    response = requests.request("GET", "https://api.diffbot.com/v3/article", headers=headers, params=querystring).json()

    if response.get("objects"):
        return response.get("objects")[0]['text'] #response.get("objects")[0]['sentiment'] --> We will use GCP INSTEAD

    return ""

def gcp_sentiment_analysis(text):
    document = types.Document(content=text, type=enums.Document.Type.PLAIN_TEXT)

    sentiment = client.analyze_sentiment(document=document).document_sentiment

    print("Text: {}".format(text))
    print("Sentiment: {}, {}".format(sentiment.score, sentiment.magnitude))

    return [sentiment.score, sentiment.magnitude]
    #from google.auth.transport import requests

def get_name(symbol):
    url = "http://d.yimg.com/autoc.finance.yahoo.com/autoc?query={}&region=1&lang=en".format(symbol)

    result = requests.get(url).json()

    for x in result['ResultSet']['Result']:
        if x['symbol'] == symbol:
            return x['name']


def parse_news_result(news_response_obj):
    title_that_went = []

    list_of_articles = []
    temp_list = news_response_obj.get("articles")

    if temp_list == None:
        return []
    i = 0
    for each_article in temp_list:
        if i > 25:
            break
        else:
            if each_article.get("description") == None:
                continue
            new_article_object = {}
            new_article_object['title'] = each_article['title']
            new_article_object['desc'] = each_article['description']
            new_article_object['img'] = each_article.get('urlToImage')
            if (not each_article['title'] in title_that_went) and (not "Reuters" in each_article['title']):
                list_of_articles.append(new_article_object)
                title_that_went.append(each_article['title'])
                i += 1

    return list_of_articles

@app.route('/')
def root():
    return render_template("index.html")
    #jsonify({"status":"200"})

@app.route('/analyze')
def analyze():
    query = request.args.get("q")

    company_name = get_name(query)
    stonks = get_stonks(query)

    most_recent_high = stonks.get("Time Series (Daily)").get("2020-10-09").get("2. high")
    previous_week_high = stonks.get("Time Series (Daily)").get("2020-10-02").get("2. high")

    all_news_related = parse_news_result(find_news_about_topic(company_name))
    neg, neu, pos, netsent = [0,0,0,0]

    for each_new in all_news_related:
        result = gcp_sentiment_analysis(each_new['desc'])
        each_new['res'] = result[0]*result[1]
        if result[0] > 0.19:
            pos += 1
        elif result[0] > -0.25:
            neu += 1
        else:
            neg += 1

        netsent += result[0]*result[1]

    obj = {'negative':neg, 'netsent':netsent, 'neutral':neu, 'positive':pos, 'stocka':most_recent_high, 'stockb': previous_week_high}

    result_model = predict_model(obj)

    result_model[1] = round(result_model[1] * 100, 2)

    label = ""
    if result_model[0] == "Increase":
        label = "> ${}".format(most_recent_high)
    if result_model[0] == "Decrease":
        label = "${} <".format(most_recent_high)


    #Output = 'Microsoft Corporation'
    return render_template("table.html", company=company_name, prediction=result_model, news=all_news_related, details=obj, label=label)
    #jsonify({"status":"200"})

@app.route('/US')
def us_analyze():
    all_news_related = parse_news_result(top_headlines_in_the_us())

    neg, neu, pos, netsent = [0,0,0,0]

    for each_new in all_news_related:
        result = gcp_sentiment_analysis(each_new['desc'])
        each_new['res'] = result[0]*result[1]
        if result[0] > 0.19:
            pos += 1
        elif result[0] > -0.25:
            neu += 1
        else:
            neg += 1

            netsent += result[0]*result[1]

    obj = {'negative':neg, 'netsent':netsent, 'neutral':neu, 'positive':pos}
    return render_template("US.html", news=all_news_related, details=obj)


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
