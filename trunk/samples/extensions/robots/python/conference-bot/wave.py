#!/usr/bin/python2.5
#
# Copyright 2009 Google Inc. Apache License 2.0

import cgi
import logging
import random

from waveapi import appengine_robot_runner
from waveapi import element
from waveapi import events
from waveapi import ops
from waveapi import robot
from django.utils import simplejson
from google.appengine.ext import deferred
from google.appengine.ext import webapp
from google.appengine.ext import db

import util
import text
import model
import converter_ss
import wavemaker
import wavedata
import wavecred

# the robot
myrobot = None

def MakeAdminWave(event, wavelet):
  wavelet.title = 'Admin Wave'
  gadget = element.Gadget(url=util.GetGadgetUrl())
  wavelet.root_blip.append(gadget)
  collection = model.ConferenceCollection()
  collection.owner = wavelet.creator
  collection.admin_wave = wavelet.wave_id
  collection.put()


def OnSelfAdded(event, wavelet):
  domain = wavelet.domain
  robot_address = wavelet.robot_address
  if IsAdminWave(wavelet):
    MakeAdminWave(event, wavelet)
    return
  proxy_for = GetWaveType(wavelet)
  id = proxy_for.split('-')[0]
  logging.info('id %s' % id)
  collection = model.ConferenceCollection.get_by_id(int(id))
  if collection.tags:
    wavelet.tags.append(collection.tags[0])
  if collection.groups:
    wavelet.participants.add(collection.groups[0])
  if collection.make_public:
    wavelet.participants.add('public@a.gwave.com')
  if IsBlankWave(wavelet):
    wavelet.title = collection.name + ' Wave: Topic'
    event.blip.append_markup(text.session_html) 
  if IsEventWave(wavelet):
    wavelet.title = collection.name + ' Event Wave: EventName'
    event.blip.append('\nWhen is it?\n\n')
    event.blip.append('Who\'s coming?\n')
    event.blip.append(element.Gadget(url='http://wave-api.appspot.com/public/gadgets/areyouin/gadget.xml'))
    event.blip.append('\n\n Where is it?')
    event.blip.append(element.Gadget(url='http://google-wave-resources.googlecode.com/svn/trunk/samples/extensions/gadgets/mappy/mappy.xml'))

def OnBlipSubmitted(event, wavelet):
  #if WAVE_TYPE in wavelet.data_documents.keys() and wavelet.data_documents[WAVE_TYPE] == 'info':
  #wavelet.participants.set_role(group, wavelet.participants.ROLE_READ_ONLY)

  if IsBlankWave(wavelet) or IsEventWave(wavelet):
    if wavedata.LINK_ADDED not in wavelet.data_documents.keys():
      SetupOauth(wavelet)
      id = GetWaveId(wavelet)
      # Get collection object
      collection = model.ConferenceCollection.get_by_id(int(id))

      # Add link to main wave
      blind_wave = myrobot.blind_wavelet(collection.toc_wave_ser)
      line = element.Line(line_type='li', indent=1)
      blind_wave.root_blip.append(line)
      blind_wave.root_blip.append(wavelet.title,
                                  bundled_annotations=[('link/wave', wavelet.wave_id)])
      myrobot.submit(blind_wave)
      wavelet.data_documents[wavedata.LINK_ADDED] = 'yes'

def OnGadgetChanged(event, wavelet):
  domain = wavelet.domain
  if IsAdminWave(wavelet):
    gadget = event.blip.first(element.Gadget, url=util.GetGadgetUrl())
    if gadget is None:
      logging.info('Error: No gadget found in Admin Wave.')
      return
    try:
      collection = GetCollectionForWave(wavelet)
    except:
      logging.info('Error: Couldnt retrieve collection.')
      return
    if collection is None:
      logging.info('Error: No collection found for Admin Wave.')
      return
    StoreGadgetChanges(wavelet, gadget, collection)
    create_main = gadget.get('createmain')
    if create_main == 'clicked' and collection.toc_wave is None:
      logging.info('toc %s' % str(collection.toc_wave))
      logging.info('Making new wave')
      MakeMainWave(wavelet, collection)
    create_sessions = gadget.get('createsessions')
    if create_sessions == 'clicked':
      MakeSessionWaves(collection)

def StoreGadgetChanges(wavelet, gadget, collection):
  collection.name = gadget.get('name')
  collection.icon = gadget.get('icon')
  make_public = gadget.get('public')
  collection.session_template = gadget.get('template')
  if make_public and make_public == 'on':
    collection.make_public = True
  #todo split CSV, make into proper list property
  groups = gadget.get('groups')
  if groups:
    collection.groups = [groups]
  tags = gadget.get('tags')
  if tags:
    collection.tags = [tags]
  collection.template = gadget.get('template')
  collection.datasource_type = gadget.get('datasource_type')
  collection.datasource_url = gadget.get('datasource_url')
  collection.put()

