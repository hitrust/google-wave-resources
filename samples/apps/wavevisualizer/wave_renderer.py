import logging


def render_wavelet(wavelet):
  output = render_thread(wavelet.root_thread, wavelet)
  return output

def render_thread(thread, wavelet):
  node = {}
  logging.info(thread)
  if len(thread.id) < 2:
    id = 'root'
  else:
    id = thread.id
  node['id'] = id
  node['name'] = 'thread:' + id
  node['data'] = {
      'snippet': str(len(thread.blips)) + ' blips',
      'type': 'thread'}
  node['children'] = []
  for blip in thread.blips:
    new_node = render_blip(blip, wavelet)
    node['children'].append(new_node)
  return node

def render_blip(blip, wavelet):
  node = {}
  node['id'] = blip.blip_id
  node['name'] = 'blip: ' + blip.blip_id
  url = 'http://wave.google.com/wave/waveref/%s/%s/~/conv+root/%s' % (wavelet.domain, wavelet.wave_id.split('!')[1], blip.blip_id)
  logging.info(url)
  node['data'] = {
      'snippet': blip.text[0:100],
      'type': 'blip',
      'url': url}
  node['children'] = []
  for thread in blip.reply_threads:
    new_node = render_thread(thread, wavelet)
    node['children'].append(new_node)
  return node
