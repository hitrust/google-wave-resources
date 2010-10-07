import logging
import os
import string

from waveapi import events
from waveapi import robot
from waveapi import element
from waveapi import appengine_robot_runner
from google.appengine.ext import db

import models
import blipconverter

# Events

def OnRobotAdded(event, wavelet):
  ExportWavelet(wavelet)

def OnBlipSubmitted(event, wavelet):
  ExportWavelet(wavelet)

# Operations

def AddBlip(wavelet, string):
  wavelet.reply('\n').append(string)

# Helper Functions

def ExportWavelet(wavelet):
  text = ExportWaveletToText(wavelet)
  html = ExportWaveletToHTML(wavelet)
  StoreExport(wavelet, text=text, html=html)
  pass

def ExportWaveletToHTML(wavelet):
  html_list = []
  for blip_id in wavelet.blips:
    blip = wavelet.blips.get(blip_id)
    html_list.append('<div class="blip">' + blipconverter.ToHTML(blip) +
                     '</div>')
  return string.join(html_list, '<br>')

def ExportWaveletToText(wavelet):
  text_list = []
  for blip_id in wavelet.blips:
    blip = wavelet.blips.get(blip_id)
    text_list.append(blipconverter.ToText(blip))
  return string.join(text_list, '\n\n')

def StoreExport(wavelet, html='', text=''):
  id = wavelet.wave_id
  query = db.Query(models.WaveExport)
  query.filter('id =', id)
  waveExport = query.get()
  if waveExport is None:
    server = os.environ['SERVER_NAME']
    url = "http://" + server + "/export?waveId=" + id.replace("+", "%252B")
    url_text = '%s&format=text' % url
    AddBlip(wavelet, "View export: \n%s\n%s\n" % (url, url_text))
    waveExport = models.WaveExport()

  waveExport.id = id
  waveExport.title = wavelet.title
  waveExport.text = text
  waveExport.html = html
  waveExport.participants = [p for p in wavelet.participants]
  waveExport.put()

if __name__ == '__main__':
  robotty = robot.Robot('Exporty',
      image_url='http://exporty-bot.appspot.com/avatar.png',
      profile_url='') 
  robot_context = [events.Context.ALL]
  robotty.register_handler(events.BlipSubmitted, OnBlipSubmitted,
                           context=robot_context)
  robotty.register_handler(events.WaveletSelfAdded, OnRobotAdded,
                           context=robot_context)
  robotty.register_handler(events.WaveletParticipantsChanged, OnRobotAdded,
                           context=robot_context)
  appengine_robot_runner.run(robotty, debug=True)
