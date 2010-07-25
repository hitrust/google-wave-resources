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
    # Parse all the needed info from the message/request
    receiver = urllib.unquote(self.request.path.split('_ah/mail/')[1])
    prefix = receiver.split('@')[0]
    sender = CleanAddress(message.sender)
    if hasattr(message, 'subject'):
      subject = CleanSubject(message.subject)
    else:
      subject = 'untitled'
    text_bodies = message.bodies(content_type='text/plain')
    use_html = False
    if len(list(text_bodies)) > 0:
      body = CleanBodies(message.bodies)
    else:
      html_bodies = message.bodies(content_type='text/html')
      body = CleanHtmlBodies(message.bodies)
      use_html = True

    #logging.info('Received mail message from %r to %r: %r \n %r',
    #             sender, receiver, subject, body)

    # Check if prefix is already associated with a digest wave
    query = db.Query(MailDigestWave)
    query.filter('prefix = ', prefix)
    maildigest = query.get()
    if maildigest is None:
      # Try to figure out wave address of sender
      if sender == 'mail-noreply@google.com':
        sender = subject.split('from')[1].strip()
      if sender.find('gmail.com') > -1 or sender.find('googlemail.com') > -1:
        wave_address = sender.split('@')[0] + '@googlewave.com'
      else:
        wave_address = sender
      participants = [wave_address]
      # Create new wave
      digest_wave = robotty.new_wave(credentials.DOMAIN,
                                    participants, submit=True)
      # Save in datastore so we can recreate later
      maildigest = MailDigestWave()
      maildigest.prefix = prefix
      maildigest.wave_id = digest_wave.wave_id
      maildigest.wave_json = simplejson.dumps(digest_wave.serialize())
      maildigest.put()
      # Update the title and submit the change
      SetDigestWaveTitle(digest_wave, receiver)

    # Update digest wave
    UpdateDigestWave(maildigest, subject, body, use_html)

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
  cleaned_subject = cleaned_subject.replace('\t', ' ')
  cleaned_subject = cleaned_subject.replace('\r', ' ')
  return cleaned_subject

def CleanBodies(bodies):
  text_bodies = bodies(content_type='text/plain')
  all_body = ''
  for body in text_bodies:
    all_body += body[1].decode()
  all_body.encode('utf-8')
  # Replace characters that Wave breaks on
  all_body = all_body.replace('\t', ' ')
  all_body = all_body.replace('\r', '\n')
  return all_body

def CleanHtmlBodies(bodies):
  from html2text import html2text

  html_bodies = bodies(content_type='text/html')
  all_body = ''
  for body in html_bodies:
    all_body += body[1].decode()
  all_body.encode('utf-8')
  all_body = html2text(all_body)
  all_body = all_body.replace('\t', ' ')
  all_body = all_body.replace('\r', '\n')
  return all_body

def SetDigestWaveTitle(digest_wave, receiver):
  digest_wave.title = 'Digest for emails sent to: %s' % receiver
  try:
    robotty.submit(digest_wave)
  except urlfetch.DownloadError:
    robotty.submit(digest_wave)

def UpdateDigestWave(maildigest, subject, body, use_html=False):
  digest_wave = robotty.blind_wavelet(maildigest.wave_json)
  new_blip = digest_wave.reply('\n')
  new_blip.append(subject, [('style/fontWeight', 'bold')])
  new_blip.append('\n', [('style/fontWeight', None)])
  if use_html:
    new_blip.append_markup(body)
  else:
    new_blip.append(body)

  try:
    robotty.submit(digest_wave)
  except urlfetch.DownloadError:
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
