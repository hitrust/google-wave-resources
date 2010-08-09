# Copyright (C) 2010 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

__authors__ = ['christian.plesner.hansen@gmail.com (Christian Plesner Hansen)']

import cgi
import traverse
import models
import urllib
from waveapi import blip, element

# Escape raw text so it can be included in an HTML document.
def escape(text):
  return cgi.escape(text).encode('ascii', 'xmlcharrefreplace')


# This visitor dispatches events appropriately to the elements, ranges and
# annotations that are active on the blip.
class EmitVisitor(traverse.HtmlVisitor):

  def __init__(self):
    self.out_ = []
    # This is used to not emit line breaks at the beginning of paragraphs.
    self.prevent_break_ = False
    self.prevent_only_one_break_ = True
    # This is used to suppress the text that contains the title
    self.in_title_ = False

  def on_element_range_start(self, range_type, indent):
    range_type.on_start(self, indent)
  
  def on_element_range_end(self, range_type, indent):
    range_type.on_end(self, indent)

  def on_element_start(self, element):
    element.on_start(self)

  def on_element_end(self, element):
    element.on_end(self)

  def on_annotation_start(self, annotation):
    annotation.on_start(self)
  
  def on_annotation_end(self, annotation):
    annotation.on_end(self)
  
  def on_text(self, text):
    self.append(escape(text))
  
  def output(self):
    return "".join(self.out_)
  
  def append_paragraph(self, str):
    self.prevent_break_ = True
    self.prevent_only_one_break_ = True
    self.out_.append(str)
  
  def append_break(self, str):
    if not self.in_title_:
      if self.prevent_break_:
        if self.prevent_only_one_break_:
          self.prevent_break_ = False
      else:
        self.out_.append(str)
  
  def on_start_title(self):
    self.in_title_ = True
  
  def on_end_title(self):
    self.in_title_ = False
    self.prevent_break_ = True
    self.prevent_only_one_break_ = False
  
  def append(self, str):
    if not self.in_title_ and str != "\n":
      self.prevent_break_ = False
      self.out_.append(str)


# The type of a range of elements.  For instance, a range of 'li' elements have
# an UnorderedListRangeType object associated with them that take care of
# inserting surrounding <ul>...</ul> tags as appropriate.
class RangeType(object):
  
  def __init__(self, id):
    self.id_ = id
  
  def __eq__(self, other):
    return self.id_ == other.id_
  
  def on_start(self, out, indent):
    pass
  
  def on_end(self, out, indent):
    pass


class SpanTag(object):

  def __init__(self, style):
    self.style_ = style

  def on_start(self, out, annotation):
    return out.append("<span style=\"%s\">" % (self.style_ % annotation.value()))

  def on_end(self, out, marker):
    return out.append("</span>")


class AnchorTag(object):

  def on_start(self, out, annotation):
    return out.append('<a href="%s" target="_blank">' % annotation.value())

  def on_end(self, out, annotation):
    return out.append("</a>")


class WaveLinkTag(object):
  
  WAVE_LINK = '<a href="https://blogspotty.appspot.com/server/waveLink?waveid=%(waveid)s" target="_blank">'
  
  def on_start(self, out, annotation):
    waveid = annotation.value()
    connection = models.Connection.get(waveid)
    if connection and connection.html_link:
      # If the wave has already been published we can just emit a link to it.
      out.append('<a href="%s" target="_blank">' % connection.html_link)
    else:
      # If the wave has not been published as a blog we let the server deal with
      # it.  That way we can redirect to the corresponding blog post if the wave
      # is published in the future.
      out.append(WaveLinkTag.WAVE_LINK % {'waveid': urllib.quote(waveid)})
  
  def on_end(self, out, annotation):
    out.append("</a>")


class TitleHandler(object):
  
  def on_start(self, out, annotation):
    out.on_start_title()
  
  def on_end(self, out, annotation):
    out.on_end_title()


_MANUAL_LINK = 'link/manual'
_WAVE_LINK = 'link/wave'
_AUTO_LINK = 'link/auto'
_TITLE = 'conv/title'


