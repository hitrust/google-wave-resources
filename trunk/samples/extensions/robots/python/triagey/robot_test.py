#!/usr/bin/python2.4
#
# Copyright 2010 Google Inc. All Rights Reserved.

"""Tests for robot."""

__author__ = 'pamelafox@google.com (Pamela Fox)'

import unittest

import robot

class RobotTest(unittest.TestCase):

  def testGetItems(self):
    labeled_buckets = robot.GetItems('google-wave-resources', 'New', 'ApiType')
    for label, issues in labeled_buckets.items():
      print label
      print issues

if __name__ == '__main__':
  unittest.main()
