from google.appengine.ext import db

class FAQ(db.Model):
  title = db.StringProperty()
  body = db.TextProperty()
  html = db.TextProperty()
  id = db.StringProperty()
  shortId = db.StringProperty()
  participants = db.StringListProperty()
  creator = db.StringProperty()
  created = db.DateTimeProperty(auto_now_add=True)
  faqs = db.ListProperty(db.Key)
  type = db.StringProperty()
  order = db.IntegerProperty(default=10)