_TAG_MAP = {
  blip.Annotation.FONT_WEIGHT: SpanTag('font-weight: %s;'),
  blip.Annotation.FONT_STYLE: SpanTag('font-style: %s;'),
  blip.Annotation.TEXT_DECORATION: SpanTag('text-decoration: %s;'),
  blip.Annotation.BACKGROUND_COLOR: SpanTag('background: %s;'),
  blip.Annotation.FONT_FAMILY: SpanTag('font-family: %s;'),
  blip.Annotation.COLOR: SpanTag('color: %s;'),
  blip.Annotation.FONT_SIZE: SpanTag('font-size: %s;'),
  _MANUAL_LINK: AnchorTag(),
  _AUTO_LINK: AnchorTag(),
  _WAVE_LINK: WaveLinkTag(),
  _TITLE: TitleHandler()
}


class AnnotationAdapter(object):
  
  def __init__(self, tag, annotation):
    self.tag_ = tag
    self.annotation_ = annotation

  def start(self):
    return self.annotation_.start
  
  def end(self):
    return self.annotation_.end
  
  def value(self):
    return self.annotation_.value
  
  def on_start(self, out):
    self.tag_.on_start(out, self)
  
  def on_end(self, out):
    self.tag_.on_end(out, self)
  
  @staticmethod
  def adapt(annotation):
    name = annotation.name
    tag = _TAG_MAP.get(name, None)
    if tag:
      return AnnotationAdapter(tag, annotation)


class ElementAdapter(object):
  
  def __init__(self, element, start, end):
    self.element_ = element
    self.start_ = start
    self.end_ = end
  
  def element(self):
    return self.element_
  
  def start(self):
    return self.start_
  
  def end(self):
    return self.end_
  
  def enclose_in_ranges(self):
    return False
  
  def on_start(self, out):
    pass
  
  def on_end(self, out):
    pass
  
  @staticmethod
  def adapt(element, start, end):
    class_type = element.class_type
    if class_type == LineAdapter.CLASS_TYPE:
      return LineAdapter(element, start, end)
    elif class_type == GadgetAdapter.CLASS_TYPE:
      return GadgetAdapter.adapt(element, start, end)
    elif class_type == AttachmentAdapter.CLASS_TYPE:
      return AttachmentAdapter.adapt(element, start, end)
    else:
      return ElementAdapter(element, start, end)


class AttachmentAdapter(ElementAdapter):
  
  CLASS_TYPE = 'ATTACHMENT'
  
  @staticmethod
  def adapt(element, start, end):
    mime_type = element.mimeType
    Handler = _ATTACHMENT_MIME_TYPE_HANDLERS.get(element.mimeType, None)
    if Handler:
      return Handler(element, start, end)
    else:
      return AttachmentAdapter(element, start, end)


class ImageRangeType(RangeType):
  
  def __init__(self):
    super(ImageRangeType, self).__init__('img')
  
  def on_start(self, out, indent):
    out.append_paragraph(ImageAdapter.RANGE_START)
  
  def on_end(self, out, indent):
    out.append_paragraph(ImageAdapter.RANGE_END)


class ImageAdapter(AttachmentAdapter):

  RANGE_TYPE = ImageRangeType()
  WIDTH = 200
  HEIGHT = 150

  def on_start(self, out):
    url = self.element().attachmentUrl
    caption = self.element().caption
    values = {
      'url': url,
      'width': ImageAdapter.WIDTH,
      'height': ImageAdapter.HEIGHT
    }
    if caption:
      template = ImageAdapter.WITH_CAPTION_TEMPLATE
      values['caption'] = caption
    else:
      template = ImageAdapter.NO_CAPTION_TEMPLATE
    out.append(template % values)
  
  def enclose_in_ranges(self):
    return True
  
  def range_type(self):
    return ImageAdapter.RANGE_TYPE
  
  def indent(self):
    return 0

  RANGE_START = """
<table align="center" cellpadding="0" cellspacing="0" style="margin-left: auto; margin-right: auto; text-align: center;">
  <tr>
"""
  RANGE_END = """
  </tr>
</table>
"""

  NO_CAPTION_TEMPLATE = """
<td>
  <div class="separator" style="margin: 0 .5em 0 .5em; text-align: center;">
    <img border="0" height="%(height)i" src="%(url)s" width="%(width)i" />
  </div>
</td>
"""

  WITH_CAPTION_TEMPLATE = """
<td>
  <table align="center" cellpadding="0" cellspacing="0" class="tr-caption-container" style="margin: 0 .5em 0 .5em;">
    <tbody>
      <tr>
        <td style="text-align: center;">
          <a href="%(url)s" imageanchor="1" style="margin-left: auto; margin-right: auto;">
            <img border="0" height="%(height)i" src="%(url)s" width="%(width)i" />
          </a>
        </td>
      </tr>
      <tr>
        <td class="tr-caption" style="text-align: center;">
          %(caption)s
        </td>
      </tr>
    </tbody>
  </table>
</td>
"""


