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
import text
import converter_ss
import util

from bitly import BitLy
import bitlycred

myrobot = None

BOLD = ('style/fontWeight', 'bold')
ITALIC = ('style/fontStyle', 'italic')

def SetupRobot():
  global myrobot
  myrobot = robot.Robot('Conference Bot')
  # Setup Oauth for domain of TOC wave
  myrobot.setup_oauth(wavecred.CONSUMER_KEY, wavecred.CONSUMER_SECRET,
    server_rpc_base=wavecred.RPC_BASE[wavecred.DOMAIN])

def SaveSessionInfo(wave_id, wavelet_id, toc_wave_id):
  SetupRobot()
  wave = myrobot.fetch_wavelet(wave_id, wavelet_id)
  session_id = wave.data_documents[wavedata.SESSION_ID]
  unique_id = toc_wave_id + session_id
  session_info = model.SessionInfo.get_or_insert(unique_id)
  session_info.id = session_id
  session_info.toc_wave = toc_wave_id
  session_info.title = wave.title
  session_info.wave_id = wave_id
  session_info.put()


# Post-creation operations
def AddGroup(wave_id, wavelet_id, group):
  SetupRobot()
  wave = myrobot.fetch_wavelet(wave_id, wavelet_id)
  wave.participants.add(group)
  myrobot.submit(wave)

def ReplaceText(wave_id, wavelet_id, target, dest):
  SetupRobot()
  wave = myrobot.fetch_wavelet(wave_id, wavelet_id)
  wave.root_blip.first(target).replace(dest)
  myrobot.submit(wave)

# Creation operations
def AddSessionTags(wave, session, conference):
  # Add session tags:
  for tag in session.tags:
    wave.tags.append(tag)

  # Add session hashtag
  if session.hashtag:
    wave.tags.append(session.hashtag.strip('#'))

def AddPublic(wave, conference):
  if conference.make_public:
    wave.participants.add('conference-waves@googlegroups.com')

def AddConferenceParticipants(wave, conference):
  for participant in conference.participants:
    wave.participants.add(participant)

def AddConferenceTags(wave, conference):
  wave.tags.append(conference.hashtag)
  # Add global tags
  for tag in conference.tags:
    wave.tags.append(tag)

def AddId(wave, session):
  if session.id:
    wave.data_documents[wavedata.SESSION_ID] = session.id

def ModBlip(blip, text, annotations=None):
  if not annotations:
    blip.append(text)
  else:
    blip.append(text, bundled_annotations=annotations)

def AddHeader(blip, text):
  ModBlip(blip, text + '\n', [BOLD])

def AddNewLine(blip):
  ModBlip(blip, '\n')

def AddTitle(wave, title):
  wave.title = title
  wave.root_blip.range(0, len(title)+1).annotate('style/fontSize', '1.5em')

  ModBlip(wave.root_blip, '\n', [('style/fontSize', None)])

def AddBackLink(wave, conference):
  # Add link back to main wave
  ModBlip(wave.root_blip, '\n')
  text = 'Back to %s Main Wave' % conference.name
  ModBlip(wave.root_blip, text, [('link/wave', conference.toc_wave)])

def AddInfoLine(blip, name, value):
  ModBlip(blip, name + ': ', [BOLD])
  ModBlip(blip, value  + '\n', [('style/fontWeight', None)])

def AddToTOC(session, conference_key, wave_id):
  SetupRobot()
  conference = model.Conference.get(conference_key)
  # Re-create TOC wave
  toc_wave = myrobot.blind_wavelet(conference.toc_wave_ser)
  blip = toc_wave.root_blip
  # Add link to main wave
  ModBlip(blip, element.Line(line_type='li', indent=1))
  ModBlip(blip, session.name, [('link/wave', wave_id)])
  ModBlip(blip, element.Line(line_type='li', indent=2))
  info_text = ' (%s, %s)' % (session.day, session.time)
  ModBlip(blip, info_text, [('link/wave', None), (wavedata.SESSION_ID, session.id)])
  myrobot.submit(toc_wave)


