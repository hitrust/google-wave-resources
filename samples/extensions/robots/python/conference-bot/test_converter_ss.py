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
    spreadsheet_converter = converter_ss.SpreadsheetConverter('http://spreadsheets.google.com/feeds/list/tGGdPAaxvQjFEgzvXi9wCdw/od6/public/values?alt=json')
    conf = spreadsheet_converter._conference
    self.assertEquals(13, len(conf.sessions))
    session = conf.sessions[0]
    self.assertEquals('Web design that grabs people', session.name)
    self.assertEquals('Scott Thomas', session.speakers[0].name)

  def testSpreadsheetConverterWebdu(self):
    url = 'http://spreadsheets.google.com/feeds/list/tVQA1EbmPcWM2yZ_i0y315g/od6/public/values?alt=json'
    spreadsheet_converter = converter_ss.SpreadsheetConverter(url)
    conf = spreadsheet_converter._conference
    self.assertEquals(45, len(conf.sessions))
    session = conf.sessions[0]
    self.assertEquals('Augmented Reality in Unity 3D using FLARToolkit', session.name)
    self.assertEquals('Ari Jacobs (Sydney, Australia)', session.speakers[0].name)


if __name__ == '__main__':
  unittest.main()