_ATTACHMENT_MIME_TYPE_HANDLERS = {
  'image/jpeg': ImageAdapter
}


class GadgetAdapter(ElementAdapter):
  
  CLASS_TYPE = 'GADGET'
  ALWAYS_SHOW_PLACEHOLDERS = False
  
  def on_start(self, out):
    properties = []
    element = self.element()
    for key in element.keys():
      properties.append("<li>%s: %s</li>" % (key, element.get(key)))
    out.append(GadgetAdapter.UNKNOWN_TEMPLATE % {
      'url': element.url,
      'properties': "".join(properties)
    })

  UNKNOWN_TEMPLATE = """
<p>
  <div style="padding: 10px; width: 480px; border: 1px dashed #707070; background: #e0e0e0; color: #707070">
    Placeholder for <code>%(url)s</code>.
    <ul>
      %(properties)s
    </ul>
  </div>
</p>
"""
  
  @staticmethod
  def adapt(element, start, end):
    url = element.url
    Handler = _GADGET_URL_HANDLERS.get(url, None)
    if Handler and not GadgetAdapter.ALWAYS_SHOW_PLACEHOLDERS:
      return Handler(element, start, end)
    else:
      return GadgetAdapter(element, start, end)


class YouTubeAdapter(GadgetAdapter):
  
  WIDTH = 480
  HEIGHT = 385
  
  def on_start(self, out):
    id = 'foo' # TODO: get the actual video id
    out.append(YouTubeAdapter.TEMPLATE % {
      'id': id,
      'width': YouTubeAdapter.WIDTH,
      'height': YouTubeAdapter.HEIGHT
    })
  
  TEMPLATE = """
<object width="%(width)i" height="%(height)i">
  <param name="movie" value="http://www.youtube.com/v/%(id)s;hl=en_US&fs=1&border=1"></param>
  <param name="allowFullScreen" value="true"></param>
  <param name="allowscriptaccess" value="always"></param>
  <embed src="http://www.youtube.com/v/%(id)s&hl=en_US&fs=1" type="application/x-shockwave-flash" allowscriptaccess="always" allowfullscreen="true" width="%(width)i" height="%(height)i">
  </embed>
</object>  
"""


class MappyAdapter(GadgetAdapter):
  
  WIDTH = 480
  HEIGHT = 385
  
  MAPTYPES = {'m': 'roadmap', 'k': 'satellite', 'h': 'hybrid'}
  
  def on_start(self, out):
    [lat, lng] = self.element().center[1:-2].split(',')
    zoom = self.element().zoom
    maptype = MappyAdapter.MAPTYPES.get(self.element().get('maptype', 'm'), 'roadmap')
    out.append(MappyAdapter.TEMPLATE % {
      'lat': lat,
      'lng': lng,
      'zoom': zoom,
      'width': MappyAdapter.WIDTH,
      'height': MappyAdapter.HEIGHT,
      'maptype': maptype
    })
  
  TEMPLATE = """
<iframe frameborder="0" marginwidth="0" marginheight="0" border="0"
        style="border:0;margin:0;width:%(width)ipx;height:%(height)ipx;"
        src="http://www.google.com/uds/modules/elements/mapselement/iframe.html?maptype=%(maptype)s&latlng=%(lat)s,%(lng)s&zoom=%(zoom)s" scrolling="no" allowtransparency="true">
</iframe>
"""


