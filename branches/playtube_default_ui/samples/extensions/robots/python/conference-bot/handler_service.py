#!/usr/bin/python2.4
#
# Copyright 2010 Google Inc. All Rights Reserved.
import logging
import os

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from django.utils import simplejson

from waveapi import robot

import util
import model
import wavecred

class RobotServiceHandler(webapp.RequestHandler):
  robot = None

  def __init__(self):
    self.robot = robot.Robot('Conference Bot')
    self.robot.setup_oauth(wavecred.CONSUMER_KEY, wavecred.CONSUMER_SECRET,
      server_rpc_base=wavecred.RPC_BASE[wavecred.DOMAIN])
    webapp.RequestHandler.__init__(self)

class CronHandler(RobotServiceHandler):
  def __init__(self, robot):
    RobotServiceHandler.__init__(self)

  def get(self):
    query = db.Query(model.Conference)
    wave = query.get()
    self.UpdateWave(wave)

  def UpdateWave(self, wave):
    import random

    wavelet = self.robot.blind_wavelet(wave.toc_wave_ser)
    num = random.randint(0, 999)
    wavelet.data_documents['robotupdated'] = str(num)
    self.robot.submit(wavelet)


class ProcessHandler(RobotServiceHandler):
  def __init__(self, robot):
    RobotServiceHandler.__init__(self)

  def get(self):
    #query = db.Query(model.ConferenceCollection)
    #query.filter('admin_wave =', 'googlewave.com!w+4VNd_lJPD')
    #conf = query.get()
    #conf.saved_search = 'group:webdu2010-waves@googlegroups.com'
    #conf.put()
    #TODO: Pass in TOC id
    self.ProcessWave()

  def ProcessWave(self):
    from google.appengine.ext import deferred
    import wavemaker

    toc_wavelet = 'googlewave.com!w+-pE27bZkbz'
    root_wavelet = wavecred.DOMAIN + '!conv+root'
    self.robot.setup_oauth(wavecred.CONSUMER_KEY,
                           wavecred.CONSUMER_SECRET,
                           server_rpc_base=wavecred.RPC_BASE[wavecred.DOMAIN])
    wavelet = self.robot.fetch_wavelet(toc_wavelet,
                                       root_wavelet)
    blip = wavelet.root_blip
    for annotation in blip.annotations:
      if annotation.name == 'link/wave':
        text = blip.text[annotation.start:annotation.end]
        deferred.defer(wavemaker.AddGroup, annotation.value, root_wavelet,
                       'public@a.gwave.com')

application = webapp.WSGIApplication(
                                     [
                                     ('/wave/cron', CronHandler),
                                     ('/wave/process', ProcessHandler)
                                     ],
                                     debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
