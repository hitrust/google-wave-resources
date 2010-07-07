import os

def GetGadgetUrl():
  return 'http://bug-triagey.appspot.com/web/gadget?nocache=true'

def GetServer():
  server = os.environ['SERVER_NAME']
  port = os.environ['SERVER_PORT']

  if port and port != '80':
    return 'http://%s:%s' % (server, port)
  else:
    return 'http://%s' % (server)
