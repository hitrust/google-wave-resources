import logging

from waveapi import events
from waveapi import robot
from waveapi import element
from waveapi import appengine_robot_runner

import forminfo

def OnSelfAdded(event, wavelet):
  blip = wavelet.root_blip
  # Don't modify an existing wave, if someone
  # accidentally adds it to one
  if len(blip.text) > 5:
    return
  wavelet.title = forminfo.title
  blip.append('\n')
  blip.append_markup(forminfo.intro)
  AddFields(blip, forminfo.fields)
  blip.append('\n')
  AddTags(wavelet)
  AddParticipants(wavelet)

def AddParticipants(wavelet):
  for participant in forminfo.participants:
    wavelet.participants.add(participant)

def AddTags(wavelet):
  for tag in forminfo.tags:
    wavelet.tags.append(tag)

def AddFields(blip, fields):
  blip.append('\n\n')
  for field in fields:
    first_line = '<b>%s</b>' % field['label']
    if field.get('extra'):
      first_line = '%s (%s)' % (first_line, field['extra'])
    first_line = '<p>%s</p>' % first_line
    blip.append_markup(first_line)
    type = 'input'
    if field.get('type'):
      type = field.get('type')
    if type == 'input':
      blip.append(element.Input(field['name']))
    elif type == 'newline':
      blip.append('\n\n\n\n')
    elif type == 'textarea':
      blip.append(element.TextArea(field['name'], '\n\n\n'))
  blip.append('\n')


if __name__ == '__main__':
  submitty = robot.Robot('Formy',
                         image_url='http://sites.google.com/site/mori79b/_/rsrc/1258609508780/icons-logos/Forms-icon.gif',
                         profile_url='')
  submitty.register_handler(events.WaveletSelfAdded, OnSelfAdded)
  appengine_robot_runner.run(submitty, debug=True)
