#!/usr/bin/python2.4

import logging
import urllib
import re
import os
import random

import models

from waveapi import events
from waveapi import robot
from waveapi import ops
from waveapi import element
from waveapi import appengine_robot_runner
from google.appengine.ext import db

GADGET_TEMPLATE = """
<Module>
<ModulePrefs title="Gadget API Example" height="120">
  <Require feature="wave" /> 
</ModulePrefs>
<Content type="html">
<![CDATA[ 
<div id="content_div" style="height: 50px;"></div>
    <script type="text/javascript">

    // Replace this code with your own!
    var div = document.getElementById('content_div');

    function buttonClicked() {
      var value = parseInt(wave.getState().get('count', '0'));
      wave.getState().submitDelta({'count': value + 1});
    }

    function stateUpdated() {
      if(!wave.getState().get('count')) {
        div.innerHTML = "The count is 0."
      }
      else {
        div.innerHTML = "The count is " + wave.getState().get('count');
      } 
    }
 
    function init() {
      if (wave && wave.isInWaveContainer()) {
        wave.setStateCallback(stateUpdated);
      }
    }
    gadgets.util.registerOnLoadHandler(init);
    </script>
    <input type=button value="Click Me!" id="butCount" onClick="buttonClicked()">
  ]]> 
  </Content>
</Module>
"""

def OnBlipSubmitted(event, wavelet):
  blip = event.blip
  addGadget(wavelet)

def OnSelfAdded(event, wavelet):
  if len(wavelet.root_blip.text) < 5:
    wavelet.title = 'Gadget Code'
    wavelet.root_blip.append(GADGET_TEMPLATE, bundled_annotations=[('style/fontFamily', 'monospace')])
  addGadget(wavelet)

def addGadget(wavelet):
  blip = wavelet.root_blip
  body = blip.text.split('\n', 2)[2]
  id = wavelet.wave_id
  query = db.Query(models.WaveExport)
  query.filter('id =', id)
  waveExport = query.get()
  server = os.environ['SERVER_NAME']
  url = "http://" + server + "/export?waveId=" + id.replace("+", "%252B") + "&ext=.xml?rand=" + str(random.randint(0, 100000))

  if waveExport is None:
    waveExport = models.WaveExport()
  else:
    if waveExport.body == body:
      #Nothing changed, do nothing
      #Blip_submitted gets called when gadget state changes as well
      return
  blip.all(element.Gadget).delete()

  gadget = element.Gadget(url)
  blip.append(gadget)

  waveExport.id = id
  waveExport.title = wavelet.title
  waveExport.body = body
  waveExport.put()


if __name__ == '__main__':
  gadgitty = robot.Robot('Gadgitty',
      image_url='http://www.seoish.com/wp-content/uploads/2009/04/wrench.png',
      profile_url='')
  gadgitty.register_handler(events.WaveletSelfAdded, OnSelfAdded)
  gadgitty.register_handler(events.BlipSubmitted, OnBlipSubmitted)
  appengine_robot_runner.run(gadgitty, debug=True)
