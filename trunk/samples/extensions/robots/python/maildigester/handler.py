import logging
from email.header import decode_header
import urllib

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import mail_handlers
from google.appengine.ext import db
from django.utils import simplejson
from google.appengine.api import urlfetch


from waveapi import appengine_robot_runner
from waveapi import element
from waveapi import events
from waveapi import ops
from waveapi import robot

import credentials

# the robot
robotty = None

class MailDigestWave(db.Model):
  prefix = db.StringProperty()
  wave_json = db.TextProperty()
  wave_id = db.StringProperty()

class MailReceiver(mail_handlers.InboundMailHandler):
   def receive(self, message):
    receiver = urllib.unquote(self.request.path.split('_ah/mail/')[1])
    prefix = receiver.split('@')[0]
    sender = CleanAddress(message.sender)
    subject = CleanSubject(message.subject)
    logging.info('Received mail message from %r to %r: %r', sender, receiver, subject)
    bodies = message.bodies(content_type='text/plain')
    all_body = ''
    for body in bodies:
      all_body += body[1].decode()
    all_body.encode('utf-8')
    logging.info(all_body)
    return

    query = db.Query(MailDigestWave)
    query.filter('prefix = ', prefix)
    maildigest = query.get()
    if maildigest is None:
      maildigest = MailDigestWave()
      maildigest.prefix = prefix
      # Try to figure out wave address
      if sender.find('gmail.com') > -1:
        wave_address = sender.split('@')[0] + '@googlewave.com'
      else:
        wave_address = sender
      participants = [wave_address]
      digest_wave = robotty.new_wave('googlewave.com',
                                    participants, submit=True)
      maildigest.wave_id = digest_wave.wave_id
      maildigest.wave_json = simplejson.dumps(digest_wave.serialize())
      maildigest.put()
      digest_wave.title = 'Digest for emails sent to: %s' % receiver
      robotty.submit(digest_wave)

    # Update digest wave
    UpdateDigestWave(maildigest, subject, all_body)

def CleanAddress(address):
  if '<' in address and '>' in address:
    cleaned_address = address[address.find('<') + 1:address.find('>')]
  else:
    cleaned_address = address
  return cleaned_address

def CleanSubject(subject):
  decoded_header = decode_header(subject)
  if decoded_header[0][1]:
    cleaned_subject = decoded_header[0][0].decode(decoded_header[0][1])
  else:
    cleaned_subject = decoded_header[0][0]
  return cleaned_subject

def UpdateDigestWave(maildigest, subject, body):
  digest_wave = robotty.blind_wavelet(maildigest.wave_json)
  new_blip = digest_wave.reply('\n')
  new_blip.append(subject, [('style/fontWeight', 'bold')])
  new_blip.append('\n')
  new_blip.append(body, [('style/fontWeight', None)])
  robotty.submit(digest_wave)

if __name__ == '__main__':
  robotty = robot.Robot('Mail Digester',
                        image_url='http://knol.google.com/k/-/-/1pde6452vn7is/whbr04/email5.gif')
  robotty.set_verification_token_info(credentials.VERIFICATION_TOKEN,
                                    credentials.ST)
  robotty.setup_oauth(credentials.KEY, credentials.SECRET,
                    server_rpc_base=credentials.RPC_BASE)
  mail_url, mail_handler = MailReceiver.mapping()
  appengine_robot_runner.run(robotty, debug=True, extra_handlers=[
      (mail_url, mail_handler)
  ]
)
