#!/usr/bin/python2.5
#
# Copyright 2009 Google Inc. Apache License 2.0

import cgi
import logging
import random

from waveapi import appengine_robot_runner
from waveapi import element
from waveapi import events
from waveapi import robot

import util
import model
import wavemaker
import wavecred

# the robot
myrobot = None
ROBOT_NAME = 'Confrenzy'
ROBOT_IMAGE = 'http://confrenzy.appspot.com/img/avatar.png'
ROBOT_PROFILE = {'name': ROBOT_NAME, 'imageUrl': ROBOT_IMAGE}

def OnSelfAdded(event, wavelet):
  if IsUnAdminWave(wavelet):
    wavemaker.MakeAdminWave(wavelet, type='unconference')
  elif IsAdminWave(wavelet):
    wavemaker.MakeAdminWave(wavelet)
  elif IsTemplateWave(wavelet):
    wavemaker.MakeTemplateWave(wavelet)

def OnBlipSubmitted(event, wavelet):
  # Add a link to the new wave with the title of this wave.
  # TODO: Listen to wave title changed, update title when that happens.
  if IsTemplateWave(wavelet):
    wavemaker.UpdateWaveLink(wavelet)

def OnGadgetChanged(event, wavelet):
  domain = wavelet.domain
  if IsAdminWave(wavelet):
    gadget = event.blip.first(element.Gadget)
    if gadget is None:
      logging.info('Error: No gadget found in Admin Wave.')
      return
    try:
      conference = GetConferenceForAdminWave(wavelet)
    except:
      logging.info('Error: Couldnt retrieve conference.')
      return
    if conference is None:
      logging.info('Error: No conference found for Admin Wave.')
      return
    StoreGadgetChanges(wavelet, gadget, conference)
    create_main = gadget.get('createmain')
    if create_main == 'clicked' and conference.toc_wave is None:
      wavemaker.MakeTOCWave(wavelet, conference)
      gadget.update_element({'createmain': None})
    create_sessions = gadget.get('createsessions')
    if create_sessions == 'clicked':
      wavemaker.MakeSessionWaves(conference)

def StoreGadgetChanges(wavelet, gadget, conference):
  conference.name = gadget.get('name')
  conference.icon = gadget.get('icon')
  make_public = gadget.get('public')
  conference.session_template = gadget.get('template')
  if make_public and make_public == 'on':
    conference.make_public = True
  #todo split CSV, make into proper list property
  participants = gadget.get('participants')
  if participants:
    participants = participants.split(',')
    conference.participants = participants
  tags = gadget.get('tags')
  if tags:
    tags = tags.split(',')
    conference.tags = tags
  hashtag = gadget.get('hashtag')
  if hashtag:
    conference.hashtag = hashtag
  conference.template = gadget.get('template')
  conference.datasource_type = gadget.get('datasource_type')
  conference.datasource_url = gadget.get('datasource_url')
  conference.put()

def GetConferenceForNewWave(wavelet):
  id = GetWaveId(wavelet)
  conference = model.Conference.get_by_id(int(id))
  return conference

def GetConferenceForAdminWave(wavelet):
  query = model.Conference.all()
  query.filter('admin_wave =', wavelet.wave_id)
  return query.get()

def IsAdminWave(wavelet):
  return GetWaveType(wavelet).find('admin') > -1

def IsUnAdminWave(wavelet):
  return GetWaveType(wavelet).find('unadmin') > -1

def IsBlankWave(wavelet):
  return GetWaveType(wavelet).find('newwave-blank') > -1

def IsEventWave(wavelet):
  return GetWaveType(wavelet).find('newwave-event') > -1

def IsTemplateWave(wavelet):
  return IsBlankWave(wavelet) or IsEventWave(wavelet)

def GetWaveType(wavelet):
  robot_address = wavelet.robot_address.split('@')[0]
  split_addy = robot_address.split('+')
  if len(split_addy) > 1:
    wave_type = split_addy[1]
  else:
    wave_type = ''
  logging.info('wave_type %s' % wave_type)
  return wave_type

def GetWaveId(wavelet):
  robot_address = wavelet.robot_address.split('@')[0]
  split_addy = robot_address.split('+')
  if len(split_addy) > 1:
    proxy = split_addy[1]
    split_proxy = proxy.split('-')
    id = split_proxy[0]
    logging.info('wave_id %s' % id)
    return id

def ProfileHandler(proxy_for_id):
  if proxy_for_id and proxy_for_id == 'unadmin':
    return ROBOT_PROFILE
  elif proxy_for_id:
    conference_id = proxy_for_id.split('-')[0]
    conference = model.Conference.get_by_id(int(conference_id))
    if conference:
      return {'name': conference.name,
            'imageUrl': conference.icon}
  return ROBOT_PROFILE


if __name__ == '__main__':
  myrobot = robot.Robot(ROBOT_NAME,
                        image_url=ROBOT_IMAGE)
  myrobot.register_handler(events.WaveletSelfAdded, OnSelfAdded)
  myrobot.register_handler(events.GadgetStateChanged, OnGadgetChanged)
  myrobot.register_handler(events.BlipSubmitted, OnBlipSubmitted)
  myrobot.register_profile_handler(ProfileHandler)
  appengine_robot_runner.run(myrobot, debug=True)
