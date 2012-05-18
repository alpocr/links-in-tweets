from collections import Counter
from django.http import HttpResponse
from django.shortcuts import render_to_response
from tweet.models import Tweet, Link
import Queue
import datetime
import json
import re
import requests
import threading

def all_tweets(username, max_id):
    url = "https://api.twitter.com/1/statuses/user_timeline.json?include_entities=true&screen_name=%s&count=200" % (username,)
    if max_id:
        url = url + "&max_id=" + str(max_id)
    tweets = json.loads(requests.get(url).text)
    return tweets

def all_links_in(tweet):
    r_links = re.compile(r"(http://[^ ]+)")
    links_in_tweet = set(r_links.findall(tweet.text))
    return list(links_in_tweet)

def all_tweets_since(username, since):
    tweets = []
    max_id = 0
    done = False
    while not done:
        for tweet in all_tweets(username, max_id):
            tweet['created_at'] = \
                datetime.datetime.strptime(tweet['created_at'], 
                                           '%a %b %d %H:%M:%S +0000 %Y')
            if tweet['created_at'] < since:
                done = True
                break
            tweets.append(tweet)
            max_id = tweet['id_str']
    return tweets

def anterior_jueves_4pm(now):
    _4PM = datetime.time(hour=16)
    _JUE = 3  # Monday=0 for weekday()
    old_now = now
    now += datetime.timedelta((_JUE - now.weekday()) % 7)
    now = now.combine(now.date(), _4PM)
    if old_now >= now:
        now += datetime.timedelta(days=7)
    now -= datetime.timedelta(days=14)
    return now


class LongLinkThread(threading.Thread):
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue

    def run(self):
        while True:
            url, link = self.queue.get()
            for _ in xrange(5): #Numero de intentos
                try:
                    response = requests.get(url).text
                    long_link = json.loads(response)['long-url']
                    link.long_link = long_link
                    link.save()
                    break
                except Exception, e:
                    pass
            self.queue.task_done()
            
def crawl_tweets_for(username, since):
    for tweet in all_tweets_since(username, since):
        try:
            tweet_record = Tweet.objects.get(tweet_id=tweet['id'])
            tweet_record.retweets = tweet['retweet_count']
        except Tweet.DoesNotExist:
            tweet_data = {
                      'tweet_id': tweet['id'],
                      'text': tweet['text'], 
                      'created_at': tweet['created_at'], 
                      'retweets': tweet['retweet_count'],
                   }
            tweet_record = Tweet(**tweet_data)
        tweet_record.save()
        
def crawl(request, username=None, year=None, month=None, day=None):
    crawl_tweets_for(username, datetime.datetime(int(year), int(month), int(day)))
    return HttpResponse("OK")

def extract_all_links(request):
    tweets = list(Tweet.objects.all().order_by('-retweets', '-created_at'))
    for tweet in tweets:
        for short_link in all_links_in(tweet):
            link, created = Link.objects.get_or_create(short_link=short_link, defaults={'long_link':""})
            link.save()
    return HttpResponse("OK")

def expand_all_links(request):
    links = list(Link.objects.all().filter(long_link__exact=""))
    for link in links:
        url = "http://api.longurl.org/v2/expand?&url=%s&format=json" % (link,)
        try:
            response = requests.get(url).text
            long_link = json.loads(response)['long-url']
            link.long_link = long_link
            link.save()
        except:
            pass
        
    return HttpResponse("OK")

def home(request):
    tweets = list(Tweet.objects.all().order_by('-retweets', '-created_at'))
    links = list(Link.objects.all())
    links = {link.short_link: link.long_link for link in links}
        
    response = []
    for tweet in tweets:
        links_in_tweet = all_links_in(tweet)
        links_in_tweet = map(lambda x: links[x], links_in_tweet)
        if links_in_tweet:
            response.append((tweet, links_in_tweet))
    response = {'tweets': response,}
    return render_to_response('home.html', response)