def AddSpeakers(blip, session):
  AddHeader(blip, text.SESSIONWAVE_SPEAKERS_HEADER)
  for i in range(len(session.speakers)):
    speaker = session.speakers[i]
    ModBlip(blip, speaker.name, [('link/manual', speaker.link)])
    if i != len(session.speakers)-1:
      ModBlip(blip, ', ', [('link/manual', None)])
  AddNewLine(blip)

def AddDescription(blip, session):
  ModBlip(blip, session.description)
  AddNewLine(blip)

def AddShortLink(blip, wave_id):
  wave_url = 'https://wave.google.com/wave/#restored:wave:%s' % wave_id
  wave_url = wave_url.replace('#', '%23')
  wave_url = wave_url.replace('+', '%252B')
  bitly = BitLy(bitlycred.LOGIN, bitlycred.KEY)
  short_url = bitly.shorten(wave_url)
  ModBlip(blip, short_url, [('link/manual', short_url),
                            ('style/fontSize', '1.5em')])
  ModBlip(blip, '\n', [('link/manual', None), ('style/fontSize', None)])


def AddLink(blip, session):
  if not session.link:
    return
  ModBlip(blip, 'More info on the website', [('link/manual', session.link)])
  ModBlip(blip, '\n', [('link/manual', None)])

def AddShortInfo(blip, session):
  info = '%s, at %s' % (session.day, session.time)
  if session.location:
    info = '%s, %s' % (info, session.location)
  ModBlip(blip, info)
  AddNewLine(blip)

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
  AddHeader(blip, text.SESSIONWAVE_ATTENDEES_HEADER)
  ModBlip(blip, element.Gadget(url='http://confrenzy.appspot.com/gadget_attendees.xml'))
  AddNewLine(blip)

def AddModerator(blip):
  AddHeader(blip, text.SESSIONWAVE_QUESTIONS_HEADER)
  ModBlip(blip, element.Gadget(url='http://confrenzy.appspot.com/gadget_moderator.xml'))
  AddNewLine(blip)

def AddLiveNotes(blip):
  AddHeader(blip, text.SESSIONWAVE_NOTES_HEADER)
  ModBlip(blip, text.SESSIONWAVE_NOTES_TEXT, [('style/fontWeight', None)])
  AddNewLine(blip)


def AddLinkToTOC(wave):
  if wavedata.LINK_ADDED not in wave.data_documents.keys():
    SetupRobot()
    conference = GetConferenceForNewWave(wave)
    # Add link to main wave
    blind_wave = myrobot.blind_wavelet(conference.toc_wave_ser,
                                       proxy_for_id=wavedata.MAIN_PROXY(conference))
    line = element.Line(line_type='li', indent=1)
    ModBlip(blind_wave.root_blip, line)
    ModBlip(blind_wave.root_blip, wave.title, [('link/wave', wave.wave_id),
                                               (wavedata.TOC_LINK(wave), '')])
    ModBlip(blind_wave.root_blip, element.Line(), [('link/wave', None)])

    myrobot.submit(blind_wave)
    wave.data_documents[wavedata.LINK_ADDED] = 'yes'


def MakeSessionWaves(conference):
  conf = None
  if conference.datasource_type == 'Spreadsheet':
    converter = converter_ss.SpreadsheetConverter(conference.datasource_url)
    conf = converter._conference
  if conf is None:
    logging.info('Error: Couldnt create conference object.')
    return
  for session in conf.sessions:
    deferred.defer(MakeSessionWave, session, conference.key())

