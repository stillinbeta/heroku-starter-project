import json
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

        self.set_status(204)
        self.finish()

        if event == 'pull_request':
            if decoded['pull_request']['state'] == 'open':
                logging.info('Pull Request opened!')
            else:
                logging.info('Pull request closed!')
        elif event == 'issues':
            if decoded['issue']['state'] == 'open':
                logging.info('Issue opened')
            else:
                logging.info('Issue closed!')
        elif (event == 'pull_request_review_comment' or
              event == 'issue_comment'):
            logging.info('Comment!')
        else:
            logging.warning("Hook receieved unknown event {}".format(event))


handlers = [URLSpec(r'/hooks/(\d+)/(\w+)', WebHookEndpoint, name='hook')]
