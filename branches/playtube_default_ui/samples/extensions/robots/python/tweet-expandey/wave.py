#!/usr/bin/python2.4
import re
import logging

from waveapi import events
from waveapi import robot
from waveapi import element
from waveapi import ops
from waveapi import element
from waveapi import appengine_robot_runner

import twitter
import cred

tweetPattern = re.compile('(http://)?twitter.com/([A-Za-z0-9_]+)/statuses/(?P<statusID>\d{10})(/)?')
PROCESSED_KEY = 'appengine/tweet-expandey'

def OnBlipSubmitted(event, wavelet):
  blip = event.blip
  ExpandTweets(blip)

def OnSelfAdded(event, wavelet):
  blip = wavelet.root_blip
  ExpandTweets(blip)

def ExpandTweets(blip):
  # look for twitter URLs
  processed_annotations = blip.annotations.get(PROCESSED_KEY, [])
  tweets = []
  for tweet in tweetPattern.finditer(blip.text):
    logging.info('Found tweet %s' % tweet.group('statusID'))
    tweets.append(tweet)

  tweets.reverse()
  for tweet in tweets:
    if not CheckOverlap(processed_annotations, tweet):
      AppendTweet(blip, tweet.end(), tweet.group('statusID'))
      blip.range(tweet.start(),tweet.end()).annotate(PROCESSED_KEY, 'processed')

def CheckOverlap(annotations, match):
  for annotation in annotations:
    if annotation.start == match.start() and annotation.end >= match.end():
      return True
  return False

def AppendTweet(blip, start, tweetId):
  api = twitter.Api(cred.username, cred.password)
  status = api.GetStatus(tweetId)
  image = element.Image(status.user.profile_image_url)
  username = status.user.screen_name
  username_url = 'http://www.twitter.com/' + username
  text = status.text
  blip.append('...') #buffer
  blip.at(start).insert('\n')
  blip.at(start+1).insert(image)
  blip.at(start+3).insert(username + ': ' + text)
  blip.all(username + ': ').annotate('link/manual', username_url)

if __name__ == '__main__':
  removey = robot.Robot('Tweet Expandey',
      image_url='http://www.seoish.com/wp-content/uploads/2009/04/wrench.png',
      profile_url='')
  removey.register_handler(events.BlipSubmitted, OnBlipSubmitted)
  appengine_robot_runner.run(removey, debug=True)