def MakeTOCWave(admin_wave, conference):
  SetupRobot()
  conference_id = conference.key().id()
  toc_wave = myrobot.new_wave(domain=admin_wave.domain, submit=True,
                              participants=[conference.owner],
                              proxy_for_id=wavedata.MAIN_PROXY(conference))
  admin_wave.root_blip.first(element.Gadget).update_element({'wave_id':
                                                          toc_wave.wave_id})
  AddConferenceTags(toc_wave, conference)
  AddConferenceParticipants(toc_wave, conference)
  AddPublic(toc_wave, conference)

  AddTitle(toc_wave, conference.name + ' ' + text.MAINWAVE_TITLE)
  blip = toc_wave.root_blip
  AddHeader(blip, text.MAINWAVE_EXTENSION_HEADER)
  ModBlip(blip, text.MAINWAVE_EXTENSION_TEXT)
  installer = element.Installer(manifest=util.GetInstallerUrl(conference.key().id()))
  ModBlip(blip, installer)
  AddHeader(blip, text.MAINWAVE_WAVES_HEADER)
  ModBlip(blip, text.MAINWAVE_WAVES_TEXT)
  myrobot.submit(toc_wave)

  conference.toc_wave = toc_wave.wave_id
  conference.toc_wave_ser = simplejson.dumps(toc_wave.serialize())
  conference.put()

def MakeAdminWave(admin_wave, type='conference'):
  title = text.ADMINWAVE_TITLE
  if type == 'unconference':
    title = text.ADMINWAVE_UNTITLE
  AddTitle(admin_wave, title)
  gadget_url = '%s&type=%s' % (util.GetGadgetUrl(), type)
  gadget = element.Gadget(gadget_url)
  ModBlip(admin_wave.root_blip, gadget)

  conference = model.Conference()
  conference.owner = admin_wave.creator
  conference.type = type
  conference.admin_wave = admin_wave.wave_id
  conference.put()

def MakeTemplateWave(wave):
  conference = GetConferenceForNewWave(wave)
  blip = wave.root_blip

  wave.data_documents[wavedata.CONFERENCE_ID] = str(conference.key().id())

  AddConferenceTags(wave, conference)
  AddConferenceParticipants(wave, conference)
  AddPublic(wave, conference)

  if IsBlankWave(wave):
    MakeSessionTemplateWave(wave, conference)
  if IsEventWave(wave):
    MakeEventTemplateWave(wave, conference)

  AddBackLink(wave, conference)

  AddLinkToTOC(wave)

def MakeSessionTemplateWave(wave, conference):
  AddTitle(wave, conference.name + ' ' + text.SESSIONWAVE_TITLE)
  blip = wave.root_blip
  AddShortLink(blip, wave.wave_id)
  AddNewLine(blip)
  AddHeader(blip, text.SESSIONWAVE_TIME_HEADER)
  AddNewLine(blip)
  AddHeader(blip, text.SESSIONWAVE_LOCATION_HEADER)
  AddNewLine(blip)
  AddHeader(blip, text.SESSIONWAVE_DESCRIPTION_HEADER)
  AddNewLine(blip)
  AddHeader(blip, text.SESSIONWAVE_SPEAKERS_HEADER)
  AddNewLine(blip)
  AddAttendees(blip)
  AddLiveNotes(blip)

def MakeEventTemplateWave(wave, conference):
  AddTitle(wave, conference.name + ' ' + text.EVENTWAVE_TITLE)
  blip = wave.root_blip
  AddHeader(blip, text.EVENTWAVE_WHEN_HEADER)
  AddNewLine(blip)
  AddHeader(blip, text.EVENTWAVE_WHO_HEADER)
  ModBlip(blip, element.Gadget(url='http://wave-api.appspot.com/public/gadgets/areyouin/gadget.xml'))
  AddNewLine(blip)
  AddHeader(blip, text.EVENTWAVE_WHERE_HEADER)
  ModBlip(blip, element.Gadget(url='http://google-wave-resources.googlecode.com/svn/trunk/samples/extensions/gadgets/mappy/mappy.xml'))

