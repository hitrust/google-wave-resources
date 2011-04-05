from waveapi import events
from waveapi import robot
from waveapi import element
from waveapi import appengine_robot_runner
import logging

PROCESSED = 'bliperator/processed'

def OnWaveletSelfAdded(event, wavelet):
  """Invoked when the robot has been added."""
  ProcessWave(wavelet)

def OnBlipSubmitted(event, wavelet):
  ProcessWave(wavelet)

def ProcessWave(wavelet):
  # If we already processed, don't process again
  if PROCESSED in wavelet.data_documents.keys():
    return

  blip = wavelet.root_blip
  blip.append(element.Line())
  # Find all the line elements
  todo = []
  for start, end in blip.all(element.Line):
    todo.append(start)
  # Sort by which line is first
  todo.sort()
  # Skip first 2 lines, since that's the title
  todo = todo[2:]
  # Reverse sort, so that we process bottom-up
  # and don't worry about our indices getting skewed
  todo.reverse()
  for position in todo:
    inline_blip = blip.insert_inline_blip(position)
    inline_blip.append('Rate this!')
    inline_blip.append(element.Gadget(url='http://www.nebweb.com.au/wave/likey.xml'))

  # Mark that we've procesed it
  wavelet.data_documents[PROCESSED] = 'done'



if __name__ == '__main__':
  myRobot = robot.Robot('Inline Bliperator')
  myRobot.register_handler(events.WaveletSelfAdded, OnWaveletSelfAdded)
  myRobot.register_handler(events.BlipSubmitted, OnBlipSubmitted)
  appengine_robot_runner.run(myRobot)
