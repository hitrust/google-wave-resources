import data
import os
import logging

from django.utils import simplejson
from google.appengine.api import urlfetch

import converter

class SpreadsheetConverter(converter.SourceConverter):
  def __init__(self, url):
    self._url = url
    self._json = None
    converter.SourceConverter.__init__(self)

  def getJSON(self):
    json = converter.fetchJSON(self._url)
    if 'feed' not in json:
      logging.info('JSON not well formed %s' % simplejson.dumps(json))
      return False
    self._json = json
    return True

  def createConference(self):
    self.getJSON()
    if not self._json:
      logging.info('Cant create')
      return
    self._conference  = data.Conference()
    talks = self._json['feed']['entry']
    for talk in talks:
      id = getSpreadsheetFieldValue(talk, 'sessionhashtag')
      day = getSpreadsheetFieldValue(talk, 'sessiondate')
      time = getSpreadsheetFieldValue(talk, 'sessiontime')
      location = 'Room #%s' % getSpreadsheetFieldValue(talk, 'room')
      talk_name = getSpreadsheetFieldValue(talk, 'sessiontitle')
      if talk_name:
        talk_name = talk_name.strip('\n')
      talk_link = getSpreadsheetFieldValue(talk, 'sessionlink')
      talk_description = getSpreadsheetFieldValue(talk, 'sessionabstract')
      talk_reqs = getSpreadsheetFieldValue(talk, 'sessionrequirements')
      waveid = getSpreadsheetFieldValue(talk, 'waveid')
      type = getSpreadsheetFieldValue(talk, 'sessiontype')
      track = getSpreadsheetFieldValue(talk, 'track')
      tags_raw = getSpreadsheetFieldValue(talk, 'tags')
      tags = []
      # Split comma separated list
      if tags:
        tags = tags.split(',')
      # Remove whitespace
      for tag in tags:
        tag = tag.strip()
 
      speakers = []
      speakers_raw = getSpreadsheetFieldValue(talk, 'sessionspeakers').split(',')
      for speaker in speakers_raw:
        speaker_name = speaker.strip()
        base_url = 'http://code.google.com/events/io/2010/speakers.html'
        speaker_link = '%s#%s' % (base_url, speaker_name.replace(' ', ''))
        speaker = data.Speaker(speaker_name, link=speaker_link)
        speakers.append(speaker)

      session = data.Session(id=id, day=day, time=time, location=location,
                             name=talk_name, link=talk_link, description=talk_description,
                             prereqs=talk_reqs, track=track, hashtag=id,
                             tags=tags, speakers=speakers, type=type,
                             waveid=waveid)
      self._conference.sessions.append(session)

def getSpreadsheetFieldValue(entry, field):
  field = 'gsx$' + field
  if field in entry:
    return entry[field]['$t']
  else:
    return None
