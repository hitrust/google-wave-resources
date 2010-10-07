import logging

from waveapi import events
from waveapi import robot
from waveapi import element
from waveapi import ops
from waveapi import element
from waveapi import appengine_robot_runner

import config
import message
import installerchecker

INSTALLER_STATUS = 'submitty/installer/status'
INSTALLER_URL = 'submitty/installer/url'
STATUS_ADDEDREVIEWERS = 'submitty/status/addedreviewers'
STATUS_APPROVED = 'submitty/status/approved'
GADGET_URL = 'http://submitty-bot.appspot.com/gadget.xml?nocache=1234567'
DOMAIN = 'googlewave.com'

def lookForInstaller(wavelet):
  blip = EnhancedBlip(wavelet.root_blip)
  if INSTALLER_STATUS in wavelet.data_documents:
    return
  installer_input, installer_index = blip.get_input('installer_url')
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

def lookForAnswer(wavelet, checkbox_name, message):
  if checkbox_name in wavelet.data_documents:
    return
  blip = wavelet.root_blip
  checkbox = blip.first(element.Check, name=checkbox_name)
  if checkbox and getattr(checkbox.value(), 'value') == 'true':
    wavelet.data_documents[checkbox_name] = 'Responded'
    for pos, elem in blip._elements.items():
      if elem == checkbox:
        inline_blip = blip.insert_inline_blip(pos+1)
        inline_blip.append(message)

def lookForAnswers(wavelet):
  #lookForAnswer(wavelet, CHECKBOX_ROBOT, message.ROBOT_QS)
  #lookForAnswer(wavelet, CHECKBOX_GADGET, message.GADGET_QS)
  #lookForAnswer(wavelet, CHECKBOX_GAE, message.GAE_QS)
  pass

def ModifiedByApprover(modifier):
  if modifier in config.APPROVERS:
    return True
  else:
    logging.info('Someone else tried to approve: %s' % modifier)
    return False

def OnGadgetStateChanged(event, wavelet):
  # if new status is review, add peeps
  # if new status is approve, add to gallery
  # if gadget changed isnt actually the approval gadget, return
  gadget = event.blip.first(element.Gadget, url=GADGET_URL)
  if gadget is None:
    return
  if gadget.status == 'review' and STATUS_ADDEDREVIEWERS not in wavelet.data_documents:
    AddReviewers(wavelet)
    wavelet.data_documents[STATUS_ADDEDREVIEWERS] = 'yes'
    wavelet.tags.append('status-inreview')
  if gadget.status == 'approved':
    # Check for maldoers
    if ModifiedByApprover(event.modified_by):
      # make new gallery wave
      AddToGallery(wavelet)
      wavelet.data_documents[STATUS_APPROVED] = 'yes'
      wavelet.tags.remove('status-inreview')
      wavelet.tags.append('status-approved')

def AddToGallery(wavelet):
  participants = [config.GALLERYGROUP, config.GALLERYMOD]
  new_wavelet = submitty.new_wave(DOMAIN, participants,
                                  proxy_for_id='noudw')
  blip = EnhancedBlip(wavelet.root_blip)
  extension_url = blip.get_input_value('installer_url')
  extension_name = installerchecker.get_name(extension_url)
  new_wavelet.title = extension_name
  new_blip = new_wavelet.root_blip
  new_blip.append('\n')
  new_blip.append(element.Installer(extension_url))
  new_wavelet.submit_with(wavelet)

def AddReviewers(wavelet):
  for reviewer in config.REVIEWERS:
    wavelet.participants.add(reviewer)

def OnButtonClicked(event, wavelet):
  blip = event.blip
  button_name = event.button_name
  for element_index, elem in blip._elements.items():
    if elem.type == 'BUTTON' and elem.name == button_name:
      button_pos = element_index
  message = wavelet.data_documents[button_name]
  inline_blip = blip.insert_inline_blip(button_pos+1)
  inline_blip.append(message)
  blip.first(element.Button, name=button_name).delete()

def OnBlipSubmitted(event, wavelet):
  blip = event.blip
  lookForInstaller(wavelet)

def OnSelfAdded(event, wavelet):
  blip = EnhancedBlip(wavelet.root_blip)

  # Deal with the case of people clicking 'New Wave' on robot in gallery waves
  if wavelet.robot_address.find('noudw') > -1:
    wavelet.title = message.ACC_TITLE
    blip.append(message.ACC_MESSAGE)
    return

  # Otherwise, assume that they want to submit an extension
  wavelet.title = message.TITLE
  blip.add_line()
  blip.append(element.Gadget(GADGET_URL))
  blip.add_line()
  blip.append_markup(message.INTRO)
  blip.add_line()
  blip.add_line()
  blip.add_fields(message.DEV_FIELDS)
  blip.add_line()
  blip.append_markup(message.MIDDLE)
  blip.add_line()
  blip.add_line()
  blip.add_fields(message.EXT_FIELDS)
  blip.add_line()
  blip.add_questions(message.EXT_QS, wavelet.data_documents)



class EnhancedBlip(object):
  def __init__(self, blip):
    self.blip = blip

  def __getattr__(self, attribute):
    return getattr(self.blip, attribute)

  def add_line(self):
    self.blip.append('\n')

  def add_questions(self, questions, datadocs):
    for question in questions:
      self.blip.append(question['label'] + '  ')
      name = question['name']
      button = element.Button(name=name, caption='(Click if yes)')
      self.blip.append(button)
      self.blip.append('\n\n')
      datadocs[name] = question['response']


  def add_fields(self, fields):
    for field in fields:
      first_line = field['label']
      if field.get('extra'):
        first_line = '%s (%s)' % (first_line, field['extra'])
      first_line = '%s' % first_line
      self.blip.append(first_line)
      self.blip.append(element.Input(field['name']))

  def get_input(self, name):
    for element_index, element in self.blip._elements.items():
      if hasattr(element, 'name') and element.name == name:
        return element, element_index
    return None, None

  def get_input_value(self, name):
    input = self.blip.first(element.Input, name=name)
    return input.value().value


if __name__ == '__main__':
  submitty = robot.Robot('Submitty',
                         image_url='http://submitty-bot.appspot.com/img/submitty_avatar.png',
                         profile_url='http://code.google.com/apis/wave/')
  submitty.register_handler(events.WaveletSelfAdded, OnSelfAdded)
  submitty.register_handler(events.DocumentChanged, OnBlipSubmitted, context=[events.Context.ALL])
  submitty.register_handler(events.BlipSubmitted, OnBlipSubmitted)
  submitty.register_handler(events.GadgetStateChanged, OnGadgetStateChanged)
  submitty.register_handler(events.FormButtonClicked, OnButtonClicked)
  appengine_robot_runner.run(submitty, debug=True)
