#!/usr/bin/python2.5
#
# Copyright 2009 Google Inc.
# Licensed under the Apache License, Version 2.0:
# http://www.apache.org/licenses/LICENSE-2.0

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

import service

def main():
  application = webapp.WSGIApplication([
      ('/service/isfollowing', service.IsFollowing),
      ('/service/follow', service.Follow),
      ('/service/unfollow', service.UnFollow)
      ])
  run_wsgi_app(application)

if __name__ == '__main__':
  main()
