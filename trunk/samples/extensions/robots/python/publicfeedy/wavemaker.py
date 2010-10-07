#!/usr/bin/python2.5
#
# Copyright 2009 Google Inc. Apache License 2.0

import logging
import os
import urllib
import random

from waveapi import robot
from waveapi import element
from google.appengine.ext import deferred
from django.utils import simplejson
from google.appengine.api import urlfetch

import credentials
import content

myrobot = None
domain = 'googlewave.com'

def SetupRobot():
  global myrobot
  myrobot = robot.Robot('Public Feedy')
  # Setup Oauth for domain of TOC wave
  myrobot.setup_oauth(credentials.CONSUMER_KEY, credentials.CONSUMER_SECRET,
    server_rpc_base=credentials.RPC_BASE[domain])


def MakeWave():
  SetupRobot()
  wave = myrobot.new_wave(domain=domain,
                          participants=['public@a.gwave.com'])
  FillWave(wave)
  myrobot.submit(wave)

def FillWave(wavelet):
  # grab youtube json
  url = 'http://gdata.youtube.com/feeds/api/standardfeeds/most_recent_Animals?alt=json'
  json = fetchJSON(url)
  entries = json['feed']['entry']
  num = random.randint(0, len(entries)-1)
  entry = entries[num]
  title = entry['title']['$t']
  descrip = entry['media$group']['media$description']['$t']
  logging.info(entry)
  id = entry['id']['$t']
  id = id.split('videos/')[1]
  gadget_url = 'http://everybodywave.appspot.com/gadget/WaveTube/main.xml'
  youtube_url = 'http://www.youtube.com/watch?v=%s' % id
  #maxage = '86400000'
  #size = '480x295'
  gadget_props = {'yturl': youtube_url}
  gadget = element.Gadget(url=gadget_url, props=gadget_props)
  wavelet.title = title
  wavelet.root_blip.append(descrip)
  wavelet.root_blip.append(gadget)
  msg = """Note: This wave contains a collaborative Youtube
viewing gadget, called WaveTube. If you do start watching
the video, it will share that with the other folks
watching the wave. Enjoy!"""
  wavelet.root_blip.append(msg)


def fetchJSON(url):
  logging.info('Fetching JSON for %s' % url)
  result = urlfetch.fetch(url)
  if result.status_code == 200:
    result_obj = simplejson.loads(result.content)
    return result_obj
  else:
    logging.info('Error retrieving JSON %s')
