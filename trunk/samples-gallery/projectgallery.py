import datetime
import math
import os
import logging
import wsgiref.handlers
import db_models

from google.appengine.ext import db
from google.appengine.api import datastore
from google.appengine.api import users
from google.appengine.ext.webapp import template
from google.appengine.ext import webapp
from google.appengine.api import mail
from google.appengine.api import memcache

# Set standard logging level to debug
logging.getLogger().setLevel(logging.WARNING)

#This enables logging only on the development server
if os.environ['SERVER_SOFTWARE'] == 'Development/1.0':
  DEBUG = True
else:
  DEBUG = False

GALLERY_TITLE = 'Samples Gallery'
GALLERY_APP_NAME = 'Sample'

class UTC(datetime.tzinfo):
  """A cheap hacky class that provides a tzinfo for datetime objects."""

  zero = datetime.timedelta(0)

  def utcoffset(self, dt):
    return self.zero

  def dst(self, dt):
    return self.zero

  def tzname(self, dt):
    return 'UTC'


class BaseHandler(webapp.RequestHandler):
  """Base handler for generating responses for most types of requests.

  Class provides helper functions for handling many of the common operations.
  """

  MODERATION_EMAIL = 'wave-samples-gallery-moderators@google.com'
  SENDER_EMAIL = 'wavesamplesgallery@gmail.com'

  def queryApp(self):
    """Small constructor for a query on db_models.Application."""
    query = db_models.Application.all()
    query.filter('moderation_status = ', db_models.Application.APPROVED)
    return query

  def loginUser(self):
    """Force the user to login on the current page."""
    self.redirect(users.create_login_url(self.request.uri))


  def sendAdminEmail(self, app, mail_type='new'):
    """Sends the admins an email about site activity.

    Args:
      app: The db_models.Application instance the e-mail is about.
      mail_type: What sort of notification this e-mail is."""
    values = {}

    if mail_type == 'new':
      template_name = 'new_email.html'
      subject = 'New sample to moderate: ' + app.title
      values['moderation_url'] = self.makeAbsoluteUrl('/moderate')
    else:
      template_name = 'edit_email.html'
      subject = 'Existing sample was edited: ' + app.title

    body = self.renderEmail(app, template_name, values)

    if 'prom.corp.google.com' in os.environ['SERVER_NAME']:
      sender_email = users.get_current_user().email()
    else:
      sender_email = self.SENDER_EMAIL

    receiver_email = self.MODERATION_EMAIL

    mail.send_mail(sender_email, receiver_email, subject, body)

  def sendUserRejectionEmail(self, app, reason=''):
    """Sends the user an e-mail indicating their application has been
    rejected.

    Args:
      app: The db_models.Application instance the e-mail is about.
      reason: The optional reason to include why the application was rejected.
    """
    template_name = 'reject_email.html'
    subject = 'Sample denied inclusion in gallery: ' + app.title

    body = self.renderEmail(app, template_name, { 'reason':reason })
    receiver_email = app.author_ref.user.email()
    sender_email = users.get_current_user().email()

    mail.send_mail(sender_email, receiver_email, subject, body, 
      bcc=self.MODERATION_EMAIL)

  def sendUserApprovalEmail(self, app, reason=''):
    """Sends the user an e-mail indicating their application has been
    approved.

    Args:
      app: The db_models.Application instance the e-mail is about.
    """
    template_name = 'approve_email.html'
    subject = 'Sample approved in gallery: ' + app.title

    body = self.renderEmail(app, template_name)
    receiver_email = app.author_ref.user.email()
    sender_email = users.get_current_user().email()

    mail.send_mail(sender_email, receiver_email, subject, body,
      bcc=self.MODERATION_EMAIL)
    
    
  def renderEmail(self, app, template_name, values={}):
    """Generates the given e-mail template into a message.
    
    Args:
      app: The db_models.Application instance the e-mail is about.
      template_name: The e-mail message template.
      values: Any custom parameters to pass in to the template.
    """
    
    values['app_url'] = self.makeAbsoluteUrl(app.GetLink())
    values['app'] = app
    
    directory = os.path.dirname(os.environ['PATH_TRANSLATED'])
    path = os.path.join(directory, 'templates', template_name)
    return template.render(path, values)
    
  def makeAbsoluteUrl(self, rel_url):
    server = os.environ['SERVER_NAME']
    port = os.environ['SERVER_PORT']
    if port != 80:
      server = server + ':' + port
    
    return 'http://' + server + rel_url

  def generate(self, template_name, template_values={}):
    """Generates the given template values into the given template.
          
    Args:
      template_name: the name of the template file (e.g., 'index.html')    
      template_values: a dictionary of values to expand into the template
    """
    # Populate the values common to all templates
    user = users.get_current_user()
    if user:
      url = users.create_logout_url(self.request.uri)
      url_linktext = 'Logout'
    else:
      url = users.create_login_url(self.request.uri)
      url_linktext = 'Sign In'
      user = ''

    values = {
      'user': user,
      'url': url,
      'url_linktext': url_linktext,
      'request': self.request,
      'debug': self.request.get('deb'),
      'apis': db_models.Application.APIS,
      'languages': db_models.Application.LANGUAGES,
      'title': GALLERY_TITLE,
      'app_name': GALLERY_APP_NAME,
    }
    values.update(template_values)

    directory = os.path.dirname(os.environ['PATH_TRANSLATED'])
    logging.debug("self.request.path = %s", self.request.path)
    path = os.path.join(directory, os.path.join('templates', template_name))
    self.response.out.write(template.render(path, values))

