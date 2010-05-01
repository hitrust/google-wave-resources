#!/usr/bin/python2.5
#
# Copyright 2009 Google Inc. Apache License 2.0

import logging
import os
import urllib

from waveapi import robot
from waveapi import element
from google.appengine.ext.webapp import template
from google.appengine.ext import deferred
from django.utils import simplejson

import model
import wavecred
import wavedata

myrobot = None

BOLD = ('style/fontWeight', 'bold')
ITALIC = ('style/fontStyle', 'italic')

def SetupRobot():
  global myrobot
  myrobot = robot.Robot('Conference Bot')
  # Setup Oauth for domain of TOC wave
  myrobot.setup_oauth(wavecred.CONSUMER_KEY, wavecred.CONSUMER_SECRET,
    server_rpc_base=wavecred.RPC_BASE[wavecred.DOMAIN])

# Post-creation operations
def AddGroup(wave_id, wavelet_id, group):
  SetupRobot()
  wave = myrobot.fetch_wavelet(wave_id, wavelet_id)
  wave.participants.add(group)
  # Doesn't yet work with active API
  # wave.participants.set_role(group, wavelet.participants.ROLE_READ_ONLY)
  myrobot.submit(wave)

def ReplaceText(wave_id, wavelet_id, target, dest):
  SetupRobot()
  wave = myrobot.fetch_wavelet(wave_id, wavelet_id)
  wave.root_blip.first(target).replace(dest)
  myrobot.submit(wave)

# Creation operations

def AddTags(wave, session, collection):
  # Add session tags:
  for tag in session.tags:
    wave.tags.append(tag)

  # Add session hashtag
  wave.tags.append(session.hashtag.strip('#'))

  # Add global tags
  for tag in collection.tags:
    wave.tags.append(tag)

def AddId(wave, session):
  if session.id:
    wave.data_documents[wavedata.SESSION_ID] = session.id

def AddTitle(wave, title):
  wave.title = title
  wave.root_blip.range(0, len(title)+1).annotate('style/fontSize', '1.5em')

  ModBlip(wave.root_blip, '\n', [('style/fontSize', None)])

def ModBlip(blip, text, annotations=None):
  if not annotations:
    blip.append(text)
  else:
    blip.append(text, bundled_annotations=annotations)

def AddBackLink(wave, collection):
  # Add link back to main wave
  wave.root_blip.append('\n')
  text = 'Back to %s Main Wave' % collection.name
  ModBlip(wave.root_blip, text, [('link/wave', collection.toc_wave)])

def AddInfoLine(blip, name, value):
  ModBlip(blip, name + ': ', [BOLD])
  ModBlip(blip, value  + '\n', [('style/fontWeight', None)])

def AddToTOC(session, collection_key, wave_id):
  SetupRobot()
  collection = model.Collection.get(collection_key)
  # Re-create TOC wave
  toc_wave = myrobot.blind_wavelet(collection.toc_wave_ser)
  blip = toc_wave.root_blip
  # Add link to main wave
  blip.append(element.Line(line_type='li', indent=1))
  blip.append(session.name, [('link/wave', wave_id)])
  blip.append(element.Line(line_type='li', indent=2))
  info_text = ' (%s, %s)' % (session.time, session.location)
  ModBlip(blip, info_text, [('link/wave', None), (wavedata.SESSION_ID, session.id)])
  myrobot.submit(toc_wave)


def AddSpeakers(blip, session):
  ModBlip(blip, 'Speaker(s): ', [BOLD])
  for i in range(len(session.speakers)):
    speaker = session.speakers[i]
    ModBlip(blip, speaker.name, [('link/manual', speaker.link)])
    if i != len(session.speakers)-1:
      ModBlip(blip, ', ', [('link/manual', None)])
  ModBlip(blip, '\n')

def AddDescription(blip, session):
  ModBlip(blip, session.description)
  ModBlip(blip, '\n')

