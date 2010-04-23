"""
Copyright 2009 Google Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

     Unless required by applicable law or agreed to in writing, software
     distributed under the License is distributed on an "AS IS" BASIS,
     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
     See the License for the specific language governing permissions and
     limitations under the License.
"""

from waveapi import events
from waveapi import robot
from waveapi import appengine_robot_runner

from pygments import lexers
from pygments import highlight
from pygments.formatter import Formatter
from pygments.token import Token

COLORS = {
  Token.Keyword:("#335588", "bold"),
  Token.Comment:("#7777FF", ""),
  Token.Literal.String:("#007000", ""),
  Token.Operator:("#663388", "bold"),
  Token.Punctuation:("#663388", ""),
  Token.Name.Function:("#550000", ""),
  Token.Name.Namespace:("#550000", ""),
  Token:("", "") }

def OnBlipSubmit(event, wavelet):
  HighlightBlip(event.blip)

def HighlightBlip(blip):
  """Highlight a blip if we find a filename or #!Language"""
  text = blip.text[:]
  stripped_text = text.lstrip()
  if stripped_text[:2] == "#!":
    lang = stripped_text[2:20].split()
    if len(lang) > 0:
      lang = lang[0]
      # only highlight after the #!language
      HighlightRange(blip, text.find(lang) + len(lang), len(blip.text), lang)
  elif stripped_text.startswith("file:"):
    idx = stripped_text.find('\n')
    if idx >= 0:
      lang = stripped_text[stripped_text.find(":")+1:idx]
      HighlightRange(blip, len(text) - len(stripped_text) + idx+1,
                     len(blip.text), lang)

def GetLexer(lang):
  """ Attempts to find a lexer according to lang.

  This will attempt to interpret lang as a #!language and failover
  to using lang as a filename.
  """
  try:
    lex = lexers.get_lexer_by_name(lang)
    return lex
  except:
    pass
  filename = "Filename." + lang
  try:
    lex = lexers.guess_lexer_for_filename(filename, "")
    return lex
  except:
    pass
  return None

def HighlightRange(blip, start, end, lang):
  """ Highlight within a specific range within the text of a blip """
  # adjust range to cut leading whitespace
  otext = blip.text[start:end]
  text = otext.lstrip()
  start = start + len(otext) - len(text)
  range = blip.range(start, end)

  # Set the text to an unknown language so Spelly will
  # leave it alone
  range.annotate("lang", "xx")
  # Change to a monospace font
  range.annotate("style/fontFamily", "Courier New,monospace")
  # Change to a monospace font
  range.annotate("style/color", "#000000")
  # Change to a monospace font
  range.annotate("style/fontWeight", "")

  # find the right lexer for this language
  lex = GetLexer(lang)
  if lex:
    formatter = WaveFormatter()
    formatter.setBlipChunk(blip, start, text)
    highlight(text, lex, formatter)

class WaveFormatter (Formatter):
  """ Formatter for Pygments library to apply syntax highlighting to a blip """
  def setBlipChunk(self, blip, end, text):
    self.blip = blip
    self.end = end
    self.text = text

  def annotateToken(self, tokenstring, color, bold=None):
    if not color and not bold:
      return
    start = self.end
    end = len(tokenstring) + self.end
    therange = self.blip.range(start, end)
    if color:
      therange.annotate("style/color", color)
    if bold:
      therange.annotate("style/fontWeight", bold)

  def format(self, tokensource, outfile):
    for (tokentype, tokenstring) in tokensource:
      parents = tokentype.split()
      # token types are hierarchical
      # the list is in this order with the most specific last
      for tok in parents[::-1]:
        if tok in COLORS:
          (color, bold) = COLORS[tok]
          self.annotateToken(tokenstring, color, bold)
          break;
      self.end += len(tokenstring)
    return ""


def OnLoad(event, wavelet):
  RecAnnotateBlips(event.blip)

def RecAnnotateBlips(blip):
  """ Recursively traverse the wavelet tree"""
  HighlightBlip(blip)
  for child_blip in blip.child_blips:
    if child_blip:
      RecAnnotateBlips(child_blip)

if __name__ == '__main__':
  lexers.get_all_lexers()
  myRobot = robot.Robot('syntaxy2',
    image_url='',
    profile_url='')
  myRobot.register_handler(events.DocumentChanged, OnBlipSubmit)
  myRobot.register_handler(events.WaveletSelfAdded, OnLoad)
  appengine_robot_runner.run(myRobot)
