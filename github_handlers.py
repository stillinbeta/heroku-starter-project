import json
from pprint import pformat
import logging
import urllib.parse

from tornado.web import RequestHandler, HTTPError, URLSpec
import tornado.escape
from repo_crud import RepositoryMixin


class WebHookEndpoint(RequestHandler, RepositoryMixin):
    def post(self, repo_id, event):
        _ = self.get_or_400(repo_id)

        payload = self.get_body_argument('payload', default=None)
        unquoted = urllib.parse.unquote(payload)
        try:
            decoded = json.loads(tornado.escape.to_unicode(unquoted))
        except ValueError:
            raise HTTPError(
                400,
                "Invalid body received {}".format(self.request.body)
            )

        print(unquoted)

        self.set_status(204)
        self.finish()

handlers = [URLSpec(r'/hooks/(\d+)/(\w+)', WebHookEndpoint, name='hook')]
