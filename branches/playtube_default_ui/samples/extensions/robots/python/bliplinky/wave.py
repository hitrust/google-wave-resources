from waveapi import events
from waveapi import element
from waveapi import robot
from waveapi import appengine_robot_runner
import logging

def OnBlipSubmitted(event, wavelet):
  blip = event.blip
  blip_id = blip.blip_id

  # If we already linked to the blip, then do nothing
  if blip_id in wavelet.data_documents.keys():
    return
  # If this is the root blip, then do nothing
  if blip_id == wavelet.root_blip.blip_id:
    return

  # Find first line of blip to serve as title
  # Start after obligatory '\n'
  header_start = 1
  # Default to ending after all the text
  header_end = len(blip.text)
  for start, end in blip.all(element.Line):
   # If we're past the first obligatory Line element,
   # assume we've seen some useful text and mark as end
   if start > 1:
     header_end = start
     break
  title = blip.text[header_start:header_end]

  # Add link to root blip to blip
  # Format is waveid://google.com/w+8hpKCBQNA/~/conv+root/b+Qq3cIxvuQ 
  domain = wavelet.domain
  wave_id = wavelet.wave_id.split('!')[1]
  blip_ref = 'waveid://%s/%s/~/conv+root/%s/' % (domain, wave_id, blip_id)
  wavelet.root_blip.append(element.Line(line_type='li', indent=1))
  wavelet.root_blip.append(title, [('link/manual', blip_ref)])
  wavelet.root_blip.append('', [('link/manual', None)])
  wavelet.data_documents[blip_id] = 'linked'


if __name__ == '__main__':
  robotty = robot.Robot('BlipLinky',
                        profile_url='')
  robotty.register_handler(events.BlipSubmitted, OnBlipSubmitted)
  appengine_robot_runner.run(robotty)
