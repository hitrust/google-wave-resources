from waveapi import events
from waveapi import robot
from waveapi import element
from waveapi import appengine_robot_runner
import logging


def OnWaveletSelfAdded(event, wavelet):
  wavelet.title = 'Blog post for review: Title here'
  blip = wavelet.root_blip
  AppendLine(blip)
  AppendLabel(blip, 'Status')
  gadget = element.Gadget(url='http://blog-reviewey.appspot.com/gadget.xml')
  blip.append(gadget)
  AppendLine(blip)
  AppendLabel(blip, 'Authors')
  AppendLine(blip)
  AppendLabel(blip, 'Body')
  AppendLine(blip)

def AppendLabel(blip, label):
  blip.append(label, [('style/fontWeight', 'bold')])
  blip.append(':', [('style/fontWeight', 'bold')])

def AppendLine(blip):
  blip.append(element.Line())
  blip.append(element.Line())

if __name__ == '__main__':
  myRobot = robot.Robot('Blog Reviewey')
  myRobot.register_handler(events.WaveletSelfAdded, OnWaveletSelfAdded)
  appengine_robot_runner.run(myRobot)