class MainPage(BaseHandler):
  """Handler for generating the response to requests for the main page."""

  def get(self):
    """Handler for HTTP GET requests.  

    Displays a featured app, editors picks, etc.
    """
    values = memcache.get('homepage')

    if not values:
      # get 5 recent apps
      query = self.queryApp()
      query.order('-created')
      recent = query.fetch(4)
      recent_next = recent[-1].index
      recent = recent[:-1]

      # get 1 featured application
      query = self.queryApp()
      query.filter('admin_tags =', 'featured')
      featured = query.fetch(1)

      # get 5 editor's picks
      query = self.queryApp()
      query.filter('best_practice = ', True)
      query.order('-created')
      editors = query.fetch(6)
      if len(editors) == 6:
        editors_next = editors[-1].index
        editors = editors[:-1]
      else:
        editors_next = 0

      values = {
        'recent_next': recent_next,
        'editors_next': editors_next,
        'featured': featured,
        'editors': editors,
        'recent': recent,
        'title': GALLERY_TITLE,
      }

      memcache.set('homepage', values, 300)

    self.generate('index.html', values)

class AboutAppHandler(BaseHandler):
  """Handler for generating the page displaying info about a specific app."""

  def get(self):
    """Handler for GET requests.  Displays app info for the specified app."""
    key = self.request.get('app_id')
    if not key:
      self.error(500)
      return
    error = self.request.get('err')
    is_admin = users.is_current_user_admin()
    app = db_models.GetApplicationById(key)
    if app: # If the app was found
      if is_admin or users.get_current_user() == app.author:
        can_edit = True
      else:
        can_edit = False
      if app.moderation_status != db_models.Application.APPROVED and not can_edit:
        if not users.get_current_user():
          self.loginUser()
          return
        else:
          self.redirect('/')
          return
      num_comments = app.comment_count

      # check if we're paging through comments
      start = self.request.get('start')
      prev = None
      next = None

      if start:
        try:
          start = int(start)
        except ValueError:
          start = None

      query = db_models.Comment.all()
      query.filter('application =', app)
      query.order('-index')

      if start:
        prev_query = db_models.Comment.all()
        prev_query.filter('application =', app)
        prev_query.order('index')
        prev_query.filter('index >', start)
        prev_results = prev_query.fetch(5)
        if prev_results:
          prev = prev_results[-1].index

        query.filter('index <=', start)

      # see if we have another page of results to look at
      comments = query.fetch(6)

      if len(comments) == 6:
        next = comments[-1].index
        comments = comments[:-1]

      values = {
        'title': GALLERY_APP_NAME + ' Details - ' + app.title,
        'app': app,
        'comments': comments,
        'num_comments': num_comments,
        'can_edit':can_edit,
        'is_admin':is_admin,
        'next':next,
        'prev':prev,
       }
      if error: # If the user was redirected here with an error.
        values['error'] = 'You do not have permission to edit this entry'
      self.generate('about_app.html', values)
    else:
      self.redirect('/')

