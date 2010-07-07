#!/usr/bin/python2.4
import logging
import os
from time import strftime

from django.utils import simplejson
from google.appengine.api import urlfetch

from waveapi import events
from waveapi import robot
from waveapi import element
from waveapi import ops
from waveapi import element
from waveapi import appengine_robot_runner

import gdata.projecthosting.client
import gdata.projecthosting.data
import gdata.gauth
import gdata.client
import gdata.data
import atom.http_core
import atom.core

import models
import util

TRIAGEY_ID = 'bug-triagey/issueid'

def AddItems(blip, source):
  # Store some handy local vars
  project = source['project']
  status = source['status']
  label = source['label']
  labeled_buckets = GetItems(project, status, label)

  # Append a descriptive header
  header = 'Issues for %s with status %s, sorted by %s:' % (project, status, label)
  blip.append(header, [('style/fontWeight', 'bold')])
  blip.append('\n\n')

  for bucket_label, issues in labeled_buckets.items():
    header_label = '%s:' % bucket_label
    blip.append(header_label, [('style/fontWeight', 'bold')])
    for issue in issues:
      issue_id = issue.id.text.split('/')[-1]
      issue_link = 'http://code.google.com/p/%s/issues/detail?id=%s' % (source['project'], issue_id)
      issue_title = issue.title.text
      blip.append('\n', [])
      blip.append(issue_title, [('link/manual', issue_link), (TRIAGEY_ID, issue_id)])
      blip.append('\n', [('link/manual', None)])
      blip.append('Looking at this? ')
      blip.append(element.Button(name=(issue_id + '-looking'), value='No'))
      blip.append(' Responded? ')
      blip.append(element.Button(name=(issue_id + '-responded'), value='No'))
      blip.append('\n')
    blip.append('\n')

def GetItems(project, status, bucket_label):
  issues_client = gdata.projecthosting.client.ProjectHostingClient()
  project_name = project
  query = gdata.projecthosting.client.Query(status=status)
  feed = issues_client.get_issues(project_name, query=query)
  labeled_buckets = {'NOLABEL': []}
  for issue in feed.entry:
    in_bucket = False
    for label in issue.label:
      if not in_bucket and label.text.find(bucket_label) > -1:
        if label.text not in labeled_buckets:
          labeled_buckets[label.text] = []
        labeled_buckets[label.text].append(issue)
        in_bucket = True
    if not in_bucket:
      labeled_buckets['NOLABEL'].append(issue)
  return labeled_buckets

def OnButtonClicked(event, wavelet):
  # Find out who clicked the button
  clicker = event.modified_by.split('@')[0]

  # Find the button element
  button_name = event.button_name
  button = event.blip.first(element.Button, name=button_name)

  # Change button label to show who clicked it
  value = 'Yes (%s)' % clicker
  button.update_element({'value': value})

  # Strike out the relevant issue if they clicked responded button
  if button_name.find('looking') > -1:
    return
  issue_id = button_name.split('-')[0]
  for annotation in wavelet.root_blip.annotations:
    if annotation.name == TRIAGEY_ID and annotation.value == issue_id:
      start = annotation.start
      end = annotation.end
      event.blip.range(start, end).annotate('style/textDecoration', 'line-through')

def OnGadgetChanged(event, wavelet):
  blip = event.blip
  gadget = blip.first(element.Gadget, url=util.GetGadgetUrl())
  preset_key = gadget.preset_key
  gadget.delete()
  url = 'http://bug-triagey.appspot.com/web/preset?preset_key=%s' % preset_key
  logging.info(url)
  result = urlfetch.fetch(url)
  logging.info(result)
  if result.status_code == 200:
    sources  = simplejson.loads(result.content)['sources']
    logging.info(sources)
    for source in sources:
      AddItems(blip, source)

def OnSelfAdded(event, wavelet):
  if len(wavelet.title) < 2:
    wavelet.title = 'Bug Triage: %s' % strftime('%Y-%m-%d')
  wavelet.root_blip.append('\n')
  gadget = element.Gadget(url=util.GetGadgetUrl())
  wavelet.root_blip.append(gadget)


if __name__ == '__main__':
  removey = robot.Robot('Bug Triagey',
      image_url='http://bug-triagey.appspot.com/static/avatar.png',
      profile_url='')
  removey.register_handler(events.WaveletSelfAdded, OnSelfAdded)
  removey.register_handler(events.GadgetStateChanged, OnGadgetChanged)
  removey.register_handler(events.FormButtonClicked, OnButtonClicked)
  appengine_robot_runner.run(removey, debug=True)
