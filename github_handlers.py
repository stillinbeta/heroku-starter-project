import json
from pprint import pformat
import logging

from tornado.web import RequestHandler, HTTPError, URLSpec
import tornado.escape
from repo_crud import RepositoryMixin


class WebHookEndpoint(RequestHandler, RepositoryMixin):
    def post(self, repo_id, event):
        _ = self.get_or_400(repo_id)

        try:
            decoded = json.loads(tornado.escape.to_unicode(self.request.body))
        except ValueError:
            raise HTTPError(
                400,
                "Invalid body received {}".format(self.request.body)
            )

        logging.info(pformat(decoded))

        self.set_status(204)
        self.finish()

handlers = [URLSpec(r'/hooks/(\d+)/(\w+)', WebHookEndpoint, name='hook')]
