from google.appengine.ext import db

class Ripple(db.Model):
  title = db.StringProperty()
  body = db.TextProperty()
  id = db.StringProperty()
  participants = db.StringListProperty()
  created = db.DateTimeProperty(auto_now_add=True)
  modified = db.DateTimeProperty(auto_now=True)

class Rippler(db.Model):
  user = db.StringProperty()
  following = db.StringListProperty()
  num = db.IntegerProperty(default=0)
  last_ripple = db.DateTimeProperty(auto_now=True)
  first_ripple = db.DateTimeProperty(auto_now_add=True)
  profile_wave_id = db.StringProperty()

def CreateRippler(user):
  rippler = Rippler()
  rippler.user = user
  return rippler

def GetRippler(user):
  query = db.Query(Rippler)
  query.filter('user =', user)
  rippler = query.get()
  return rippler

def GetOrCreateRippler(user):
  rippler = GetRippler(user)
  if rippler is None:
    rippler = CreateRippler(user)
  return rippler