def AddShortInfo(blip, session):
  info = '%s, at %s' % (session.day, session.time)
  if session.location:
    info = '%s, %s' % (info, session.location)
  ModBlip(blip, info, [ITALIC])
  ModBlip(blip, '\n', [('style/fontStyle', None)])

def AddSocialMedia(blip, session, wave_id):
  if not session.hashtag:
    return
  search_url = 'http://www.google.com.au/search?hl=en&q=%s&aq=f&aqi=g-s1&aql=&oq=&gs_rfai=' % session.hashtag
  ModBlip(blip, session.hashtag, [BOLD, ('link/manual', search_url)])
  ModBlip(blip, ' | ', [BOLD, ('link/manual', None)])
  wave_url = 'https://wave.google.com/wave/#restored:wave:%s' % wave_id
  status = 'Live wave-ing: %s %s' % (wave_url, session.hashtag)
  tweet_url = 'http://twitter.com/home?status=%s' % urllib.quote_plus(status)
  ModBlip(blip, 'Tweet This', [BOLD, ('link/manual', tweet_url)])
  ModBlip(blip, ' | ', [BOLD, ('link/manual', None)])
  buzz_message = 'Live wave-ing the "%s" session! %s' % (session.name,
                                                         session.hashtag)
  buzz_url = 'http://www.google.com/buzz/post?message=%s&url=%s' % (buzz_message, wave_url)

  ModBlip(blip, 'Buzz This', [BOLD, ('link/manual', buzz_url)])
  ModBlip(blip, '\n\n', [('link/manual', None)])

def AddAttendees(blip):
  ModBlip(blip, 'Attendees:\n', [BOLD])
  blip.append(element.Gadget(url='http://confrenzy.appspot.com/gadget_attendees.xml'))
  ModBlip(blip, '\n')

def AddModerator(blip):
  ModBlip(blip, '\nQuestions:\n', [BOLD])
  gadget_url = 'http://confrenzy.appspot.com/gadget_moderator.xml'
  blip.append(element.Gadget(url=gadget_url))
  ModBlip(blip, '\n')

def AddLiveNotes(blip):
  ModBlip(blip, '\nLive Notes:\n', [BOLD])
  live_notes_text = 'It usually works best if a few people self-elect themselves as note-takers, and edit this bit with running notes.'
  ModBlip(blip, live_notes_text, [('style/fontWeight', None)])
  ModBlip(blip, '\n')

def MakeNewWave(collection):
  # Create session wave
  try:
    participants = [collection.owner] + collection.groups
    new_wave = myrobot.new_wave(wavecred.DOMAIN, submit=True,
                                participants=participants)
    collection.all_session_waves.append(new_wave.wave_id)
    collection.main_session_waves.append(new_wave.wave_id)
    collection.put()
  except Exception, e:
    logging.info('Error creating new wave: %s' % str(e))
    return None
  return new_wave


def MakeSessionWave(session, collection_key):
  if not session.name:
    logging.info('Error: No name. Not making wave')
    return

  SetupRobot()
  collection = model.Collection.get(collection_key)

  # Wave mod
  new_wave = MakeNewWave(collection)
  new_wave.data_documents[wavedata.WAVE_TYPE] = 'live'
  AddId(new_wave, session)
  AddTags(new_wave, session, collection)
  AddTitle(new_wave, 'Live Wave: ' + session.name)

  # Blip mod
  blip = new_wave.root_blip
  AddShortInfo(blip, session)
  AddSocialMedia(blip, session, new_wave.wave_id)
  AddAttendees(blip)
  AddModerator(blip)
  AddLiveNotes(blip)
  AddBackLink(new_wave, collection)

  # Discuss Blip
  reply_blip = new_wave.reply('\n')
  ModBlip(reply_blip, 'Discuss this session below this blip.', [ITALIC])

  # Submit all operations on new wave
  myrobot.submit(new_wave)

  # Add links to TOC wave
  deferred.defer(AddToTOC, session, collection.key(), new_wave.wave_id)
