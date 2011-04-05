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
from google.appengine.api import urlfetch
from django.utils import simplejson

import model
import credentials

SESSION_ID = 'confrenzy/session/id'
WAVE_TYPE = 'confrenzy/wavetype'
myrobot = None
domain = 'googlewave.com'

def SetupRobot():
  global myrobot
  myrobot = robot.Robot('Conference Bot')
  # Setup Oauth for domain of TOC wave
  myrobot.setup_oauth(credentials.CONSUMER_KEY, credentials.CONSUMER_SECRET,
    server_rpc_base=credentials.RPC_BASE[domain])

def fetchJSON(url):
  logging.info('Fetching JSON for %s' % url)
  result = urlfetch.fetch(url)
  if result.status_code == 200:
    result_obj = simplejson.loads(result.content)
    return result_obj
  else:
    logging.info('Error retrieving JSON %s')
    return None

def SaveSessionInfo(wave_id, wavelet_id, toc_wave_id):
  SetupRobot()
  wave = myrobot.fetch_wavelet(wave_id, wavelet_id)
  if SESSION_ID not in wave.data_documents:
    logging.info('Couldnt find for %s' % wave_id)
    return
  session_id = wave.data_documents[SESSION_ID]
  logging.info(session_id)
  gadget_url = 'http://io2010-moderator.appspot.com/moderator_production.xml'
  gadget = wave.root_blip.first(element.Gadget, url=gadget_url)
  session_info = model.SessionInfo.get_or_insert(session_id)
  session_info.id = session_id
  session_info.title = wave.title
  if gadget:
    logging.info(gadget.topicId)
    session_info.moderator_id = gadget.topicId
    moderator_url = 'https://www.googleapis.com/moderator/v1/series/26864/topics/%s' % gadget.topicId
    json = fetchJSON(moderator_url)
    num_questions = json['data']['counters']['submissions']
    num_votes = json['data']['counters']['minusVotes'] + json['data']['counters']['plusVotes']
    session_info.num_questions = num_questions
    session_info.num_votes = num_votes

  session_info.wave_id = wave_id
  session_info.num_blips = len(wave.blips)
  num_participants = 0
  for p in wave.participants:
    if p.find('appspot') < 0:
      num_participants += 1
  session_info.num_participants = num_participants
  session_info.put()

def UpdateHashtag(wave_id, wavelet_id, group, new_hashtag):
  SetupRobot()
  wave = myrobot.fetch_wavelet(wave_id, wavelet_id)
  # pass in ss data

def RemoveGroup(wave_id, wavelet_id, group):
  SetupRobot()
  wave = myrobot.fetch_wavelet(wave_id, wavelet_id)
  wave.participants.remove(group)

def AddGroup(wave_id, wavelet_id, group):
  SetupRobot()
  wave = myrobot.fetch_wavelet(wave_id, wavelet_id)
  wave.participants.add(group)
  # Doesn't yet work with active API
  # wave.participants.set_role(group, wavelet.participants.ROLE_READ_ONLY)
  myrobot.submit(wave)

def FixLink(wave_id, wavelet_id):
  SetupRobot()
  wave = myrobot.fetch_wavelet(wave_id, wavelet_id)
  hashtag = wave.data_documents[SESSION_ID]
  link = 'http://www.google.com/search?q=%s&hl=en&tbs=mbl:1' % hashtag.replace('#', '%23')
  wave.root_blip.first(hashtag).annotate('link/manual', link)
  myrobot.submit(wave)


def FixBuzzLink(wave_id, wavelet_id):
  SetupRobot()
  wave = myrobot.fetch_wavelet(wave_id, wavelet_id)
  hashtag = wave.data_documents[SESSION_ID]
  wave_url = 'https://wave.google.com/wave/#restored:wave:%s' % wave_id.replace('+', '%252B')
  wave_url = wave_url.replace('#', '%23')
  title = wave.title.split(': ', 1)[1]
  buzz_message = 'Live wave-ing the "%s" session! %s' % (title,
                                                         hashtag.replace('#', '%23'))
  buzz_url = 'http://www.google.com/buzz/post?message=%s&url=%s' % (buzz_message, wave_url)
  wave.root_blip.first('Post to Google Buzz').annotate('link/manual', buzz_url)
  myrobot.submit(wave)