class NewCommentActionHandler (BaseHandler):
  """Handler for creating a new comment associated with an app."""

  def post(self):
    """Handler for HTTP POST requests.  Processes a new comment and rating."""
    
    user = users.get_current_user()
    
    if user:
      app = db_models.GetApplicationById(self.request.get('app_id'))
      if not app:
        self.error('404')
        return
      title = self.request.get('title')
      body = self.request.get('body')
      nickname = self.request.get('nickname')
      rating = int(self.request.get('star_rating'))
      # Create a comment, update the avg_rating in a transaction.
      comment = db_models.Comment()
      comment.application = app
      comment.title = title
      comment.body = body
      comment.nickname = nickname
      comment.author = user
      comment.rating = rating
      comment.Add()

      if rating >= 1 and rating <=5:
        old_rating = db.run_in_transaction(self.RateApp, app, rating, user)
        db.run_in_transaction(self.UpdateAppAvg, app, rating, old_rating)  
      self.redirect(app.GetLink())
    else:
       self.loginUser()
  
  def RateApp(self, app, rating, user):
    """ Keeps track of the fact that a user is rating this application and
    returns the previous rating if one exists.
    
    Args:
      app: The application entity to be rated
      rating: the new rating given
      user: the user who is doing the rating.
    """
    
    old_rating = None
    keyname = "rating%s:%s" % (str(app.key().id()), user.email())
    user_rating = db_models.ApplicationRating.get_by_key_name(keyname)
    if not user_rating:
      user_rating = db_models.ApplicationRating(key_name = keyname)
    else:
      old_rating = user_rating.rating
    user_rating.user = user
    user_rating.rating = rating
    user_rating.application = app
    user_rating.put()
    
    return old_rating
  
  def UpdateAppAvg(self, app, rating, old_rating = None):
    """Updates the average rating for the application in the datastore.
      
       Args: 
         app: the Application entity to be updated
         rating: the new rating value
         old_rating: a previous rating given by the user, if one exists
    """
    
    if app.avg_rating > 0:
      if old_rating:
        app.sum_ratings += rating - old_rating
      else:
        app.sum_ratings += rating
        app.total_ratings += 1
      app.avg_rating = int(round((app.sum_ratings / app.total_ratings)))
      app.rated_index = "%d:%d:%d" % (
        app.avg_rating, app.total_ratings, app.index)
      app.put()
    else:
      app.total_ratings = 1
      app.avg_rating = rating
      app.sum_ratings = rating
      app.rated_index = "%d:%d:%d" % (
        app.avg_rating, app.total_ratings, app.index)
      app.put()

class NewAppHandler(BaseHandler):
  """Handler for displaying page for adding an app."""

  def get(self):
    """Handler for HTTP GET requests.  Displays a page for adding an app."""

    if not users.get_current_user():
       self.loginUser()
       return

    values = {
      'title': 'Submit',
      'apis': db_models.Application.APIS,
      'languages': db_models.Application.LANGUAGES,
    }

    self.generate('submit.html', values)

class NewAppActionHandler (BaseHandler):
  """Handler for creating an app."""

  def post(self):
    """Handler for HTTP POST requests.  Creates a new app in the datastore."""
    if users.get_current_user():
      # Get the args. First check to see that the image files are under 1MB 
      title = self.request.get('title')
      user = users.get_current_user()
      type = self.request.get('type')
      code_snippet = self.request.get('code_snippet').lstrip()
      description = self.request.get('content')
      tech_details = self.request.get('tech_details')
      thumbnail = self.request.get('thumbnail')
      screenshot = self.request.get('screenshot')
      url = self.request.get('url')
      source_url = self.request.get('source_url')
      if source_url and not source_url.startswith('http://'):
        source_url = "http://" + source_url
      robot_email = self.request.get('robot_email')
      gadget_xml = self.request.get('gadget_xml')
      installer_xml = self.request.get('installer_xml')
      video_url = self.request.get('video_url')
      apis_list = self.request.get_all('apis')
      languages_list = self.request.get_all('languages')
      tags_str = self.request.get('tags').replace(" ", "")
      tags = tags_str.split(',')

      app = db_models.Application()
      if self.request.get('best_practice') == 'on':
        app.best_practice = True
      app.type = type
      app.code_snippet = code_snippet
      app.title = title
      app.description = description
      app.tech_details = tech_details
      app.api_usage = self.request.get('api_usage')
      app.source_url = source_url
      app.tags = tags
      app.apis = apis_list
      app.languages = languages_list
      app.url = url
      app.robot_email = robot_email
      app.gadget_xml = gadget_xml
      app.installer_xml = installer_xml
      app.video_url = video_url
      if users.is_current_user_admin():
        app.moderation_status = db_models.Application.APPROVED

      if (len(self.request.get('thumbnail')) > 1000000 or
          len(self.request.get('screenshot')) > 1000000):
          template_values = {'title': 'Submit',
                         'app': app,
                         'apis': db_models.Application.APIS,
                         'languages': db_models.Application.LANGUAGES,
                         'error': 'Image files need to be under 1MB',
                         }
          for api in apis_list:
            template_values[str(api)] = True
          for language in languages_list:
            template_values[str(language)] = True
          self.generate('submit.html', template_values)
      else:
        app.Add()
        app.AddThumbnail(thumbnail)
        app.AddScreenshot(screenshot)
        app.AddAuthor(user)
        app.put()

        self.sendAdminEmail(app)
        self.redirect(app.GetLink())
    else:
      self.loginUser()

