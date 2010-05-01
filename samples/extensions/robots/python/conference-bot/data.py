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
               location=None, description=None, id=None):
    self.name = name
    self.link = link
    self.id = id
    self.time = time
    self.day = day
    self.location = location
    self.description = description
    # list of speakers
    self.speakers = speakers or []

  def __str__(self):
    return 'name: %s, link: %s, id: %s, time: %s, day: %s, location: %s, description: %s' % (self. name, str(self.link), str(self.id), str(self.time), str(self.day), unicode(self.location), unicode(self.description))

class Speaker():
  def __init__(self, name, link=None, description=None):
    self.name = name
    self.link = link
    self.description = description
