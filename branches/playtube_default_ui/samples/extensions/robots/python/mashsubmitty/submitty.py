#!/usr/bin/python2.4
#

import logging
import urllib
import re

from waveapi import events
from waveapi import robot
from waveapi import element
from waveapi import ops
from waveapi import element 
from waveapi import appengine_robot_runner

from django.utils import simplejson
from google.appengine.api import urlfetch
from google.appengine.api import mail

import message
import installerchecker
import credentials

INSTALLER_STATUS = 'submitty/installer/status'
STATUS_ADDEDREVIEWERS = 'submitty/status/addedreviewers'
STATUS_APPROVED = 'submitty/status/approved'
GADGET_URL = 'http://mashable-submitty.appspot.com/gadget.xml?nocache=1234567'
REVIEW_GROUP = 'mashable-google-wave-api-team@googlegroups.com'

def lookForInstaller(wavelet):
  blip = wavelet.root_blip
  if INSTALLER_STATUS in wavelet.data_documents:
    return

  installer_input, installer_index = GetInput(blip, 'installer_url')
  if installer_input is None:
    return
  installer_url = installer_input.value
  if len(installer_url) < 20:
    return
  errors = installerchecker.check(installer_url)

  response_blip = blip.insert_inline_blip(installer_index+1)
  if len(errors) > 0:
    wavelet.data_documents[INSTALLER_STATUS] = 'errors'
    response_blip.append('\n'.join(errors))
  else:
    wavelet.data_documents[INSTALLER_STATUS] = 'success'
    response_blip.append('Installer looks good!')
    response_blip.append(element.Installer(installer_url))

def GetInput(blip, name):
  for element_index, element in blip._elements.items():
    if hasattr(element, 'name') and element.name == name:
      return element, element_index
  return None, None

def ModifiedByApprover(modifier):
  approvers = ['pamela.fox@googlewave.com', 
               'adamhirschmashable@googlewave.com',
               'mystalic@googlewave.com',
               'pamela.fox@wavesandbox.com',
               'dlpeters@googlewave.com']
  if modifier in approvers:
    return True
  else:
    logging.info('Someone else tried to approve: %s' % modifier)
    return False

def OnGadgetStateChanged(event, wavelet):
  # if new status is review, add peeps
  # if new status is approve, add to gallery
  gadget = event.blip.first(element.Gadget, url=GADGET_URL)
  if gadget.status == 'review' and STATUS_ADDEDREVIEWERS not in wavelet.data_documents:
    AddReviewers(wavelet)
    wavelet.data_documents[STATUS_ADDEDREVIEWERS] = 'yes'
  #if gadget.status == 'approved' and STATUS_APPROVED not in wavelet.data_documents:
  if gadget.status == 'approved':
    # Check for maldoers
    if ModifiedByApprover(event.modified_by):
      # make new gallery wave
      AddToGallery(wavelet)
      wavelet.data_documents[STATUS_APPROVED] = 'yes'
      wavelet.tags.append('status-approved')

def GetInputValue(blip, name):
  input = blip.first(element.Input, name=name)
  return input.value().value

def GetTextAreaValue(blip, name):
  input = blip.first(element.TextArea, name=name)
  return input.value().value

def AddToGallery(wavelet):
  group = 'mashable-google-wave-api-challenge@googlegroups.com'
  pamela = 'pamela.fox@googlewave.com'
  public = 'public@a.gwave.com'
  domain = 'googlewave.com'

  # Get info
  blip = wavelet.root_blip
  installer_url = GetInputValue(blip, 'installer_url')
  extension_name = GetInputValue(blip, 'name')
  extension_summary = GetInputValue(blip, 'summary')
  extension_description = GetTextAreaValue(blip, 'description')
  extension_screenshot = GetInputValue(blip, 'screenshot')
  if installer_url:
    extension_thumbnail = installerchecker.get_thumbnail(installer_url)
  else:
    extension_thumbnail = 'http://wave-samples-gallery.appspot.com/static/img/project_gallery_logo.png'


  # Create installer wave
  # Create discussion wave
  participants = [pamela, public]
  discussion_wave = submitty.new_wave(domain, participants,
                                      submit=True)
  discussion_wave.title = 'Discuss: %s' % extension_name
  blip = discussion_wave.root_blip
  blip.append('\n%s\n\n' % extension_description)
  if installer_url:
    blip.append(element.Installer(installer_url))
  gadget_url = 'http://mashable-submitty.appspot.com/gadget_ratings.xml'
  blip.append(element.Gadget(gadget_url))
  gadget_url = 'http://mashable-submitty.appspot.com/gadget_twitter.xml'
  props = {'wavetitle': extension_name}
  blip.append(element.Gadget(gadget_url, props))
  submitty.submit(discussion_wave)

  # Add to TOC wave
  toc_wave_id = 'googlewave.com!w+DYz-iagTK'
  toc_wavelet_id = 'googlewave.com!conv+root'
  toc_wavelet = submitty.fetch_wavelet(toc_wave_id, toc_wavelet_id)
  blip = toc_wavelet.root_blip
  line = element.Line(line_type='h2')
  blip.append(line)
  blip.append(extension_name)
  blip.append('\n')
  image = element.Image(url=extension_thumbnail, width=120, height=120)
  blip.append(image)
  blip.append("\n%s\n" % extension_summary)
  AddLink(blip, discussion_wave.title, discussion_wave.wave_id)
  blip.append('\n\n')
  blip.at(len(blip.text)-2).clear_annotation('style/fontStyle')
  blip.at(len(blip.text)-2).clear_annotation('link/wave')
  blip.at(len(blip.text)-2).clear_annotation('link/manual')
  submitty.submit(toc_wavelet)

def AddLink(blip, link_text, link_id):
  line = element.Line(line_type='li')
  blip.append(line)
  blip.append(link_text, bundled_annotations=[('link/wave', link_id)])
  blip.append('\n', bundled_annotations=[])

def AddReviewers(wavelet):
  wavelet.participants.add(REVIEW_GROUP)
  wavelet.participants.add('pamela.fox@'+ wavelet.domain)

def OnBlipSubmitted(event, wavelet):
  blip = event.blip
  lookForInstaller(wavelet)

def OnSelfAdded(event, wavelet):
  blip = wavelet.root_blip
  # Don't modify an existing wave, if someone
  # accidentally adds it to one
  if len(blip.text) > 5:
    return

  wavelet.title = 'Submissions are closed!'
  return
  wavelet.title = 'Mashable Extension Submission'
  blip.append('\n')
  gadget = element.Gadget(GADGET_URL)
  blip.append(gadget)
  blip.append('\n')
  blip.append_markup(message.intro)
  AddFields(blip, message.team_fields)
  blip.append('\n\n')
  blip.append_markup(message.middle)
  AddFields(blip, message.ext_fields)

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
  submitty = robot.Robot('Submitty',
                         image_url='http://submitty-bot.appspot.com/img/submitty_avatar.png',
                         profile_url='http://code.google.com/apis/wave/')
  submitty.set_verification_token_info(credentials.VERIFICATION_TOKEN, credentials.ST) 
  submitty.setup_oauth(credentials.CONSUMER_KEY, credentials.CONSUMER_SECRET,
    server_rpc_base=credentials.RPC_BASE)
  submitty.register_handler(events.WaveletSelfAdded, OnSelfAdded)
  submitty.register_handler(events.BlipSubmitted, OnBlipSubmitted)
  submitty.register_handler(events.GadgetStateChanged, OnGadgetStateChanged)
  appengine_robot_runner.run(submitty, debug=True)
