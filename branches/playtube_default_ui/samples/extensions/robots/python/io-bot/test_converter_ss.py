#!/usr/bin/python2.5
#
# Copyright 2009 Google Inc. All Rights Reserved.

"""Tests for util."""

import unittest

from google.appengine.api import urlfetch
from google.appengine.api import apiproxy_stub_map
from google.appengine.api import urlfetch_stub

import converter_ss

class UtilTest(unittest.TestCase):

  def setUp(self):
    apiproxy_stub_map.apiproxy = apiproxy_stub_map.APIProxyStubMap()
    apiproxy_stub_map.apiproxy.RegisterStub('urlfetch', urlfetch_stub.URLFetchServiceStub())


  def testSpreadsheetConverter(self):
    url = 'http://spreadsheets.google.com/feeds/list/tyc8JlfaUPHQbG0ok-VtIFw/od6/public/values?alt=json'
    spreadsheet_converter = converter_ss.SpreadsheetConverter(url)
    conf = spreadsheet_converter._conference
    self.assertEquals(80, len(conf.sessions))
    session = conf.sessions[0]
    print session
    self.assertEquals('A beginner\'s guide to Android', session.name)
    self.assertEquals('Reto Meier', session.speakers[0].name)
    self.assertEquals('http://code.google.com/events/io/2010/speakers.html#RetoMeier',
                      session.speakers[0].link)
    session = conf.sessions[2]
    print session
    self.assertEquals('Romain Guy', session.speakers[0].name)
    self.assertEquals('http://code.google.com/events/io/2010/speakers.html#RomainGuy',
                      session.speakers[0].link)
    self.assertEquals('Adam Powell', session.speakers[1].name)
    self.assertEquals('http://code.google.com/events/io/2010/speakers.html#AdamPowell',
                      session.speakers[1].link)


if __name__ == '__main__':
  unittest.main()
