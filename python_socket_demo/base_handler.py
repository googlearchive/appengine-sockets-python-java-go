#!/usr/bin/env python
#
# Copyright 2012 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

""" The base request handler class.
"""


import webapp2
from webapp2_extras import jinja2
import json

from google.appengine.api import users


class BaseHandler(webapp2.RequestHandler):
  """The other handlers inherit from this class.  Provides some helper methods
  for rendering a template and generating template links."""


  @webapp2.cached_property
  def jinja2(self):
    return jinja2.get_jinja2(app=self.app)

  def render_template(self, filename, template_args):
    self.response.write(self.jinja2.render_template(filename, **template_args))

  def render_json(self, response):
    self.response.write("%s(%s);" % (self.request.GET['callback'],
                                     json.dumps(response)))


