import datetime
from google.appengine.ext import db
from google.appengine.api import users

class Collection(db.Model):
  owner = db.StringProperty()
  name = db.StringProperty()
  admin_wave = db.StringProperty()
  admin_wave_ser = db.TextProperty()
  toc_wave = db.StringProperty()
  toc_wave_ser = db.TextProperty()
  groups = db.StringListProperty()
  tags = db.StringListProperty()
  make_public = db.BooleanProperty()
  # URL for installer and avatar
  icon = db.StringProperty()

class ConferenceCollection(Collection):
  all_session_waves = db.StringListProperty()
  main_session_waves = db.StringListProperty()
  session_template = db.StringProperty()
  #spreadsheet, dapper, calendar
  datasource_type = db.StringProperty()
  # might be StringList in future
  datasource_url = db.StringProperty()

class SessionInfo(db.Model):
  id = db.StringProperty()
  moderator_id = db.StringProperty()
  wave_id = db.StringProperty()
  title = db.StringProperty()
  num_participants = db.IntegerProperty()
  num_blips = db.IntegerProperty()
  num_votes = db.IntegerProperty()
  num_questions = db.IntegerProperty()
