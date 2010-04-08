from waveapi import events
from waveapi import robot
from waveapi import blip
from waveapi import wavelet
from waveapi import appengine_robot_runner
import logging

def OnWaveletSelfAdded(event, wl):
  bl = wl.root_blip
  if len(bl.text) > 5:
    return
  wl.title = 'Sample Wave'

  # Repeatedly call function to append different single annotations to lines of text
  appendAnnotatedText(bl, 'BACKGROUND_COLOR=pink', blip.Annotation.BACKGROUND_COLOR, 'pink')
  appendAnnotatedText(bl, 'COLOR=green', blip.Annotation.COLOR, 'green')
  appendAnnotatedText(bl, 'FONT_FAMILY=serif', blip.Annotation.FONT_FAMILY, 'serif')
  appendAnnotatedText(bl, 'FONT_STYLE=italic', blip.Annotation.FONT_STYLE, 'italic')
  appendAnnotatedText(bl, 'FONT_WEIGHT=bold', blip.Annotation.FONT_WEIGHT, 'bold')
  appendAnnotatedText(bl, 'TEXT_DECORATION=underline', blip.Annotation.TEXT_DECORATION, 'underline')
  appendAnnotatedText(bl, 'link/manual=google.com', 'link/manual', 'http://www.google.com')

  # Append a line of text with multiple annotations
  bl.append('Everything!\n', bundled_annotations=[
                (blip.Annotation.BACKGROUND_COLOR, 'pink'),
                (blip.Annotation.COLOR, 'green'),
                (blip.Annotation.FONT_FAMILY, 'serif'),
                (blip.Annotation.FONT_STYLE, 'italic'),
                (blip.Annotation.FONT_WEIGHT, 'bold'),
                (blip.Annotation.TEXT_DECORATION, 'underline'),
                ('link/manual', 'http://www.google.com')])

# Append text to a blip with a single bundled annotation
def appendAnnotatedText(bl, text, name, value):
  bl.append(text+'\n', bundled_annotations=[(name, value)])

if __name__ == '__main__':
  myRobot = robot.Robot('Role Test')
  myRobot.register_handler(events.WaveletSelfAdded, OnWaveletSelfAdded)
  appengine_robot_runner.run(myRobot)