class EditProfileHandler(BaseHandler):
  def get(self):
    query = db.Query(db_models.ApplicationAuthor)
    query.filter('user = ', users.get_current_user())
    author = query.get()
    template_values = {
      'author': author
    }
    self.generate('edit_profile.html', template_values)

class ProfileHandler(BaseHandler):
  def get(self):
    id = self.request.get('id')
    author = db_models.GetApplicationAuthorById(id)
    template_values = {
      'author': author
    }
    if author:
      apps = author.application_set
      template_values['apps'] = apps

    self.generate('profile.html', template_values)


class EditProfileActionHandler(BaseHandler):
  def post(self):
    query = db.Query(db_models.ApplicationAuthor)
    query.filter('user = ', users.get_current_user())
    author = query.get()
    author.name = self.request.get('name')
    author.url = self.request.get('url')
    author.location = self.request.get('location')
    lat = self.request.get('latbox')
    lng = self.request.get('lonbox')
    if lat:
      author.latlng = db.GeoPt(float(lat), float(lng))
    author.put()
    self.redirect('/profile?id=' + str(author.key().id()))

class EditAppHandler(BaseHandler):
  """Handler for displaying an app for editing."""

  def get(self):
    """Handler for HTTP GET requests.  

    Loads an app from the datastore and displays information for 
    editing purposes.
    """
    user = users.get_current_user()
    app = db_models.GetApplicationById(self.request.get('app_id'))
    is_admin = users.is_current_user_admin()
    if not user:
      self.loginUser()
      return
    if app and (user == app.author or is_admin):

      template_values = {
        'title': 'Edit',
        'app': app,
        'is_admin': is_admin,
      }
      for api in app.apis:
        template_values[str(api)] = True
      for language in app.languages:
        template_values[str(language)] = True
      self.generate('edit.html', template_values)
    else:
       self.redirect(app.GetLink())

class EditAppActionHandler (BaseHandler):
  """Handler for editing an app."""

  def post(self):
    """Handler for HTTP POST requests.  

    Loads an app from the datastore and modifies supplied info.
    """
    user = users.get_current_user()
    is_admin = users.is_current_user_admin()
    app = db_models.GetApplicationById(self.request.get('app_id'))
    if app and (user == app.author or is_admin): 
      app.title=self.request.get('title')
      app.author_name = self.request.get('author_name')
      app.author_url = self.request.get('author_url')
      app.type = self.request.get('type')
      if self.request.get('author_googler') == 'on':
        app.author_googler = True
      if self.request.get('best_practice') == 'on':
        app.best_practice = True
      app.description = self.request.get('content')
      app.code_snippet = self.request.get('code_snippet').lstrip()
      app.tech_details = self.request.get('tech_details')
      app.api_usage = self.request.get('api_usage')
      app.url = self.request.get('url')
      #if app.url and not app.url.startswith('http://'):
      #  app.url = "http://" + app.url
      app.source_url = self.request.get('source_url')
      if app.source_url and not app.source_url.startswith('http://'):
        app.source_url = "http://" + app.source_url
      tags_str = self.request.get('tags').replace(" ", "")
      app.tags = tags_str.strip().split(',')
      app.robot_email = self.request.get('robot_email')
      app.gadget_xml = self.request.get('gadget_xml')
      app.installer_xml = self.request.get('installer_xml')
      app.video_url = self.request.get('video_url')
      app.apis = self.request.get_all('apis')
      app.languages = self.request.get_all('languages')

      if self.request.get('updatedthumbnail'):
        thumb = self.request.get('thumbnail')
        if len(thumb) <= 1000000:
          app.UpdateThumbnail(thumb)
      if self.request.get('updatedscreenshot'):
        ss = self.request.get('screenshot')
        if len(ss) <= 1000000:
          app.UpdateScreenshot(ss)
      if is_admin:
        admin_tags = self.request.get('admin_tags').replace(' ', '')
        app.admin_tags = admin_tags.split(',')
      app.put()
      if not is_admin:
        self.sendAdminEmail(app, 'edit')
      self.redirect(app.GetLink())
    else:
      self.redirect(app.GetLink() + '&err=1')

