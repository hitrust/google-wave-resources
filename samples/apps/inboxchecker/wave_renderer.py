import blip_renderer
import logging

def render_wavelet(wavelet):
  output = render_thread(wavelet.root_thread, 1)
  return output

def render_thread(thread, indent):
  output = []
  for blip in thread.blips:
    margin = indent * 10
    output.append('<div style="margin-left:%spx">' % margin)
    output.append(render_blip(blip, indent))
    output.append('</div>\n')
  return ''.join(output)

def render_blip(blip, indent):
  output = []
  output.append('<div style="border-radius: 5px; border:1px dotted grey; padding: 3px; margin: 2px">')
  output.append(blip_renderer.to_html(blip))
  output.append('</div>\n')
  for thread in blip.reply_threads:
    output.append(render_thread(thread, (indent+1)))
  return ''.join(output)
