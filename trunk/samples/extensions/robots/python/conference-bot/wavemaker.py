#!/usr/bin/python2.5
#
# Copyright 2009 Google Inc. Apache License 2.0

import logging
import os

from waveapi import robot
from waveapi import element
from google.appengine.ext.webapp import template

import model
import credentials

SESSION_ID = 'confrenzy/session/id'

def MakeSessionWave(session, collection_key):
  # Construct robot
  myrobot = robot.Robot('Conference Bot')

  # Get collection object
  collection = model.Collection.get(collection_key)

  # Re-create TOC wave
  toc_wave = myrobot.blind_wavelet(collection.toc_wave_ser)

  # Setup Oauth for domain of TOC wave
  myrobot.setup_oauth(credentials.CONSUMER_KEY, credentials.CONSUMER_SECRET,
    server_rpc_base=credentials.RPC_BASE[toc_wave.domain])

  # Create session wave
  try:
    participants = [collection.owner] + collection.groups
    new_wave = myrobot.new_wave(toc_wave.domain, submit=True,
                                participants=participants)
    collection.session_waves.append(new_wave.wave_id)
    collection.put()
  except Exception, e:
    logging.info('Error creating new wave: %s' % str(e))
    return None

  # Add content to session wave
  new_wave.title = session.name.replace('\n', '')
  markup = renderSession(session, collection.session_template)
  new_wave.root_blip.append_markup(markup)
  #new_wave.root_blip.append(element.Image(url='http://imagine-it.org/google/wave/jonsifooter.png'))

  if session.id:
    new_wave.data_documents[SESSION_ID] = session.id
  # Add link back to main wave
  #new_wave.root_blip.append('\n')
  #new_wave.root_blip.append('Back to Main Wave',
  #                          bundled_annotations=[('link/wave',
  #                                                collection.toc_wave)])

  # Add tags
  for tag in collection.tags:
    new_wave.tags.append(tag)

  # Submit all operations on new wave
  myrobot.submit(new_wave)

  # Add link to main wave
  line = element.Line(line_type='li', indent=1)
  toc_wave.root_blip.append(line)
  toc_wave.root_blip.append(session.name, bundled_annotations=[('link/wave', new_wave.wave_id)])
  myrobot.submit(toc_wave)

def renderSession(session, session_template):
  if not session_template:
    session_template = 'default'
  template_filename = 'templates/_session_%s.html' % session_template
  template_values = {'session': session}
  if len(session.speakers) > 0:
    template_values['speaker'] = session.speakers[0]
  path = os.path.join(os.path.dirname(__file__), template_filename)
  return template.render(path, template_values)
