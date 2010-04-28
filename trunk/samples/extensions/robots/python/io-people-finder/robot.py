import logging
import os

from django.utils import simplejson
from google.appengine.ext import db
from google.appengine.ext import webapp
from model import Profile, GTUG
from waveapi import robot
from waveapi import events
from waveapi import element
from waveapi import wavelet as wavelet_mod
from waveapi import appengine_robot_runner

import credentials 
from interests import INTERESTS
# Globals
ROBOT_NAME = 'PeopleFinder'

# TODO
#
# * Search gadget
# Make a single wave with the search gadget
# Add link to search wave to the profile page
#
# Make the search result links to the users profile page. 
# Add public as read-only to the profile.
# Implement "Start a conversation" button that creates a new wave
#   with all the checked search results
#
# * Robot
# Add info about GTUGS present at the conference
# Add a link to the gtugs.org page if no chapters are found
# Style the profile page
#  
# Issues
# - incorrect cursor for checkbox 
# - moving map marker doesn't update gadget state
#
# DONE
# don't require creating a profile page to do an interest search


def OnParticipantsChanged(event, wavelet):
  public = 'public@a.gwave.com'
  if public in wavelet.participants:
    wavelet.participants.set_role(public, wavelet_mod.Participants.ROLE_READ_ONLY)


def OnBlipSubmitted(event, wavelet):
  """The map gadget can only be edited when the blip
  is in write mode, so we can safely handle updates
  to the user location in the BlipSubmitted event.
  """
  blip = event.blip

  mapgadget = blip.all(element.Gadget).value()
  coord = None
  for key in mapgadget.keys():
    if key.startswith('overlay-'):
      mapdata = simplejson.loads(getattr(mapgadget, key))
      if mapdata['type'] == 'point':
        coord = mapdata['coordinates'][0]

  profile = Profile.get_or_insert(wavelet.wave_id)
  oldlocation = profile.location
  if coord:
    profile.location = db.GeoPt(coord['lat'], coord['lng']) 
    profile.update_location()
    logging.debug(profile.location)
    if ( oldlocation is None ) or ( oldlocation != profile.location ):
      if oldlocation:
        logging.debug(oldlocation)
      # search for gtugs
      logging.debug(profile.location)
      results = GTUG.proximity_fetch(
          GTUG.all(),
          profile.location,
          max_results=5,
          max_distance=80467
          ) 
      if results:
        gtugblip = blip.reply()
        gtugblip.append_markup("<p>Great news, we found a Google Technology User Group near you!</p>")
        gtugblip.append(element.Line())
        gtugblip.append(element.Line())
        gtugblip.append_markup("<p>The group name is </p>")
        gtugblip.append(results[0].key().name(), [
          ('link/manual', results[0].url)
          ])
  else:
    pass # Remove the point?
  profile.put()

def OnDocumentChanged(event, wavelet):
  public = 'public@a.gwave.com'
  if public in wavelet.participants:
    wavelet.participants.set_role(public, wavelet_mod.Participants.ROLE_READ_ONLY)

  blip = event.blip

  interests = []
  for e in blip.elements:
    if isinstance(e, element.Check):
      if e.value == 'true':
        interests.append(e.name)

  fullname = ''
  nameinput = blip.first(element.Input, name='fullname')
  if nameinput:
    fullname = nameinput.get('value','')
  profile = Profile.get_or_insert(wavelet.wave_id)
  profile.name = fullname
  profile.creator = wavelet.creator
  profile.interests = interests
  profile.put()

class CreateChatHandler(webapp.RequestHandler):
  _robot  = None

  # override the constructor
  def __init__(self, robot):
    self._robot  = robot
    webapp.RequestHandler.__init__(self)

  def get(self):
    users = self.request.get('users', '').split(',')

    # create a new wave, submit immediately
    wavelet = self._robot.new_wave(domain    = 'googlewave.com',
                                participants = users,
                                submit       = True)
    wavelet.title = ("Let's chat!")
    wavelet.root_blip.append("I found you via the Google I/O 2010 People Finder.")
    self._robot.submit(wavelet)

    if wavelet.wave_id:
      json = '{"status": "success", "wave_id": "%s"}' % wavelet.wave_id
    else:
      json = '{"status": "error"}'
    self.response.out.write(json)

