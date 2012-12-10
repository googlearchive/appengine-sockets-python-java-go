#!/usr/bin/python

""" The base request handler class.
"""

import json

import webapp2
from webapp2_extras import jinja2


class BaseHandler(webapp2.RequestHandler):
  """The other handlers inherit from this class.  Provides some helper methods
  for rendering a template and generating template links."""

  @webapp2.cached_property
  def jinja2(self):
    return jinja2.get_jinja2(app=self.app)

  def render_template(self, filename, template_args):
    self.response.write(self.jinja2.render_template(filename, **template_args))

  def render_json(self, response):
    self.response.write('%s(%s);' % (self.request.GET['callback'],
                                     json.dumps(response)))