class SearchResultsHandler(BaseHandler):
  """Handler for searching apps."""
  
  def get(self):
    """Handler for GET requests to search applications in the datastore."""

    DEFAULT_NUM = 5

    cache_key = None
    cacheable = False

    # Grab the args from the request
    api = self.request.get('api')
    language = self.request.get('language')
    tag = self.request.get('q')
    topapps = self.request.get('topapps')
    google = self.request.get('google')
    try:
      author = users.User(self.request.get('author'))
    except users.UserNotFoundError:
      author = None

    values = None
    start = None
    prev = None

    # Grab the args from the request
    start = self.request.get('start')

    if not start:
      start = 0
    else:
      try:
        start = int(start)
      except ValueError:
        start = 0

    # custom page sizes are overrated and hard to cache.
    num = DEFAULT_NUM

    if topapps:
      cache_key = 'topapps'
    elif api:
      cache_key = 'api_' + api
    elif language:
      cache_key = 'language_' + language

    if start == 0 and num == DEFAULT_NUM and cache_key:
      cacheable = True
      values = memcache.get(cache_key)

    if not values:
      query = self.queryApp()
      prev_query = self.queryApp()
      query.order('-index')
      prev_query.order('index')

      if tag:
        query.filter('tags = ', tag)
        prev_query.filter('tags = ', tag)
        q_type = "q"
        q = tag
        label = 'Tag: %s' % tag
      elif topapps:
        query.filter('best_practice = ', True)
        q_type = "topapps"
        q="true"
        label = "Best Practices"
      elif language:
        query.filter('languages =', language)
        prev_query.filter('languages =', language)
        q_type = "language"
        q = language
        label = 'Language: %s' % language
      elif api:
        query.filter('apis =', api)
        prev_query.filter('apis =', api)
        q_type = "api"
        q = api
        label = 'API: %s' % api
      elif author:
        query.filter('author =', author)
        prev_query.filter('author =', author)
        q_type = "author"
        q = author.email()
        label = 'Author: %s' % author.email()
      elif google:
        query.filter('author_googler =', True)
        prev_query.filter('author_googler =', True)
        q_type = "google"
        q = "google"
        label = "By Google"

      else: #default to most recent apps. 
        self.redirect('/recent')
        return

      count = query.count(300)
      if start > 0:
        prev_query.filter('index >', start)
        prev_results = prev_query.fetch(num)
        if prev_results:
          prev = prev_results[-1].index
        query.filter('index <=', start)

      results = query.fetch(num + 1)
      if len(results) == num + 1:
        next = results[-1].index
        apps = results[:-1]
      else:
        next = None
        apps = results

      values = {'apps' : apps,
            'total' : len(apps),
            'prev' : prev,
            'next' : next,
            'q_type' : q_type,
            'num' : num,
            'q' : q,
            'count': count,
            'label' : label }

      if cacheable:
          memcache.set(cache_key, values, 600)

    self.generate('results.html', values)


