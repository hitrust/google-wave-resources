#!/usr/bin/python2.4
#
import logging

from waveapi import events
from waveapi import robot
from waveapi import element
from waveapi import ops
from waveapi import element
from waveapi import appengine_robot_runner
from google.appengine.ext import db

import models
import credentials

domain = 'wavesandbox.com'

def OnSelfAdded(event, wavelet):
  # Modify title
  wavelet.title = 'Ripple: '
  wavelet.participants.add('public@a.gwave.com')
  blip = wavelet.root_blip
  blip.append('\n\n\n')
  url = 'http://i-like-it.googlecode.com/svn/trunk/ILikeIt.xml'
  gadget = element.Gadget(url)
  blip.append(gadget)
  query = db.Query(models.Rippler)
  query.filter('user =', wavelet.creator)
  rippler = query.get()
  if rippler is None:
    rippler = models.CreateRippler(wavelet.creator)
    # create profile wave
    participants = ['public@a.gwave.com', wavelet.creator]
    profile_wave = robotty.new_wave(wavelet.domain, participants, submit=True)
    profile_wave.title = 'Profile for: %s' % wavelet.creator
    profile_wave.root_blip.append('Exciting profile info goes here.')
    url = 'http://ripple-bot.appspot.com/gadget_follow.xml'
    props = {'creator': wavelet.creator}
    gadget = element.Gadget(url, props)
    profile_wave.root_blip.append(gadget)
    profile_wave.submit_with(wavelet)
    rippler.profile_wave_id = profile_wave.wave_id
  rippler.num = rippler.num + 1
  rippler.put()
  start = len(blip.text)+len(wavelet.title)
  blip.append('Visit Profile  ')
  blip.range(start, start+6).annotate('link/wave', rippler.profile_wave_id)
  # Add to datastore
  ripple = models.Ripple()
  ripple.id = wavelet.wave_id
  SetRipple(ripple, wavelet)

def OnBlipSubmitted(event, wavelet):
  UpdateRipple(wavelet)

def OnParticipantsChanged(event, wavelet):
  UpdateRipple(wavelet)

def UpdateRipple(wavelet):
  query = db.Query(models.Ripple)
  query.filter('id =', wavelet.wave_id)
  ripple = query.get()
  if ripple is not None:
    SetRipple(ripple, wavelet)


def SetRipple(ripple, wavelet):
  ripple.title = wavelet.title
  ripple.body = wavelet.root_blip.text
  ripple.participants = [p for p in wavelet.participants]
  ripple.put()


if __name__ == '__main__':
  robotty = robot.Robot('The Rippler',
                        image_url='http://zaksiddons.files.wordpress.com/2008/03/ripple_effect.jpg',
                        profile_url='')
  robotty.set_verification_token_info(credentials.VERIFICATION_TOKEN, credentials.ST) 
  robotty.setup_oauth(credentials.CONSUMER_KEY, credentials.CONSUMER_SECRET,
                          server_rpc_base=credentials.RPC_BASE[domain])
  robotty.register_handler(events.WaveletSelfAdded, OnSelfAdded)
  robotty.register_handler(events.BlipSubmitted, OnBlipSubmitted)
  robotty.register_handler(events.WaveletParticipantsChanged, OnParticipantsChanged)
  appengine_robot_runner.run(robotty, debug=True)
