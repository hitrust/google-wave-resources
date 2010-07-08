import random
import logging

from waveapi import robot
from waveapi import events
from waveapi import appengine_robot_runner

ROBOT_KEY = 'colorizer'

def random_color(color='#'):
  if len(color) == 7:
    return color
  else:
    color = color + hex(random.randrange(0, 255))[2:][:1]
    return random_color(color)

def OnAnnotationChanged(event, wavelet):
  """Actual linking."""
  blip = event.blip
  text = blip.text
  # construct the todo outside of the loop to avoid
  # influencing what we're observing:
  todo = []
  for ann in blip.annotations:
    logging.info(ann.name)
    if ann.name == ROBOT_KEY:
      todo.append((ann.start, ann.end))
  for start, end in todo:
    logging.info(str(start))
    blip.range(start, end).clear_annotation(ROBOT_KEY)
    for x in range(start, (end-1)):
      color = random_color()
      blip.range(x, x+1).annotate('style/color', color)

if __name__ == '__main__':
  robotty = robot.Robot('Colorizer',
                        image_url='http://www.astro.cf.ac.uk/aboutus/forteachersandschools/resources/rainbow-th.jpg',
                        profile_url='')
  robotty.register_handler(events.AnnotatedTextChanged, OnAnnotationChanged, filter=ROBOT_KEY)
  robotty.register_handler(events.WaveletSelfAdded, OnAnnotationChanged)
  appengine_robot_runner.run(robotty, debug=True)