class RecentAppsHandler(BaseHandler):
  """Handler for paging through recent apps."""

  def get(self):
    """Handler for GET requests to search applications in the datastore."""

    num = 5
    cache_key = 'recentapps'
    cacheable = False
    values = None
    prev = None

    # Grab the args from the request
    start = self.request.get('start')

    if not start:
      start = 0
    else:
      try:
        start = int(start)
      except ValueError:
        start = 0

    if start == 0:
      cacheable = True

      values = memcache.get(cache_key)

    if not values:
      query = self.queryApp()
      query.order('-index')
      count = query.count()
      if start > 0:
        prev_query = self.queryApp()
        prev_query.order('index')
        prev_query.filter('index >', start)
        prev_results = prev_query.fetch(num)
        if prev_results:
          prev = prev_results[-1].index
        query.filter('index <=', start)

      results = query.fetch(num + 1)
      if len(results) == num + 1:
        next = results[-1].index
        apps = results[:-1]
      else:
        next = None
        apps = results

      values = {'apps' : apps,
                'total' : len(apps),
                'start' : start,
                'next' : next,
                'count': count,
                'prev' : prev,
                'num' : 5,
                'q_type' : 'recentapps',
                'q' : "true",
                'label' : "Recent " + GALLERY_APP_NAME + 's',
                'title' : 'Recent ' + GALLERY_APP_NAME + 's', 
                }

      if cacheable:
        memcache.set(cache_key, values, 60)

    self.generate('results.html', values)


class ImageHandler (BaseHandler):
  """Handler to retrieve an image blob from the datastore."""

  def get(self):
    """Generates the image from a blog in the datastore.

    request.get('img_type') is used to determine whether we are displaying a 
    screenshot (300x200) or a thumbnail (120x60).  These are stored in 
    different entity properties so we pull
    the right one based on a cgi parameter passed in.
    """
    key = self.request.get('img_id')
    if not key:
      self.error(400)
      return
    app = db_models.GetApplicationById(key)
    
    if app is None:
      self.error(400)
      return
    img_type = self.request.get('img_type')
    
    if img_type != 'screenshot' and img_type != 'thumbnail':
      self.error(400)
      self.response.out.write('Bad img_type')
      return
    query = db_models.ApplicationImage.all()
    query.filter('application =', app)
    query.filter('img_type =', img_type)
    image = query.get()
    
    if image is None:
      self.error(404)
      self.response.out.write('Image not found')
      return
    
    self.response.headers['Content-Type'] = 'image/png'
    self.response.out.write(image.content)


class DeleteAppActionHandler (BaseHandler):
  """Handler to delete the specified app from the datastore."""
  
  def post(self):
    """Handler for HTTP POST requests to delete an app from the datastore."""
    user = users.get_current_user()
    key = self.request.get('app_id')
    if key is None:
      self.redirect('/')
      return
    app = db_models.GetApplicationById(key)
    if app and (user == app.author or users.is_current_user_admin()):
      for comment in app.comments:
        comment.delete()
      for image in app.images:
        image.delete()
      app.delete()

    self.redirect('/')


class FeedHandler (BaseHandler):
  """Handler to generate Atom feeds. 
  """
  
  def GetCurrentRfc822Time(self):
    """ Returns the current time in RFC822 format"""
    import time
    
    now = time.gmtime()
    #YYYY-MM-DDTHH:MM:SSZ
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', now)
  
 
  def GetEntry(self, app):
    """Produces an atom.Entry object representing the specified app.

    Args:
      app: the Application object to transform into an entry

    Returns:
      The specified Application object as an atom.Entry
    """

    entry = {}
    entry['app_url'] = 'http://%s%s' % (
      self.request.host, app.GetLink())
    if app.thumbnail:
      entry['icon_url'] = 'http://%s/images?img_id=%s&img_type=thumbnail' % (
        self.request.host, str(app.key().id()))
    else:
      entry['icon_url'] = 'http://%s/static/img/project_gallery_logo.png' % (
        self.request.host)
    entry['ss_url'] = 'http://%s/images?img_type=screenshot&img_id=%s' % (
      self.request.host,str(app.key().id()))
    
    entry['title'] = app.title
    entry['description'] = app.description
    entry['author'] = {}
    entry['author']['name'] = app.author_ref.name
    entry['id'] = 'http://%s/feeds/apps/appid/%s' % (
      self.request.host, str(app.key().id()))
    
    app.created = app.created.replace(tzinfo = UTC())
    
    if app.updated is not None:
      app.updated = app.updated.replace(tzinfo = UTC())
      entry['updated'] = app.updated.strftime('%Y-%m-%dT%H:%M:%SZ')
    else:
      entry['updated'] = app.created.strftime('%Y-%m-%dT%H:%M:%SZ')
    
    entry['published'] = app.created.strftime('%Y-%m-%dT%H:%M:%SZ')
    
    return entry


  def RenderFeed(self, title, id, entries):
    """Renders the Atom feed of the given applications"""
    
    feed = {}
    feed['entries'] = []
    feed['title'] = title
    feed['id'] = id
    feed['updated'] = self.GetCurrentRfc822Time()
    
    for app in entries:
      feed['entries'].append(self.GetEntry(app))

    directory = os.path.dirname(os.environ['PATH_TRANSLATED'])
    path = os.path.join(directory, os.path.join('templates', 'atom_feed.xml'))
    return template.render(path, {'feed': feed})
    

