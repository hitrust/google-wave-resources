#!/usr/bin/python2.4
import logging

from waveapi import events
from waveapi import robot
from google.appengine.ext import webapp
from waveapi import appengine_robot_runner
from google.appengine.ext import deferred

import wavemaker
import credentials

class CreateHandler(webapp.RequestHandler):
  robot  = None

  # override the constructor
  def __init__(self):
    webapp.RequestHandler.__init__(self)

  def get(self):
    num = int(self.request.get('num', '1'))
    for x in range(num):
      deferred.defer(wavemaker.MakeWave)
    self.response.out.write('Creating %s waves' % str(num))

if __name__ == '__main__':
  wavey = robot.Robot('Public Feedy',
                      image_url='http://wave.google.com/wave/static/images/unknown.jpg')
  appengine_robot_runner.run(wavey, debug=True, extra_handlers=[('/web/create',
                                                                   lambda:
                                                                   CreateHandler())])