def MakeNotesWave(wave_id, wavelet_id):
  SetupRobot()
  # fetch live wave
  live_wave = myrobot.fetch_wavelet(wave_id, wavelet_id)
  if live_wave.root_blip.text.find('Live Notes!') < 1:
    return

  # create new wave
  participants = ['io2010-wave@googlegroups.com',
                  'io2010-notetakers@googlegroups.com',
                  'pamela.fox@googlewave.com']
  new_wave = myrobot.new_wave(domain, submit=True, participants=participants)
  new_wave.participants.set_role('io2010-wave@googlegroups.com',
                                 new_wave.participants.ROLE_READ_ONLY)
  title = live_wave.title.split(': ', 1)[1]
  new_wave.title = 'Live Notes: %s' % title
  new_wave.root_blip.append('A designated Googler will take notes as the session happens\n')
  new_wave.root_blip.append('Back to Live Wave',
                            bundled_annotations=[('link/wave', wave_id)])
  myrobot.submit(new_wave)
  # add link to live wave
  live_wave.root_blip.first('Live Notes!').replace(new_wave.title,
                                        bundled_annotations=[('link/wave',
                                                              new_wave.wave_id),
                                                             ('style/fontWeight',
                                                              'bold')])

  myrobot.submit(live_wave)


def MakeNewWave(collection):
  # Create session wave
  try:
    participants = [collection.owner] + collection.groups
    new_wave = myrobot.new_wave(domain, submit=True,
                                participants=participants)
    collection.all_session_waves.append(new_wave.wave_id)
    collection.main_session_waves.append(new_wave.wave_id)
    collection.put()
  except Exception, e:
    logging.info('Error creating new wave: %s' % str(e))
    return None
  return new_wave


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
    wave.data_documents[SESSION_ID] = session.id

def AddTitle(wave, title):
  wave.title = title 
  wave.root_blip.range(0, len(title)+1).annotate('style/fontSize',
                                                          '1.5em')

  wave.root_blip.append('\n', bundled_annotations=[('style/fontSize', None)])

def AddBackLink(wave, collection):
  # Add link back to main wave
  wave.root_blip.append('\n')
  text = 'Back to %s Main Wave' % collection.name
  wave.root_blip.append(text,
                            bundled_annotations=[('link/wave',
                                                  collection.toc_wave)])
def AddInfoLine(blip, name, value):
  blip.append(name + ': ', bundled_annotations=[('style/fontWeight', 'bold')])
  blip.append(value  + '\n', bundled_annotations=[('style/fontWeight', None)])

def MakeInfoWave(session, collection_key):
  if not session.name:
    logging.info('Error: No name. Not making wave')
    return

  SetupRobot()

  # Get collection object
  collection = model.Collection.get(collection_key)

  # Create session wave
  new_wave = MakeNewWave(collection)
  AddId(new_wave, session)
  new_wave.data_documents[WAVE_TYPE] = 'info'

  # Add content to session wave
  title = 'Google I/O 2010: %s' % session.name
  AddTitle(new_wave, title)

  # Add content
  blip = new_wave.root_blip
  blip.append(session.description + '\n')
  blip.append(element.Line(alignment='c'))
  blip.append('Have questions or want to discuss this session?',
              bundled_annotations=[('style/fontSize', '1.3em'),
                                   ('style/fontWeight', 'bold')])
  blip.append(element.Line(alignment='c'))
  blip.append('Join in on this wave', 
              bundled_annotations=[('style/fontSize', '1.3em'),
                                   ('style/fontWeight', 'bold')])
  blip.append('\n')
  blip.append(element.Line())
  blip.append('Speaker(s): ', bundled_annotations=[('style/fontWeight', 'bold')])
  for i in range(len(session.speakers)):
    speaker = session.speakers[i]
    blip.append(speaker.name, bundled_annotations=[('link/manual', speaker.link)])
    if i != len(session.speakers)-1:
      ModBlip(blip, ', ', [('link/manual', None)])

  blip.append('\n')
  AddInfoLine(blip, 'Time', session.time)
  AddInfoLine(blip, 'Day', session.day)
  AddInfoLine(blip, 'Location', session.location)
  blip.append('\n')
  AddInfoLine(blip, 'Session type', session.type)
  AddInfoLine(blip, 'Attendee requirements', session.prereqs)
  blip.append('\n')
  AddInfoLine(blip, 'Hashtag', session.hashtag)

  AddBackLink(new_wave, collection)
  AddTags(new_wave, session, collection)

  # Submit all operations on new wave
  myrobot.submit(new_wave)

  new_wave_ser = simplejson.dumps(new_wave.serialize())
  deferred.defer(MakeLiveWave, session, collection.key(), new_wave.wave_id,
                 new_wave_ser)

def AddToTOC(session, collection_key, session_wave_id, live_wave_id):
  SetupRobot()
  collection = model.Collection.get(collection_key)
  # Re-create TOC wave
  toc_wave = myrobot.blind_wavelet(collection.toc_wave_ser)
  blip = toc_wave.root_blip
  # Add link to main wave
  blip.append(element.Line(line_type='li', indent=1))
  blip.append(session.name, [('link/wave', None)])
  blip.append(element.Line(line_type='li', indent=2))
  ModBlip(blip, 'Info Wave', [('link/wave', session_wave_id)])
  ModBlip(blip, ' | ', [('link/wave', None)])
  ModBlip(blip, 'Live Wave', [('link/wave', live_wave_id)])
  info_text = ' (%s, %s)' % (session.time, session.location)
  ModBlip(blip, info_text, [('link/wave', None), (SESSION_ID, session.id)])
  myrobot.submit(toc_wave)