class FeaturedFeedHandler(FeedHandler):
  """Handler to generated the Featured App Feed."""
  
  def get(self):
    """Constructs and renders the requested feed to the client."""
    
    
    feed = memcache.get('featured_feed')
    
    if not feed:  
      query = self.queryApp()
      query.filter('admin_tags =', 'featured')
      featured = query.fetch(1)
    
      feed_id = 'http://%s/feeds/apps/featured' % self.request.host
      
      feed = self.RenderFeed("Featured Application", feed_id, featured)
      
      memcache.set('featured_feed', feed, 600)
      
    self.response.headers['Content-Type'] = 'application/atom+xml'
    self.response.out.write(feed)


class EditorsPicksFeedHandler(FeedHandler):
  """Handler to generated the Editor's Picks Feed."""

  def get(self):
    """Constructs and renders the requested feed to the client."""
    
    feed = memcache.get('editors_picks_feed')
    
    if not feed:
      query = self.queryApp()
      query.filter('admin_tags =', 'editor')
      #query.order('-avg_rating').order('-total_ratings')
      editor_picks = query.fetch(5)

      feed_id = 'http://%s/feeds/apps/editor_picks' % self.request.host
      feed = self.RenderFeed("Best Practices", feed_id, editor_picks)
      memcache.set('editors_picks_feed', feed, 600)
      
    self.response.headers['Content-Type'] = 'application/atom+xml'
    self.response.out.write(feed)

  
class RecentFeedHandler(FeedHandler):
  """Handler to generated the Recent Apps Feed."""
  
  def get(self):
    """Constructs and renders the requested feed to the client."""
    
    feed = memcache.get('recent_feed')
    
    if not feed:
      query = self.queryApp()
      query.order('-created')
      apps = query.fetch(25)

      feed_id = 'http://%s/feeds/apps/all' % self.request.host
      feed = self.RenderFeed("Recent Apps", feed_id, apps)
      memcache.set('recent_feed', feed, 60)

    self.response.headers['Content-Type'] = 'application/atom+xml'
    self.response.out.write(feed)

class SitemapHandler(BaseHandler):
  def get(self):
    sitemap = memcache.get('sitemap')
    if sitemap is None:
      query = self.queryApp()
      apps = query.fetch(1000)
      template_values = {"apps": apps}
      directory = os.path.dirname(os.environ['PATH_TRANSLATED'])
      path = os.path.join(directory, os.path.join('templates', 'sitemap.xml'))
      sitemap = template.render(path, template_values)
      memcache.set('sitemap', sitemap, 300)
    self.response.out.write(sitemap)

class GetUrlsHandler(BaseHandler):
  def get(self):
    query = self.queryApp()
    apps = query.fetch(1000)
    emails = {}
    print "<html><body>"
    for app in apps:
      url = app.source_url
      if url.find("code.google.com/p") > -1:
        urlSplit = url.partition("/p/")
        url = "http://" + urlSplit[2].partition("/")[0] + ".googlecode.com/svn/trunk/"
      print url + "<br>"
    print "</body></html>"

class GetEmailsHandler(BaseHandler):
  def get(self):
    query = self.queryApp()
    apps = query.fetch(1000)
    emails = {}
    for app in apps:
      emails[app.author_ref.user.email()] = 1
    for email in emails:
      print email + ","

