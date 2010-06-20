import logging
import re
import cgi

from waveapi import element

def Log(message, string):
  logging.info(message + ': ' + string)

def ToText(blip):
  format = "-------------------------------\n\
Creator: %s \n\
Contributors: %s \n\
Last Modified: %s \n\
Content: %s\n\
-------------------------------\n"
  text = format % (blip.creator, ', '.join(blip.contributors),
                   blip.last_modified_time, blip.text)
  return text

def ToCSSProperty(annotation_name):
  split_annotation = annotation_name.split('/')
  style_type = split_annotation[1]
  css_rule = re.sub(r'([A-Z])','-\\1', style_type, 1)
  css_rule = css_rule.lower()
  return css_rule

def ToCharacter(text):
  return cgi.escape(text)

def ToHTML(blip):
  # Take in a blip, convert to HTML
  indices = []
  text = blip.text
  i = 0
  while i < len(text):
    indices.insert(i, {'index': i, 'character': ToCharacter(text[i]),
                       'element': None, 'linkStarts': [], 'linkEnds': [],
                       'annotationStarts': [], 'annotationEnds': []})
    i += 1

  for annotation in blip.annotations:
    start = annotation.start
    end = annotation.end
    if 'style' in annotation.name or annotation.name == 'conv/title':
      #only process these for now
      indices[start]['annotationStarts'].append(annotation)
      indices[min(end, len(text)-1)]['annotationEnds'].append(annotation)
    if 'link' in annotation.name:
      Log('Link: ', annotation.value)
      indices[start]['linkStarts'].append(annotation)
      indices[min(end, len(text) -1)]['linkEnds'].append(annotation)

  for elem_ind, elem in blip._elements.items():
    indices[elem_ind]['element'] = elem

  html = ''
  first_line = len(text.split('\n')[1])+1
  active_annotations = []
  open_span = False
  line_started = False
  for data in indices[first_line:]:
    closed_span = False
    saw_new = False
    if data['element']:
      elem = data['element']
      if isinstance(elem, element.Line):
        html += '<br>'
        line_started = True

    if len(data['annotationEnds']) > 0:
      html = html + '</span>'
      closed_span = True
      open_span = False

    if len(data['linkEnds']) > 0:
      html += '</a>'
    if len(data['linkStarts']) > 0:
      link_starts = data['linkStarts']
      html += '<a href="' + link_starts[0].value + '">'

    annotation_starts = data['annotationStarts']
    if len(annotation_starts) > 0:
      active_annotations.extend(annotation_starts)
      saw_new = True
      if not closed_span:
        html += '</span>'

    if saw_new or closed_span:
      html += '<span style="'
      current_annotations = []
      for annotation in active_annotations:
        if annotation.end > data['index']:
          if annotation.name == 'conv/title':
            css_property = 'style/fontWeight'
            css_value = 'bold'
          else:
            css_property = ToCSSProperty(annotation.name)
            css_value = annotation.value
          html += css_property + ':' + css_value + ';'
      html += '">'
      open_span = True

    # Account for whitespace at beginning of lines
    # by keeping track of when a line starts and when first text
    # starts after the line.
    character = data['character']
    if line_started and character.isspace():
      html = html + '&nbsp;'
    else:
      line_started = False
      html = html + data['character']

    span_now = False
  if open_span:
    html += '</span>'

  Log('html', html)
  return html
