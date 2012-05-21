from django.db import models

class UserTweet(models.Model):
    username = models.CharField(max_length=80)
    last_date_to_crawl = models.DateTimeField()
    
    def __str__(self):
        return "%s" % (self.username,)
    
    def __unicode__(self):
        return u"%s" % (self.__str__(),)
    

class Tweet(models.Model):
    tweet_id = models.BigIntegerField(primary_key=True)
    username = models.ForeignKey(UserTweet)
    created_at = models.DateTimeField()
    text = models.TextField(max_length=140)
    retweets = models.IntegerField()
    
    def __str__(self):
        return "%s" % (self.text,)
    
    def __unicode__(self):
        return u"%s" % (self.__str__(),)


class Link(models.Model):
    short_link = models.CharField(max_length=100, primary_key=True)
    long_link = models.CharField(max_length=256, blank=True)
    
    def __str__(self):
        return "%s %s" % (self.short_link, self.long_link)
    
    def __unicode__(self):
        return u"%s" % (self.__str__(),)