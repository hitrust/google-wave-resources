import datetime
from google.appengine.ext import db
from google.appengine.api import users

class Conference(db.Model):
  owner = db.StringProperty()
  name = db.StringProperty()
  admin_wave = db.StringProperty()
  admin_wave_ser = db.TextProperty()
  toc_wave = db.StringProperty()
  toc_wave_ser = db.TextProperty()
  participants = db.StringListProperty()
  hashtag = db.StringProperty()
  tags = db.StringListProperty()
  make_public = db.BooleanProperty()
  # unconference or conference
  type = db.StringProperty()
  # URL for installer and avatar
  icon = db.StringProperty()
  include_savedsearch = db.BooleanProperty(default=True)
  include_newwave = db.BooleanProperty(default=True)
  session_waves = db.StringListProperty()
  #spreadsheet, dapper, calendar
  datasource_type = db.StringProperty()
  # might be StringList in future
  datasource_url = db.StringProperty()

class SessionInfo(db.Model):
  toc_wave = db.StringProperty()
  id = db.StringProperty()
  moderator_id = db.StringProperty()
  wave_id = db.StringProperty()
  title = db.StringProperty()
