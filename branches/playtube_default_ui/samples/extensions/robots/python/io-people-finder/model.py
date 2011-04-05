from geo.geomodel import GeoModel
from google.appengine.ext import db


class Person(GeoModel):
  """Storage for a single person.

  key = viewer_id

  location is inherited from GeoModel.
  """
  name = db.StringProperty()
  thumbnail = db.StringProperty()
  country = db.StringProperty()

class GTUG(GeoModel):
  """
  key = name
  """
  gtugid = db.IntegerProperty()
  url = db.StringProperty()
