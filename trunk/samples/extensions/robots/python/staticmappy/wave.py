from waveapi import robot
from waveapi import events
from waveapi import element
from waveapi import appengine_robot_runner
from google.appengine.api import urlfetch

import logging
import urllib2

ROBOT_KEY = 'appspot/staticmappy/address'

def GetStaticMap(address):
  url = 'http://maps.google.com/maps/api/staticmap?center=%s&size=400x400&sensor=false' % address.replace(' ', '+').replace('&', '%26')
  #file_data = urllib2.urlopen(url).read().strip()
  file_data = urlfetch.fetch(url).content
  attachment = element.Attachment(caption=address, data=file_data)
  return attachment

def OnAnnotationChanged(event, wavelet):
  blip = event.blip
  text = blip.text
  # construct the todo outside of the loop to avoid
  # influencing what we're observing:
  todo = []
  for ann in blip.annotations:
    if ann.name == ROBOT_KEY:
      logging.info('found it!')
      todo.append((ann.start, ann.end, ann.value))
  for start, end, value in todo:
    payload = text[start:end]
    blip.range(start, end).clear_annotation(ROBOT_KEY)
    blip.at(end).insert(GetStaticMap(payload))

if __name__ == '__main__':
  robotty = robot.Robot('Static Mappy',
                        image_url='http://staticmappy-bot.appspot.com/avatar.png')
  robotty.register_handler(events.AnnotatedTextChanged, OnAnnotationChanged, filter=ROBOT_KEY)
  robotty.register_handler(events.WaveletSelfAdded, OnAnnotationChanged)
  appengine_robot_runner.run(robotty, debug=True)
