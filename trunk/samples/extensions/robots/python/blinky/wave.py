#!/usr/bin/python2.5
#
# Copyright 2009 Google Inc. Apache License 2.0

import cgi
import logging

from waveapi import appengine_robot_runner
from waveapi import element
from waveapi import events
from waveapi import ops
from waveapi import robot
from google.appengine.ext import deferred

import credentials
import actions

domain='wavesandbox.com'

def OnSelfAdded(event, wavelet):
  wavelet.root_blip.append('Hello World')
  for i in range(21):
    deferred.defer(actions.makeWaveBlink, wavelet.serialize(), i, _countdown=i)

if __name__ == '__main__':

  myrobot = robot.Robot('Blinky',
                        image_url='http://media.giantbomb.com/uploads/0/3584/207911-1blinky_large.jpg')
  myrobot.register_handler(events.WaveletSelfAdded, OnSelfAdded)
  myrobot.set_verification_token_info(credentials.VERIFICATION_TOKEN, credentials.ST) 
  myrobot.setup_oauth(credentials.CONSUMER_KEY, credentials.CONSUMER_SECRET,
    server_rpc_base=credentials.RPC_BASE[domain])
  appengine_robot_runner.run(myrobot, debug=True)