class CreateProfileHandler(webapp.RequestHandler):
  _robot  = None

  # override the constructor
  def __init__(self, robot):
    self._robot  = robot
    webapp.RequestHandler.__init__(self)

  def get(self):
    user = self.request.get('user')
    public = 'public@a.gwave.com'
    # create a new wave, submit immediately
    wavelet = self._robot.new_wave(domain    = 'googlewave.com',
                                participants = [user, public],
                                submit       = True)
    # Doesn't work yet, OSFE issue
    # wavelet.participants.set_role(public, wavelet_mod.Participants.ROLE_READ_ONLY)
    self.populateWavelet(wavelet)
    self._robot.submit(wavelet)

    # Create new profile entry
    profile = Profile.get_or_insert(wavelet.wave_id)
    profile.creator = user
    profile.put()

    if wavelet.wave_id:
      json = '{"status": "success", "wave_id": "%s"}' % wavelet.wave_id
    else:
      json = '{"status": "error"}'
    self.response.out.write(json)

  def populateWavelet(self, wavelet):
    blip = wavelet.root_blip
    wavelet.title = 'People-Finder Profile'
    blip.append_markup('<h2>Full Name</h2>')
    blip.append(element.Line())
    blip.append(element.Input('fullname', 'Your Name'))
    blip.append_markup('<h2>Interests</h2>')
    for (id, label) in INTERESTS:
      if id == '--':
        blip.append_markup('<h3>%s</h3>' % label)
      else:
        blip.append(element.Line())
        blip.append(element.Check(id, 'false'))
        blip.append(element.Label(id, label))

    blip.append(element.Line())
    blip.append_markup('<h2>Location</h2>')
    blip.append(element.Line())
    blip.append('You may optionally add a marker to the following map to note where you are coming from:')
    blip.append(element.Gadget('http://google-wave-resources.googlecode.com/svn/trunk/samples/extensions/gadgets/mappy/mappy.xml'))
    wavelet.tags.append('io2010')
    wavelet.tags.append('google-profile')
    wavelet.participants.add('public@a.gwave.com')

class GetProfileHandler(webapp.RequestHandler):
  _robot  = None

  # override the constructor
  def __init__(self, robot):
    self._robot  = robot
    webapp.RequestHandler.__init__(self)

  def get(self):
    user = self.request.get('user')

    # Create new profile entry
    query = Profile.all()
    query.filter('creator =', user)
    profile = query.get()
    if profile:
      json = '{"status": "success", "wave_id": "%s"}' % profile.key().name()
    else:
      json = '{"status": "error"}'
    self.response.out.write(json)

if __name__ == '__main__':
  appid = os.environ['APPLICATION_ID']
  r = robot.Robot(ROBOT_NAME.capitalize(),
      image_url='http://%s.appspot.com/static/icon.png' % appid,
      profile_url='http://%s.appspot.com/static/profile.html' % appid)

  r.set_verification_token_info(credentials.VERIFICATION_TOKEN, credentials.ST)
  r.setup_oauth(credentials.CONSUMER_KEY, credentials.CONSUMER_SECRET,
                  server_rpc_base='http://gmodules.com/api/rpc')

  r.register_handler(events.DocumentChanged, OnDocumentChanged, 
     context = [events.Context.ALL])
  r.register_handler(events.BlipSubmitted, OnBlipSubmitted)
  r.register_handler(events.WaveletParticipantsChanged, OnParticipantsChanged)

  appengine_robot_runner.run(r, debug=True, extra_handlers=[
      ('/web/getprofilewave', lambda: GetProfileHandler(r)),
      ('/web/startawave', lambda: CreateChatHandler(r)),
      ('/web/profilewave', lambda: CreateProfileHandler(r))
      ]
      )
