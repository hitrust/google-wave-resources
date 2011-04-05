#!/usr/bin/python2.5
#
# Copyright 2009 Google Inc. All Rights Reserved.

"""Tests for util."""

import unittest

from google.appengine.api import urlfetch
from google.appengine.api import apiproxy_stub_map
from google.appengine.api import urlfetch_stub

from bitly import BitLy
import bitlycred

class BitlyTest(unittest.TestCase):

  def setUp(self):
    apiproxy_stub_map.apiproxy = apiproxy_stub_map.APIProxyStubMap()
    apiproxy_stub_map.apiproxy.RegisterStub('urlfetch', urlfetch_stub.URLFetchServiceStub())


  def testShortenURL(self):
    bitly = BitLy(bitlycred.LOGIN, bitlycred.KEY)
    short_url = bitly.shorten('http://www.chrishannam.co.uk')
    print short_url


if __name__ == '__main__':
  unittest.main()
