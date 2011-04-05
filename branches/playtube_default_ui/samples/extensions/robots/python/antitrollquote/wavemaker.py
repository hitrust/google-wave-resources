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

import credentials
import content

myrobot = None
domain = 'googlewave.com'

def SetupRobot():
  global myrobot
  myrobot = robot.Robot('Guessing Game')
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
  num = random.randint(0, len(content.quotes)-1)
  quote = content.quotes[num]
  wavelet.title = 'Guess the quote!'
  wavelet.root_blip.append(quote['quote'] + ' (' + str(quote['year']) + ')')
