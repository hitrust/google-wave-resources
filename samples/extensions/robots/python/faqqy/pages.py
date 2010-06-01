import cgi
import os
import models
import re

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.api import memcache 
from google.appengine.ext.webapp import template

class MainPage(webapp.RequestHandler):
  def get(self):
    mainpage = memcache.get('mainpage')
    if mainpage is None:
      query = db.Query(models.FAQ)
      query.filter('type = ', 'toc')
      query.order('order')
      tocs = query.fetch(20)
      data = []
      for toc in tocs:
        faqs = [db.get(key) for key in toc.faqs]
        faqsEscaped = []
        for faq in faqs:
          if faq is None:
            continue
          faq.body = cgi.escape(faq.body)
          def dashrepl(matchobj):
            if matchobj.group(0): return len(matchobj.group(0)) * '&nbsp;'
            else: return ''
          faq.body = re.sub('(?<=\n)\s+(?=\w)', dashrepl, faq.body)
          faqsEscaped.append(faq)
        data.append({"shortId": toc.shortId, "title": toc.title, "faqs": faqsEscaped})
      template_values = {'title': 'Google Wave API FAQ', 'data': data}
      path = os.path.join(os.path.dirname(__file__), 'templates/faq.html')
      mainpage = template.render(path, template_values)
      memcache.set('mainpage', mainpage, 10)
    self.response.out.write(mainpage)

application = webapp.WSGIApplication(
                                     [('/', MainPage)],
                                     debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