class ModerationHandler (BaseHandler):
  """Handler for moderation queue actions."""

  def get(self):
    if not users.is_current_user_admin():
      self.redirect('/')
      return

    values = {}
    q = db_models.Application.all()
    values['moderation_list'] = q.filter(
      'moderation_status = ', db_models.Application.UNREVIEWED)

    self.generate('moderate.html', values)


  def post(self):
    if users.is_current_user_admin():
      app = db_models.GetApplicationById(self.request.get('app_id'))
      action = self.request.get('moderate_action')
      if app and action:
        if action == "approve":
          app.moderation_status = db_models.Application.APPROVED
          self.sendUserApprovalEmail(app)
        elif action == "reject":
          app.moderation_status = db_models.Application.REJECTED
          self.sendUserRejectionEmail(app, self.request.get('reason'))
        app.put()

    self.redirect('/moderate')

  
class UpgradeDatabaseHandler (BaseHandler):
  """Handler for database migrations."""

  def get(self):
    if not users.is_current_user_admin():
      self.redirect('/')
      return

    values = {}
    q = db_models.Application.all()
    q.filter('SCHEMA_VERSION = ', 2)
    models = q.fetch(limit=2)
    models[0].Upgrade()
    if len(models) == 2:
      values['continue'] = True

    self.generate('upgrade_db.html', values)

class UpgradeAuthorsHandler(BaseHandler):
  def get(self):
    self.response.out.write("Upgrading authors <br>")
    app = db_models.GetApplicationById(self.request.get('id'))
    if app is None:
      query = self.queryApp()
      apps = query.fetch(170)
      for app in apps:
        app.author_ref.name = app.author_name
        app.author_ref.url = app.author_url
        app.author_ref.put()
        if app.author_ref is None:
          self.response.out.write("upgrading " + app.title + "<br>")
          self.response.out.write(app.AddAuthor(app.author))
          app.put()
    elif app.author_ref is None:
      self.response.out.write("upgrading " + app.title + "<br>")
      self.response.out.write(app.AddAuthor(app.author))
      app.put()

class ReportHandler(BaseHandler):
  def get(self):
    query = self.queryApp()
    appCount = query.count()
    self.response.out.write("Total Samples: " + str(appCount) + '<br>')

    self.response.out.write('<img src="' + self.getChartForArray(db_models.Application.APIS, 'apis') + '"><br>')
    self.response.out.write('<img src="' + self.getChartForArray(db_models.Application.LANGUAGES, 'languages') + '"><br>')

  def getChartForArray(self, array, prop):
    counts = []
    baseUrl = "http://chart.apis.google.com/chart?chxt=x,y&chxl=0:|" + "|".join(array) + "|&cht=bvs&chco=76A4FB&chls=2.0&chs=300x250&chbh=r,0.3&chd=t:"
    for item in array:
      query = self.queryApp()
      query.filter(prop + ' =', item)
      counts.append(str(query.count()))
    return baseUrl + ','.join(counts)

class AuthorsMapHandler(BaseHandler):
  def get(self):
    query = db.Query(db_models.ApplicationAuthor)
    query.filter('location !=', None)
    authors = query.fetch(500)
    template_values = {
      'authors': authors
    }
    self.generate('authorsmap.html', template_values)

application = webapp.WSGIApplication ( 
  [('/submit', NewAppHandler),
   ('/submit.do', NewAppActionHandler),
   ('/postcomment.do', NewCommentActionHandler),
   ('/images', ImageHandler),
   ('/delete.do', DeleteAppActionHandler),
   ('/edit', EditAppHandler),
   ('/edit.do', EditAppActionHandler),
   ('/edit_profile', EditProfileHandler),
   ('/edit_profile.do', EditProfileActionHandler),
   ('/about_app', AboutAppHandler),
   ('/profile', ProfileHandler),
   ('/results', SearchResultsHandler),
   ('/recent', RecentAppsHandler),
   ('/authors_map', AuthorsMapHandler),
   ('/feeds/apps/featured', FeaturedFeedHandler),
   ('/feeds/apps/editor_picks', EditorsPicksFeedHandler),
   ('/feeds/apps/all', RecentFeedHandler),
   ('/moderate', ModerationHandler),
   ('/getemails', GetEmailsHandler),
   ('/geturls', GetUrlsHandler),
   ('/upgradedb', UpgradeDatabaseHandler),
   ('/upgradeauthors', UpgradeAuthorsHandler),
   ('/sitemap.xml', SitemapHandler),
   ('/report', ReportHandler),
   ('/',MainPage)], debug=DEBUG)


def main():
  """Main method to handle all requests"""
  wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()
