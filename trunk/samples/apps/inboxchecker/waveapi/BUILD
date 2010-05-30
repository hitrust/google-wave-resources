# Copyright 2009 Google Inc. All Rights Reserved.
# Author: davidbyttow@google.com (David Byttow)
#
# Package:
#   walkabout/externalagents/api
#
# Description:
#   Collects the files pushed to demetrius into a bundle.

# TODO(Douwe): Get these from third party:
ENTRIES = [
  FilesetEntry(srcdir="//walkabout/externalagents/api",
               files=glob([
                   '*.py',
                   'simplejson/*.py',
                   'simplejson/LICENSE',
                   'oauth/*.py',
                   'oauth/LICENSE',
               ]),
               destdir='src/waveapi'),
]

Fileset(name='source',
        entries=ENTRIES,
        out='bundle')

# the api thing as a library
py_library(name = "waveapi",
           srcs = [
                    "__init__.py",
                    "blip.py",
                    "element.py",
                    "errors.py",
                    "events.py",
                    "ops.py",
                    "robot.py",
                    "util.py",
                    "wavelet.py",
                  ],
           deps = [ "//pyglib",
                    "//third_party/py/simplejson",
                    "//third_party/py/oauth",
                  ])

py_binary(name = "commandline_robot_runner",
           srcs = [ "commandline_robot_runner.py" ],
           deps = [ ":waveapi" ])

# Tests
# =========================================================
py_test(name = "blip_test",
        srcs = [ "blip_test.py" ],
        tags = [ "manual" ],
        deps = [ ":waveapi" ])

py_test(name = "commandline_robot_runner_test",
        srcs = [ "commandline_robot_runner_test.py",
                 "commandline_robot_runner.py" ],
        deps = [ ":waveapi",
                 "//testing/pybase", ])

py_test(name = "element_test",
        srcs = [ "element_test.py" ],
        tags = [ "manual" ],
        deps = [ ":waveapi" ])

py_test(name = "ops_test",
        srcs = [ "ops_test.py" ],
        tags = [ "manual" ],
        deps = [ ":waveapi" ])

py_test(name = "robot_test",
        srcs = [ "robot_test.py" ],
        tags = [ "manual" ],
        deps = [ ":waveapi" ])

py_test(name = "wavelet_test",
        srcs = [ "wavelet_test.py" ],
        tags = [ "manual" ],
        deps = [ ":waveapi" ])
