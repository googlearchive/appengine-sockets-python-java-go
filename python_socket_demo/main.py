#!/usr/bin/python

""" A demo app that shows use of the App Engine Socket API, via the nntplib
module. The nntp server object is created (and the socket connection opened) in
a client request instance, and summary info about the newsgroup obtained; then
the pickled nntp server object is passed in a task queue task payload to
a (potentially) different instance, where it is used further to fetch the
details of the first N posts.  The task queue task pings the client via the
Channel API when it has fetched the posts and stored them in the datastore, and
then the client retrieves the post data from the datastore.
This simple app does no caching or entity reuse, but could easily be extended to
do so.
"""

import cgi
import json
import logging
import nntplib
import uuid
import wsgiref

from base_handler import BaseHandler

from google.appengine.api import channel
from google.appengine.ext import ndb
from google.appengine.ext import webapp
from google.appengine.ext.deferred import defer


class PostData(ndb.Model):
  """Holds retrieved newsgroup post information, to send to the client.
  This simple app makes no reuse of these entities past their original
  request, nor does it purge the entities."""

  posts = ndb.PickleProperty()


def parseRootParams(request):
  """Parse the requst params."""
  params = {
      'newsgroup': 'sci.physics',
      'cid': ''
      }

  for k, v in params.iteritems():
    # Possibly replace default values.
    params[k] = request.get(k, v)
  return params


def fetch_posts(s, newsgroup, last, cid):
  """Fetch newsgroups posts, using the given nntp object s."""
  NUM_POSTS = 10  # we will fetch the last 10 posts (at most)
  try:
    start = str(int(last) - NUM_POSTS)
    _, items = s.xover(start, last)
    posts = []
    for (article_id, subject, author, _, _, _,
         _, _) in items:
      _, _, _, text = s.article(article_id)
      article = []
      for l in text:
        try:
          article.append(l.decode('utf-8', errors='ignore'))
        except UnicodeDecodeError:
          logging.exception('error on: %s', l)

      post_info = [article_id, author.decode('utf-8', errors='ignore'),
                   subject.decode('utf-8', errors='ignore'), len(text), article]
      posts.append(post_info)
    if posts:
      pd = PostData(posts=posts)
      pd.put()
      pid = pd.key.id()
      logging.debug('pid: %s, cid: %s', pid, cid)
      channel.send_message(cid, json.dumps(
          {'pid': pid, 'newsgroup': newsgroup}))
  except:
    logging.exception('Something went wrong...')


class IndexHandler(BaseHandler):
  """Render the index page and open the Channel API channel."""

  def get(self):
    cid = str(uuid.uuid4())
    token = channel.create_channel(cid)
    app_url = wsgiref.util.application_uri(self.request.environ)
    self.render_template('index.html', {'token': token, 'cid': cid,
                                        'app_url': app_url})


class GetPostsInfoHandler(BaseHandler):
  """This handler is called when the client is notified, via the channel api
  from a task queue tasks, that some post information is fetched and ready
  to display. (see index.html)."""

  def get(self):
    """Returns a json object containing the posts details in html format."""
    pid = cgi.escape(self.request.get('pid'))
    newsgroup = cgi.escape(self.request.get('newsgroup'))
    logging.info('got pid: %s', pid)
    try:
      # get the entity with the post information.
      pd = PostData.get_by_id(int(pid))
    except Exception, e:
      logging.exception("Something went wrong...")
      self.render_json({'status': 'ERROR', 'error': str(e)})
      return
    # use templating to generate an html string with the post details
    template_args = {'posts': pd.posts, 'newsgroup': newsgroup}
    pstring = self.jinja2.render_template('posts.html', **template_args)
    # return a json object with the results.
    self.render_json({'status': 'OK', 'pstring': pstring})


class FetchPostHandler(BaseHandler):
  """Get summary information about a newsgroup, and enqueue a task to fetch
  some posts from that newsgroup."""

  def get(self):
    self.getPosts(parseRootParams(self.request))

  def getPosts(self, params):
    """Get summary information about a newsgroup, and enqueue a task to fetch
  some posts from that newsgroup."""
    newsgroup = cgi.escape(params['newsgroup'])
    cid = params['cid']
    logging.info('got newsgroup: %s', newsgroup)
    if not newsgroup:
      self.response.out.write('Could not get newsgroup.')
      return

    try:
      NNTP_SERVER = 'news.mixmin.net'
      # get an nntp server object
      s = nntplib.NNTP(NNTP_SERVER)
      # get information about the given newsgroup
      resp, count, first, last, name = s.group(newsgroup)
      res_msg = ('resp, count, first, last, name: %s, %s, %s, %s, %s' % (
          resp, count, first, last, name))
      logging.info(res_msg)
      # enqueue a task to fetch some posts from that newsgroup.  Include the
      # nntp object as part of the task payload.
      defer(fetch_posts, s, newsgroup, last, cid)

    except Exception, e:
      logging.exception('something went wrong...')
      self.render_json({'status': 'ERROR', 'error': str(e)})
      return

    self.render_json({'status': 'OK', 'msg': res_msg})


application = webapp.WSGIApplication([
    ('/', IndexHandler),
    ('/get_posts', FetchPostHandler),
    ('/get_posts_info', GetPostsInfoHandler)
], debug=True)

