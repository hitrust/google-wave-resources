#!/usr/bin/python2.5
#
# Copyright 2009 Google Inc. Apache License 2.0

import logging

from waveapi import robot
from waveapi import element
from waveapi import blip
import credentials

def logSomething(str):
  logging.info(str)

def makeWaveBlink(wavelet_ser, i):
  # Construct robot
  myrobot = robot.Robot('Blinky')

  # Construct wavelet
  wavelet = myrobot.blind_wavelet(wavelet_ser)

  # Setup Oauth
  myrobot.setup_oauth(credentials.CONSUMER_KEY, credentials.CONSUMER_SECRET,
    server_rpc_base=credentials.RPC_BASE[wavelet.domain])

  if i % 2 == 0:
    wavelet.root_blip.all().annotate(blip.Annotation.COLOR, '#FFFFFF')
  else:
    wavelet.root_blip.all().annotate(blip.Annotation.COLOR, '#000000')
  myrobot.submit(wavelet)
