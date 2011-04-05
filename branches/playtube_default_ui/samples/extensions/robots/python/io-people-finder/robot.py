import logging
import os

from django.utils import simplejson
from google.appengine.ext import db
from google.appengine.ext import webapp
from model import Person, GTUG
from waveapi import robot
from waveapi import events
from waveapi import element
from waveapi import wavelet as wavelet_mod
from waveapi import appengine_robot_runner

import credentials 
# Globals
ROBOT_NAME = 'Google I/O 2010'

class RemoveLocation(webapp.RequestHandler):
  _robot  = None

  # override the constructor
  def __init__(self, robot):
    self._robot  = robot
    webapp.RequestHandler.__init__(self)

  def get(self):
    viewer_id = self.request.get('viewer_id', '')
    if viewer_id.find('googlewave.com') > -1:
      gadget_key = viewer_id.split('@')[0]
    else:
      gadget_key = viewer_id
    wavelet = self._robot.fetch_wavelet('googlewave.com!w+0iIr7fEYA', "googlewave.com!conv+root")
    delta = {}
    delta[gadget_key] = None 
    wavelet.root_blip.first(element.Gadget).update_element(delta)
    self._robot.submit(wavelet)


class SaveLocation(webapp.RequestHandler):
  _robot  = None

  # override the constructor
  def __init__(self, robot):
    self._robot  = robot
    webapp.RequestHandler.__init__(self)

  def get(self):
    viewer_id = self.request.get('viewer_id', '')
    if viewer_id.find('googlewave.com') > -1:
      gadget_key = viewer_id.split('@')[0]
    else:
      gadget_key = viewer_id
    viewer_name = self.request.get('viewer_name', '')
    viewer_thumbnail = self.request.get('viewer_thumbnail', '')

    # compress viewer
    latlng = self.request.get('latlng', '')
    country = self.request.get('country', '')
    wavelet = self._robot.fetch_wavelet('googlewave.com!w+0iIr7fEYA', "googlewave.com!conv+root")
    delta = {}
    delta[gadget_key] = latlng.replace(' ', '') + ',' + country
    wavelet.root_blip.first(element.Gadget).update_element(delta)
    self._robot.submit(wavelet)
    person = Person.get_or_insert(viewer_id)
    person.name = viewer_name
    person.thumbnail = viewer_thumbnail
    person.country = country
    logging.info(person.name)
    person.put()
    oldlocation = person.location
    coord_list = latlng.split(',')
    lat = float(coord_list[0])
    lng = float(coord_list[1])
    person.location = db.GeoPt(lat, lng)
    person.update_location()
    person.put()

class GetPersonInfo(webapp.RequestHandler):
  def get(self):
    participant_ids = self.request.get('participant_ids').split(',')
    info = []
    for participant_id in participant_ids:
      if len(participant_id) > 3:
        if participant_id.find('@') < 0:
          participant_id = participant_id + '@googlewave.com'
        person = Person.get_by_key_name(participant_id)
        thumbnail = person.thumbnail
        if thumbnail and thumbnail.find('http') < 0:
          thumbnail = 'http:%s' % thumbnail
        info.append({'address': participant_id, 'name': person.name, 'thumbnail': thumbnail})
    self.response.out.write(simplejson.dumps(info))

class MakeWave(webapp.RequestHandler):
  _robot  = None

  # override the constructor
  def __init__(self, robot):
    self._robot  = robot
    webapp.RequestHandler.__init__(self)

  def get(self):
    domain = 'googlewave.com'
    addresses = self.request.get('addresses').split(',')
    wavelet = self._robot.new_wave(domain = domain,
                                  participants  = addresses,
                                  submit = True)
    wavelet.title = ('I found you on the Google I/O Attendees map..')
    self._robot.submit(wavelet)
    url = 'https://wave.google.com/wave/#restored:wave:%s' % wavelet.wave_id
    self.redirect(url);


if __name__ == '__main__':
  appid = os.environ['APPLICATION_ID']
  r = robot.Robot(ROBOT_NAME.capitalize(),
                  image_url='http://io2010-bot.appspot.com/img/thumbnail.png',
                  profile_url='http://code.google.com/events/io')

  r.set_verification_token_info(credentials.VERIFICATION_TOKEN, credentials.ST)
  r.setup_oauth(credentials.CONSUMER_KEY, credentials.CONSUMER_SECRET,
                  server_rpc_base='http://gmodules.com/api/rpc')

  appengine_robot_runner.run(r, debug=True, extra_handlers=[
      ('/web/savelocation', lambda: SaveLocation(r)),
      ('/web/removelocation', lambda: RemoveLocation(r)),
      ('/web/getpersoninfo', lambda: GetPersonInfo()),
      ('/web/makewave', lambda: MakeWave(r))
      ]
      )
