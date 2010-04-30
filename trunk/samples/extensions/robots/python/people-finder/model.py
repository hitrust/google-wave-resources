from geo.geomodel import GeoModel
from google.appengine.ext import db


class Profile(GeoModel):
  """Storage for a single profile.
  
  key = wave_id, for the Profile Wave
  
  location is inherited from GeoModel.
  """
  name = db.StringProperty()
  address = db.StringProperty()
  creator = db.StringProperty()
  interests = db.StringListProperty()

class GTUG(GeoModel):
  """
  key = name
  """
  gtugid = db.IntegerProperty()
  url = db.StringProperty()
