import logging
import os
import cgi

from google.appengine.ext import db
from google.appengine.api import memcache
from waveapi import events
from waveapi import robot
from waveapi import appengine_robot_runner 

import models
import blipconverter

def AddBlip(wavelet, string):
  wavelet.reply('\n').append(string)

def OnBlipSubmitted(event, wavelet):
  ExportRootBlip(wavelet)

def OnRobotAdded(event, wavelet):
  ExportRootBlip(wavelet)

def ExportRootBlip(wavelet):
  if wavelet.creator != 'pamela.fox@googlewave.com':
    logging.info('Uh oh, %s tried to make an FAQ.' % wavelet.creator)
    return

  wavelet.participants.add('google-wave-api-team@googlegroups.com')
  root_blip = wavelet.root_blip
  title = wavelet.title
  id = wavelet.wave_id
  body = root_blip.text.split('\n', 1)[1] # strip title
  html = blipconverter.ToHTML(root_blip)

  query = db.Query(models.FAQ)
  query.filter('id =', id)
  faq = query.get()
  new_faq = False
  if faq is None:
    new_faq = True
    AddBlip(wavelet, "Exported Wave to FAQ.")
    faq = models.FAQ()

  faq.id = id
  faq.title = title

  # Format: "FAQ:invites: How can I get invites?"
  split_title = title.split(':', 2)
  if len(split_title) >= 3:
    faq.short_id = split_title[1]
    faq.title = split_title[2]
    if new_faq:
      url = 'http://wave-api-faq.appspot.com/#%s' % faq.short_id
      AddBlip(wavelet, url)
  else:
    logging.warn('Could not find a short title. Exiting')
    return

  # Figure out if it's a TOC or FAQ
  if title.find('TOC') > -1:
    faq.type = 'toc'
    faq.order = 1
    faq.faqs = []
    # Find short IDs, map to keys, store in listproperty
    short_ids = []
    lines = body.split('\n')
    for line in lines:
      split_title = line.split(':', 2)
      if len(split_title) >= 2:
        short_id = split_title[1]
        short_ids.append(short_id)
    query = db.Query(models.FAQ)
    query.filter('shortId IN', short_ids)
    results = query.fetch(20)
    for result in results:
      faq.faqs.append(result.key())
  elif title.find('FAQ') > -1:
    faq.type = 'faq'
  else:
    logging.warn('Could not figure out if TOC or FAQ. Exiting')
    return

  faq.body = body
  faq.html = html
  faq.creator = wavelet.creator
  faq.participants = [p for p in wavelet.participants]
  faq.put()
  memcache.delete('mainpage')

if __name__ == '__main__':
  faqqy = robot.Robot('Wave API Faqqy',
                        image_url='http://code.google.com/apis/sketchup/images/faq.gif',
                        profile_url='http://wave-api-faq.appspot.com/')
  faqqy.register_handler(events.BlipSubmitted, OnBlipSubmitted)
  faqqy.register_handler(events.WaveletSelfAdded, OnRobotAdded)
  appengine_robot_runner.run(faqqy)
