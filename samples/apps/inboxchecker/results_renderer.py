from time import gmtime, strftime

def render(results):
  html = '%s, (%s)<br>' % (results.query, results.num_results)
  for digest in results.digests:
    url = 'http://wave.google.com/wave/#restored:wave:%s' % digest.wave_id
    url = '/app/fetchwave?wave_id=%s' % digest.wave_id.replace('+', '%252B')
    html += '<a href="%s"><b>%s</b></a><br>%s' % (url, digest.title, digest.snippet)
    date = strftime("%a, %d %b %Y %H:%M:%S", gmtime(digest.last_modified/1000))
    html += '%s/%s:%s' % (str(digest.unread_count), str(digest.blip_count),
                            date)
    participants = [p for p in digest.participants]
    html += '(%s)' % ','.join(participants)
    html += '<br><br>'
  return html