def MakeMainWave(wavelet, collection):
  SetupOauth(wavelet)
  new_wave = myrobot.new_wave(domain=wavelet.domain, submit=True,
                              participants=[collection.owner])
  new_wave.title = collection.name + ' Main Wave'
  blip = new_wave.root_blip
  blip.append_markup(text.main_html_2)
  installer = element.Installer(manifest=util.GetInstallerUrl(collection.key().id()))
  blip.append(installer)
  blip.append_markup(text.main_html)
  myrobot.submit(new_wave)

  collection.toc_wave = new_wave.wave_id
  collection.toc_wave_ser = simplejson.dumps(new_wave.serialize())
  collection.put()

def GetCollectionForWave(wavelet):
  query = model.ConferenceCollection.all()
  query.filter('admin_wave =', wavelet.wave_id)
  return query.get()

def MakeSessionWaves(collection):
  logging.info(collection.datasource_type)
  conf = None
  if collection.datasource_type == 'Spreadsheet':
    converter = converter_ss.SpreadsheetConverter(collection.datasource_url)
    conf = converter._conference
  if conf is None:
    logging.info('Error: Couldnt create conference object.')
    return
  for session in conf.sessions:
    deferred.defer(wavemaker.MakeSessionWave, session, collection.key())

def IsAdminWave(wavelet):
  return GetWaveType(wavelet).find('admin') > -1

def IsBlankWave(wavelet):
  return GetWaveType(wavelet).find('newwave-blank') > -1

def IsEventWave(wavelet):
  return GetWaveType(wavelet).find('newwave-event') > -1

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

def SetupOauth(wavelet):
  myrobot.setup_oauth(wavecred.CONSUMER_KEY, wavecred.CONSUMER_SECRET,
    server_rpc_base=wavecred.RPC_BASE[wavelet.domain])


class CronHandler(webapp.RequestHandler):
  robot  = None

  # override the constructor
  def __init__(self, robot):
    self.robot = robot
    webapp.RequestHandler.__init__(self)

  def get(self):
    query = db.Query(model.ConferenceCollection)
    wave = query.get()
    self.UpdateWave(wave)

  def UpdateWave(self, wave):
    wavelet = self.robot.blind_wavelet(wave.toc_wave_ser)
    self.robot.setup_oauth(wavecred.CONSUMER_KEY, wavecred.CONSUMER_SECRET, server_rpc_base=wavecred.RPC_BASE[wavelet.domain])
    num = random.randint(0, 999)
    wavelet.data_documents['robotupdated'] = str(num)
    self.robot.submit(wavelet)


class ProcessHandler(webapp.RequestHandler):
  robot = None

  # override the constructor
  def __init__(self, robot):
    self.robot = robot
    webapp.RequestHandler.__init__(self)

  def get(self):
    query = db.Query(model.ConferenceCollection)
    wave = query.get()
    self.ProcessWave(wave)

  def ProcessWave(self, wave):
    root_wavelet = wavecred.DOMAIN + '!conv+root'
    self.robot.setup_oauth(wavecred.CONSUMER_KEY,
                           wavecred.CONSUMER_SECRET,
                           server_rpc_base=wavecred.RPC_BASE[wavecred.DOMAIN])
    wavelet = self.robot.fetch_wavelet('googlewave.com!w+eRiTZrZkCcw',
                                       root_wavelet)
    # iterate through the annotations, finding the links
    blip = wavelet.root_blip
    for annotation in blip.annotations:
      if annotation.name == 'link/wave':
        text = blip.text[annotation.start:annotation.end]
        if text.find('Live') > -1:
          pass
          #deferred.defer(wavemaker.AddGroup, annotation.value, root_wavelet, group)
 
if __name__ == '__main__':

  myrobot = robot.Robot('Confrenzy',
                        image_url='http://dfki.de/~jameson/icon=conference.gif')
  myrobot.set_verification_token_info(wavecred.VERIFICATION_TOKEN, wavecred.ST)
  myrobot.register_handler(events.WaveletSelfAdded, OnSelfAdded)
  myrobot.register_handler(events.GadgetStateChanged, OnGadgetChanged)
  myrobot.register_handler(events.BlipSubmitted, OnBlipSubmitted)
  appengine_robot_runner.run(myrobot, debug=True, extra_handlers=[
      ('/_wave/cron', lambda: CronHandler(myrobot)),
      ('/_wave/process', lambda: ProcessHandler(myrobot))
      ])
