#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
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
#




import wsgiref.handlers
import feedparser
import xmlrpclib

from google.appengine.api import urlfetch
from google.appengine.ext import webapp


class MainHandler(webapp.RequestHandler):

  def get(self):
    # Just subscribe to everything.
    self.response.out.write(self.request.get('hub.challenge'))
    self.response.set_status(200)

  def post(self):
    body = self.request.body.decode('utf-8')

    data = feedparser.parse(self.request.body)
    if data.bozo:
      if (hasattr(data.bozo_exception, 'getLineNumber') and
          hasattr(data.bozo_exception, 'getMessage')):
        line = data.bozo_exception.getLineNumber()
        segment = self.request.body.split('\n')[line-1]
      return self.response.set_status(500)

    update_list = []
    for entry in data.entries:
      entry_id = entry.id
      try:
        content = entry.summary
      except AttributeError:
        content = entry.content[0].value
        
      link = entry.get('link', '')
      title = entry.get('title', '')
      url = self.request.get('endpoint')
      published = entry.get('published')
      blog_id = self.request.get('blog_id')
      username = self.request.get('login')
      password = self.request.get('password')
      categories = tuple([self.request.get('category')])
      post = {'description': content, 'title': title, 'categories':  categories} 
      payload = xmlrpclib.dumps(tuple([blog_id, username, password, post, True]), "metaWeblog.newPost")
      
      rpc = urlfetch.create_rpc()
      urlfetch.make_fetch_call(rpc, url, payload, urlfetch.POST)
      try:
        result = rpc.get_result()
        status = result.status_code
        content = result.content
      except urlfetch.DownloadError:
        # Request timed out or failed.
        status = 500
        content = "DownloadError (but the post might have been posted... )"
        
    self.response.set_status(status)
    self.response.out.write(payload);


def main():
  application = webapp.WSGIApplication([('/', MainHandler)],
                                       debug=True)
  wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()
