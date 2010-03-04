from google.appengine.ext import db

# Define our Models for the datastore

class ApplicationAuthor(db.Model):
  user = db.UserProperty()
  name = db.StringProperty()
  url = db.StringProperty(default='')
  googler = db.BooleanProperty(default=False)
  location = db.StringProperty(default='')
  latlng = db.GeoPtProperty()


class ApplicationIndex(db.Model):

  DEFAULT_SCHEMA_VERSION = 1

  max_index = db.IntegerProperty(default = 0)
  SCHEMA_VERSION = db.IntegerProperty(default=DEFAULT_SCHEMA_VERSION)

class Application(db.Model):
  """Application

  Entities of this type will store the information
  for each of the applications submitted to the gallery

  Properties:
    title: title of the application
    description: description of the application
    tech_details: technical details on the application
    author: The Google Accounts user who submitted the app
    url: url of the application
    source_url: url of the source
    tags: list of tags entered by author
    admin_tags: admins can tag apps, used for display in featured section
    thumbnail: True if there is an associated thumbnail
    screenshot: True if there is an associated screenshot
    created: date the application entry was created
    updated: date the application entry was updated
    avg_rating: avgerage rating shown as stars
    total_ratings: total number of ratings associated with application
    developer_key: the developer key for the application
    client_id: the client_id for the application
    comment_count: the number of comments associated with this application
  """

  UNREVIEWED = 0
  APPROVED = 1
  REJECTED = 2

  DEFAULT_SCHEMA_VERSION = 3

  APIS = ['Robots', 'Gadgets', 'Embed', 'Installer']
  LANGUAGES = ['Java', 'Python', 'JavaScript', 'ActionScript']
  api_v2 = db.BooleanProperty(default = False)
  author_ref = db.ReferenceProperty(ApplicationAuthor)
  author = db.UserProperty() # deprecated
  author_name = db.StringProperty() #deprecated
  author_url = db.StringProperty() #deprecated
  type = db.StringProperty()
  title = db.StringProperty()
  code_snippet = db.TextProperty()
  description = db.TextProperty()
  tech_details = db.TextProperty()
  url = db.StringProperty()
  api_usage = db.StringProperty(multiline = True)
  source_url = db.StringProperty()
  robot_email = db.StringProperty()
  gadget_xml = db.StringProperty()
  installer_xml = db.StringProperty()
  video_url = db.StringProperty()
  thumbnail = db.BooleanProperty(default = False)
  screenshot = db.BooleanProperty(default = False)
  tags = db.StringListProperty()
  apis = db.StringListProperty()
  languages = db.StringListProperty()
  created = db.DateTimeProperty(auto_now_add=True)
  updated = db.DateTimeProperty(auto_now=True)
  admin_tags = db.StringListProperty()
  avg_rating = db.IntegerProperty(default = 0)
  sum_ratings = db.IntegerProperty(default = 0)
  total_ratings = db.IntegerProperty(default = 0)
  moderation_status = db.IntegerProperty(default=UNREVIEWED)
  index = db.IntegerProperty()
  rated_index = db.StringProperty()
  comment_count = db.IntegerProperty(default = 0)
  SCHEMA_VERSION = db.IntegerProperty(default=DEFAULT_SCHEMA_VERSION)
  best_practice = db.BooleanProperty()

  def GetLink(self):
    """ Returns a relative URL to a page about this application. """
    return '/about_app?app_id=%s' % self.key().id()

  def Add(self):
    """ Handle adding a new entity to the datastore with a unique incrementing
    index. """

    def GetNextIndexValue(name):

      index = ApplicationIndex.get_by_key_name(name)
      if not index:
        index = ApplicationIndex(key_name = name)
      index.max_index += 1
      index.put()
      return index.max_index

    self.index = db.run_in_transaction(GetNextIndexValue, 'index1')
    self.rated_index = "%d:%d:%d" % (self.avg_rating, self.total_ratings, self.index)
    self.put()

  def Upgrade(self):
    """Handle upgrading the data model for this instance."""

    if self.SCHEMA_VERSION == 2:
      self.comment_count = len(list(self.comments))

    self.SCHEMA_VERSION = Application.DEFAULT_SCHEMA_VERSION
    self.put()

  def UpdateScreenshot(self, screenshot):
    """Updates the screenshot for the application. 

    Args:
      screenshot: A binary blob containing screenshot data.
    """

    if not screenshot:
      return

    query = ApplicationImage.all()
    query.filter('application =', self)
    query.filter('img_type =', 'screenshot')
    former = query.get()

    self.AddImage(screenshot, 300, 200, 'screenshot', former)
    self.screenshot = True

  def UpdateThumbnail(self, thumbnail):
    """Updates the thumbnail for the application.

    Args:
      thumbnail: A binary blob containing thumbnail data.
    """

    if not thumbnail:
      return

    query = ApplicationImage.all()
    query.filter('application =', self)
    query.filter('img_type =', 'thumbnail')
    former = query.get()

    self.AddImage(thumbnail, 120, 60, 'thumbnail', former)
    self.thumbnail = True

  def AddScreenshot(self, screenshot):
    """ Handle adding a screenshot of the application. 

    Args:
      screenshot: A binary blob containing screenshot data.
    """

    if not screenshot:
      return

    self.AddImage(screenshot, 300, 200, 'screenshot')
    self.screenshot = True

  def AddThumbnail(self, thumbnail):
    """ Handle adding a thumbnail of the application. 

    Args:
      thumbnail: A binary blob containing thumbnail data.
    """

    if not thumbnail:
      return

    self.AddImage(thumbnail, 120, 60, 'thumbnail')
    self.thumbnail = True

  def AddImage(self, image_data, width, height, img_type, instance = None):
    """ Handle adding an image of the application.

    Args:
      image_data: binary blob from an HTTP request.
      width: the image maximum width in pixels.
      height: the image maximum height in pixels.
      img_type: the type of the image (screenshot or thumbnail)
      instance: a previously stored image for this app, if one exists. """

    from google.appengine.api.images import Image

    imageContent = Image(image_data)
    imageContent.resize(width, height)

    if instance is None:
      image = ApplicationImage()
    else:
      image = instance
    image.application = self
    image.img_type = img_type
    image.content = imageContent.execute_transforms()
    image.put()

  def AddAuthor(self, user):
    query = db.Query(ApplicationAuthor)
    query.filter('user =', user)
    author = query.get()
    if author is None:
      author = ApplicationAuthor()
      author.user = user
      author.name = user.nickname().split('@')[0]
      author.put()
    self.author_ref = author