def MakeNewWave(conference):
  # Create session wave
  try:
    participants = [conference.owner] + conference.participants
    new_wave = myrobot.new_wave(wavecred.DOMAIN, submit=True,
                                participants=participants)
    conference.all_session_waves.append(new_wave.wave_id)
    conference.main_session_waves.append(new_wave.wave_id)
    conference.put()
  except Exception, e:
    logging.info('Error creating new wave: %s' % str(e))
    return None
  return new_wave


def MakeSessionWave(session, conference_key):
  if not session.name:
    logging.info('Error: No name. Not making wave')
    return

  SetupRobot()
  conference = model.Conference.get(conference_key)

  # Wave mod
  new_wave = MakeNewWave(conference)
  new_wave.data_documents[wavedata.WAVE_TYPE] = 'live'
  AddId(new_wave, session)
  AddSessionTags(new_wave, session)
  AddConferenceTags(new_wave, conference)
  AddTitle(new_wave, 'Live Wave: ' + session.name)

  # Blip mod
  blip = new_wave.root_blip
  AddShortLink(blip, new_wave.wave_id)
  AddNewLine(blip)
  AddShortInfo(blip, session)
  AddDescription(blip, session)
  AddSpeakers(blip, session)
  AddLink(blip, session)
  AddNewLine(blip)
  AddSocialMedia(blip, session, new_wave.wave_id)
  AddAttendees(blip)
  AddModerator(blip)
  AddLiveNotes(blip)
  AddBackLink(new_wave, conference)

  # Discuss Blip
  reply_blip = new_wave.reply('\n')
  ModBlip(reply_blip, 'Discuss this session below this blip.', [ITALIC])

  # Submit all operations on new wave
  myrobot.submit(new_wave)

  # Add links to TOC wave
  deferred.defer(AddToTOC, session, conference.key(), new_wave.wave_id)

def UpdateWaveLink(wavelet):
  SetupRobot()
  should_update = False

  if wavedata.OLD_TITLE in wavelet.data_documents.keys():
    old_title = wavelet.data_documents[wavedata.OLD_TITLE]
    new_title = wavelet.title
    if new_title != old_title:
      should_update = True
  else:
    should_update = True

  if should_update:
    wavelet.data_documents[wavedata.OLD_TITLE] = wavelet.title
    conference_id = wavelet.data_documents[wavedata.CONFERENCE_ID]
    conference = model.Conference.get_by_id(int(conference_id))
    wavelet_id = wavelet.domain + '!conv+root'
    toc_wave = myrobot.fetch_wavelet(conference.toc_wave, wavelet_id,
                                     proxy_for_id=wavedata.MAIN_PROXY(conference))
    for annotation in toc_wave.root_blip.annotations:
      if annotation.name == wavedata.TOC_LINK(wavelet):
        start = annotation.start
        end = annotation.end
    toc_wave.root_blip.range(start, end).replace(wavelet.title,
        bundled_annotations=[('link/wave', wavelet.wave_id),
                             (wavedata.TOC_LINK(wavelet), '')])
    myrobot.submit(toc_wave)


def IsAdminWave(wavelet):
  return GetWaveType(wavelet).find('admin') > -1

def IsBlankWave(wavelet):
  return GetWaveType(wavelet).find('newwave-blank') > -1

def IsEventWave(wavelet):
  return GetWaveType(wavelet).find('newwave-event') > -1

def GetConferenceForNewWave(wavelet):
  proxy_for = GetWaveType(wavelet)
  id = proxy_for.split('-')[0]
  collection = model.Conference.get_by_id(int(id))
  return collection

def GetWaveType(wavelet):
  robot_address = wavelet.robot_address.split('@')[0]
  split_addy = robot_address.split('+')
  if len(split_addy) > 1:
    wave_type = split_addy[1]
  else:
    wave_type = ''
  logging.info('wave_type %s' % wave_type)
  return wave_type
