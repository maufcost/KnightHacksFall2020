from google.cloud import language
from google.cloud.language import enums
from google.cloud.language import types
import os
import time
import requests
import json
import string

client = language.LanguageServiceClient()

def top_headlines_in_the_us():

    url = "https://newsapi.org/v2/top-headlines?country=us&apiKey={}".format(os.environ.get('NEWS_CRED'))

    payload = {}
    headers = {
      'Cookie': '__cfduid=d98e181a0aa46675c6bbdfcb1c90504731600977573'
    }

    response = requests.request("GET", url, headers=headers, data = payload).json()
    return response


def get_stonks(symbol, ci):
    api = ["5256OPPTA7UOSJJW","U8NDN89P92V2FZ51","HS4NIZGQRTMHYFUA", "9BRL22J8LE1CSUQE"]
    url = "https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={}&apikey={}".format(symbol, api[ci%4] )

    payload = {}
    headers= {}

    response = requests.request("GET", url, headers=headers, data = payload).json()
    return response

def find_news_about_topic(query, time_q): #YYYY-MM-DD
    url = "https://newsapi.org/v2/everything?q={}&{}&language=en&sortBy=popularity&apiKey={}".format(query, time_q, os.environ.get('NEWS_CRED'))

    payload = {}
    headers = {
      'Cookie': '__cfduid=d98e181a0aa46675c6bbdfcb1c90504731600977573'
    }

    response = requests.request("GET", url, headers=headers, data = payload).json()
    return response


def gcp_sentiment_analysis(text):

    document = types.Document(content=text, type=enums.Document.Type.PLAIN_TEXT)

    sentiment = client.analyze_sentiment(document=document).document_sentiment

    print("Text: {}".format(text))
    print("Sentiment: {}, {}".format(sentiment.score, sentiment.magnitude))

    return [sentiment.score, sentiment.magnitude]
    #from google.auth.transport import requests

def parse_news_result(news_response_obj):

    list_of_articles = []
    temp_list = news_response_obj.get("articles")
    if temp_list == None:
        return []
    i = 0
    for each_article in temp_list:
        if i > 15:
            break
        else:
            if each_article.get("description") == None:
                continue
            new_article_object = {}
            new_article_object['title'] = each_article['title']
            new_article_object['desc'] = each_article['description']
            list_of_articles.append(new_article_object)
            i += 1

    return list_of_articles

def start_the_madness(list_names, list_tickers, date_q, time_s):
    fout = open("magic-file.txt",'w')

    csv = "company,ticker,negative,neutral,positive,netsent,stockb,stocka,category\n"

    for i in range(len(list_names)):
        stonks_data = get_stonks(list_tickers[i], i)
        time.sleep(5)

        for date_index in range(len(date_q)):
            positive = 0
            negative = 0
            neutral = 0
            net_sentiment_batch = 0
            list_of_articles = parse_news_result(find_news_about_topic(list_names[i], date_q[date_index]))

            for each_article in list_of_articles:
                result = gcp_sentiment_analysis(each_article['desc'])
                if result[0] >= -0.25 and result[0] <= 0.19:
                    neutral += 1
                elif result[0] > 0.19:
                    positive += 1
                elif result[0] < -0.25:
                    negative += 1

                net_sentiment_batch += result[0]*result[1]

            csv += "{},{},{},{},{},{},".format(list_names[i], list_tickers[i], negative, neutral, positive, net_sentiment_batch)


            end = time_s[date_index][0]
            start = time_s[date_index][1]

            price_high_end = stonks_data.get("Time Series (Daily)").get(end).get("2. high")
            price_high_start = stonks_data.get("Time Series (Daily)").get(start).get("2. high")

            csv += "{},{},".format(price_high_start, price_high_end)

            if price_high_end > price_high_start:
                csv += "Increase\n"
            else:
                csv += "Decrease\n"

            print(csv)
            fout.write(csv)




fin = open("base_in.txt","r")
ticker = []
name = []
date_queries = ['from=2020-10-03&to=2020-10-10','from=2020-09-27&to=2020-10-03','from=2020-09-20&to=2020-09-27','from=2020-09-13&to=2020-09-20']
time_series = [["2020-10-09", "2020-10-02"],['2020-10-02','2020-09-28'], ['2020-09-28', '2020-09-21'], ['2020-09-21', '2020-09-14']]

for each_line in fin:
    ticker.append(each_line.rstrip().split(",")[0])
    name.append(each_line.rstrip().split(",")[1])

# start_name = ['Apple']
# start_ticker= ['AAPL']

start_the_madness(name, ticker, date_queries, time_series)

fin.close()