class CommentIndex(db.Model):

  DEFAULT_SCHEMA_VERSION = 1

  max_index = db.IntegerProperty(default = 0)
  SCHEMA_VERSION = db.IntegerProperty(default=DEFAULT_SCHEMA_VERSION)

class Comment(db.Model):
  """Comment

  Entities of this type will store the information
  for comment. A reference is made to the app the
  comment is being associated with.

  Properties:
    application: reference to the parent the application
    title: title of the comment
    body: body of the comment
    nickname: string ID of the user, entered by the user when adding a comment
    author: the Google Accounts user who made the comment
    rating: 0-5 rating given by the user
    created: date the comment was created
  """
  DEFAULT_SCHEMA_VERSION = 1

  application = db.Reference(Application, collection_name='comments')
  title = db.StringProperty()
  body = db.TextProperty()
  nickname = db.StringProperty(default = 'Anonymous')
  rating = db.IntegerProperty(default = 0)
  created = db.DateTimeProperty(auto_now_add=True)
  index = db.IntegerProperty()
  author = db.UserProperty()
  SCHEMA_VERSION = db.IntegerProperty(default=DEFAULT_SCHEMA_VERSION)

  def Add(self):
    """ Handle adding a new entity to the datastore with a unique incrementing
    index. """

    def GetNextIndexValue(application):

      index = CommentIndex.get_by_key_name('app:' + str(application.key().id()))
      if not index:
        index = CommentIndex(key_name = 'app:' + str(application.key().id()))
      index.max_index += 1
      index.put()
      return index.max_index
    
    self.index = db.run_in_transaction(GetNextIndexValue, self.application)
    self.put()
    
    def IncrementCommentCount(application):
      application.comment_count += 1
      application.put()
      
    db.run_in_transaction(IncrementCommentCount, self.application)
    
class ApplicationRating(db.Model):
  """Stores a rating for an application for a particular user.
  
  Properties:
    application: the application being rated
    rating: the user's 1-5 star rating
    user: the user who rated the app"""
  
  DEFAULT_SCHEMA_VERSION = 1
  
  application = db.Reference(Application, collection_name='ratings')
  rating = db.IntegerProperty(default = 0)
  user = db.UserProperty()
  SCHEMA_VERSION = db.IntegerProperty(default=DEFAULT_SCHEMA_VERSION)
  
    
class ApplicationImage(db.Model):
  """Stores a binary image blob for an application.

  Properties:
    application: reference to the parent application
    content: the image binary contents
    type: the type of the image "thumbnail" or "screenshot"
  """
  DEFAULT_SCHEMA_VERSION = 1

  application = db.Reference(Application, collection_name='images')
  content = db.BlobProperty()
  img_type = db.StringProperty()
  SCHEMA_VERSION = db.IntegerProperty(default=DEFAULT_SCHEMA_VERSION)
  
  
def GetApplicationById(id):
  """ Returns an Application instance corresponding to the provided id."""
  try:
    app = Application.get_by_id(int(id))
    return app
  except ValueError:
    return None

def GetApplicationAuthorById(id):
  """ Returns an Application instance corresponding to the provided id."""
  try:
    app = ApplicationAuthor.get_by_id(int(id))
    return app
  except ValueError:
    return None