_GADGET_URL_HANDLERS = {
  'http://wave-api.appspot.com/public/gadgets/youtube/youtube.xml': YouTubeAdapter,
  'http://google-wave-resources.googlecode.com/svn/trunk/samples/extensions/gadgets/mappy/map_v2.xml': MappyAdapter
}


class UnorderedListRangeType(RangeType):
  
  def __init__(self):
    super(UnorderedListRangeType, self).__init__('ul')
  
  def on_start(self, out, indent):
    out.append_paragraph("<ul>")
  
  def on_end(self, out, indent):
    out.append_paragraph("</ul>")


class AlignedLineRangeType(RangeType):
  
  def __init__(self, alignment):
    super(AlignedLineRangeType, self).__init__(alignment)
    self.alignment_ = alignment

  def get_tag(self, indent):
    if indent == 0:
      return 'p'
    else:
      return 'blockquote'
  
  def on_start(self, out, indent):
    tag = self.get_tag(indent)
    out.append_paragraph('<%s style="text-align: %s;">' % (tag, self.alignment_))

  def on_end(self, out, indent):
    out.append_paragraph('</%s>' % self.get_tag(indent))


class LineAdapter(ElementAdapter):

  CLASS_TYPE = 'LINE'

  def __init__(self, element, start, end):
    super(LineAdapter, self).__init__(element, start, end)
    self.range_type_ = LineAdapter.get_range_type(element)

  def enclose_in_ranges(self):
    return self.range_type_ != None

  def range_type(self):
    return self.range_type_

  def on_start(self, out):
    type = self.element().lineType
    if not type:
      # Plain line elements, with or without alignment, are handled by the range
      # type.  The individual lines just have to be separated.
      out.append_break('<br />')
    else:
      align = self.element().alignment
      if align == element.Line.ALIGN_CENTER:
        text_align = 'center'
      elif align == element.Line.ALIGN_RIGHT:
        text_align = 'right'
      else:
        text_align = 'left'
      out.append_paragraph('<%s style="text-align: %s;">' % (type, text_align))

  def on_end(self, out):
    type = self.element().lineType
    if type:
      out.append_paragraph('</%s>' % type)

  def indent(self):
    value = self.element().indent
    if value is None:
      return 0
    else:
      return int(value)

  LI_RANGE_TYPE = UnorderedListRangeType()
  LEFT_RANGE_TYPE = AlignedLineRangeType('left')
  CENTER_RANGE_TYPE = AlignedLineRangeType('center')
  RIGHT_RANGE_TYPE = AlignedLineRangeType('right')

  @staticmethod
  def get_range_type(elm):
    line_type = elm.lineType
    if line_type is None:
      alignment = elm.alignment
      if alignment == element.Line.ALIGN_CENTER:
        return LineAdapter.CENTER_RANGE_TYPE
      elif alignment == element.Line.ALIGN_RIGHT:
        return LineAdapter.RIGHT_RANGE_TYPE
      else:
        return LineAdapter.LEFT_RANGE_TYPE
    elif line_type == 'li':
      return LineAdapter.LI_RANGE_TYPE
    else:
      return None
  


class BlipAdapter(object):
  
  def __init__(self, blip):
    self.blip_ = blip
    self.text_ = blip.text
  
  def elements(self):
    result = []
    prev = None
    elements = self.blip_._elements
    for pos_str in sorted(elements.keys()):
      element = elements[pos_str]
      pos = int(pos_str)
      if not prev is None:
        (prev_pos, prev_element) = prev
        result.append(ElementAdapter.adapt(prev_element, prev_pos, pos))
      prev = (pos, element)
    if not prev is None:
      (prev_pos, prev_element) = prev
      result.append(ElementAdapter.adapt(prev_element, prev_pos, self.length()))
    return result
  
  def annotations(self):
    result = []
    for annot in self.blip_.annotations:
      adapted = AnnotationAdapter.adapt(annot)
      if adapted:
        result.append(adapted)
    return result
  
  def length(self):
    return len(self.text_)
  
  def substring(self, start, end):
    return self.text_[start:end]


def to_html(blip):
  dispatcher = traverse.HtmlVisitorDispatcher(BlipAdapter(blip))
  visitor = EmitVisitor()
  dispatcher.dispatch(visitor)
  return visitor.output()
