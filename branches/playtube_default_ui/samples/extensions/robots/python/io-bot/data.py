class Conference():
  # each conference should have a list of sessions
  # each session should have title, and other optional info
  def __init__(self, sessions=None):
    if sessions is None:
      self.sessions = []
    else:
      self.sessions = sessions

class Session():
  def __init__(self, name='Untitled', link=None, speakers=None, time=None, day=None,
               location=None, description=None, id=None, prereqs=None,
               track=None, type=None, hashtag=None, tags=None, waveid=None):
    self.name = name
    self.link = link
    self.id = id
    self.time = time
    self.day = day
    self.location = location
    self.description = description
    self.prereqs = prereqs
    self.tags = tags or []
    self.hashtag = hashtag
    self.track = track
    self.type = type
    # list of speakers
    self.speakers = speakers or []
    self.waveid = waveid

  def __str__(self):
    template_str = """name: %s, link: %s, id: %s, time: %s, day: %s, location: %s,
    description: %s, prereqs: %s, tags: %s, hashtag: %s, track: %s, type: %s"""
    new_str = template_str % (self. name, str(self.link), str(self.id), str(self.time),
     str(self.day), unicode(self.location), unicode(self.description),
     unicode(self.prereqs), str(self.tags), str(self.hashtag), str(self.track),
     str(self.type))
    return new_str

class Speaker():
  def __init__(self, name, link=None, description=None):
    self.name = name
    self.link = link
    self.description = description