def ModBlip(blip, text, annotations=None):
  if not annotations:
    blip.append(text)
  else:
    blip.append(text, bundled_annotations=annotations)

def MakeLiveWave(session, collection_key, session_wave_id, session_wave_ser):
  SetupRobot()
  collection = model.Collection.get(collection_key)
  new_wave = MakeNewWave(collection)
  #new_wave = myrobot.fetch_wavelet(session.waveid,
  #                                'googlewave.com!conv+root')
  AddId(new_wave, session)
  new_wave.data_documents[WAVE_TYPE] = 'live'
  AddTitle(new_wave, 'Live Wave: ' + session.name)
  blip = new_wave.root_blip
  info = '%s, at %s, %s ' % (session.day, session.time, session.location)
  italic = ('style/fontStyle', 'italic')
  ModBlip(blip, info, [italic])
  ModBlip(blip, '(', [italic])
  ModBlip(blip, 'More Info', [italic, ('link/wave', session_wave_id)])
  ModBlip(blip, ')', [italic, ('link/wave', None)])
  ModBlip(blip, '\n', [('style/fontStyle', None)])
  search_url = 'http://www.google.com/search?q=%s&hl=en&tbs=mbl:1' % session.hashtag
  bold = ('style/fontWeight', 'bold')
  ModBlip(blip, session.hashtag, [bold, ('link/manual', search_url)])
  ModBlip(blip, ' | ', [bold, ('link/manual', None)])
  wave_url = 'https://wave.google.com/wave/#restored:wave:%s' % new_wave.wave_id
  status = 'Live wave-ing: %s %s' % (wave_url, session.hashtag)
  tweet_url = 'http://twitter.com/home?status=%s' % urllib.quote_plus(status)
  ModBlip(blip, 'Tweet This', [bold, ('link/manual', tweet_url)])
  ModBlip(blip, ' | ', [bold, ('link/manual', None)])
  buzz_message = 'Live wave-ing the "%s" session! %s' % (session.name,
                                                         session.hashtag)
  wave_url = 'https://wave.google.com/wave/#restored:wave:%s' % new_wave.wave_id.replace('+', '%252B')
  wave_url = wave_url.replace('#', '%23')
  title = new_wave.title.split(': ', 1)[1]
  buzz_message = 'Live wave-ing the "%s" session! %s' % (title,
                                                         session.hashtag.replace('#', '%23'))
  buzz_url = 'http://www.google.com/buzz/post?message=%s&url=%s' % (buzz_message, wave_url)
  ModBlip(blip, 'Post to Google Buzz', [bold, ('link/manual', buzz_url)])
  ModBlip(blip, '\n\n', [('link/manual', None)])
  ModBlip(blip, 'Attendees:\n', [bold])
  blip.append(element.Gadget(url='http://io2010-bot.appspot.com/gadget_attendees.xml'))
  ModBlip(blip, '\nQuestions:\n', [bold])
  gadget_url = 'http://io2010-moderator.appspot.com/moderator_production.xml'
  blip.append(element.Gadget(url=gadget_url))
  ModBlip(blip, '\n\nLive Notes:\n', [bold])
  live_notes_text = 'A designated Googler will be taking notes during this session, but feel free to join in below!\n\n'
  ModBlip(blip, live_notes_text, [('style/fontWeight', None),
                                  ('style/fontStyle', 'italic')])
  reply_blip = new_wave.reply('\n')
  ModBlip(reply_blip, 'Discuss this session below this blip.', [italic])

  AddTags(new_wave, session, collection)
  AddBackLink(new_wave, collection)

  # Submit all operations on new wave
  myrobot.submit(new_wave)

  # Add link for this wave to session wave
  session_wave = myrobot.blind_wavelet(session_wave_ser)
  session_wave.root_blip.first('Join in on this wave').annotate('link/wave',
                                                                new_wave.wave_id)
  myrobot.submit(session_wave)

  # Add links to TOC wave
  deferred.defer(AddToTOC, session, collection.key(), session_wave_id, new_wave.wave_id)


def RenderSession(session, session_template):
  if not session_template:
    session_template = 'default'
  template_filename = 'templates/_session_%s.html' % session_template
  template_values = {'session': session}
  if len(session.speakers) > 0:
    template_values['speaker'] = session.speakers[0]
  path = os.path.join(os.path.dirname(__file__), template_filename)
  return template.render(path, template_values)
