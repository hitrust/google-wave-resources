# Constants used for keys in datadocs or custom annotations
PREFIX = 'confrenzy/'
LINK_ADDED = PREFIX + 'new-wave/linkadded'
SESSION_ID = PREFIX + 'session-id'
WAVE_TYPE  = PREFIX + 'wavetype'
OLD_TITLE = PREFIX + 'oldtitle'
CONFERENCE_ID = PREFIX + 'conference-id'

def TOC_LINK(wave):
  return PREFIX + 'toc/' + wave.wave_id

def MAIN_PROXY(conference):
  return '%s-mainwave' % str(conference.key().id())
