import json
import logging
import urllib.parse

from tornado.web import RequestHandler, HTTPError, URLSpec
import tornado.escape
from tornado import gen

import trello
from repo_crud import RepositoryMixin
from models import User, Issue


class WebHookEndpoint(RequestHandler, RepositoryMixin):
    def initialize(self):
        self.trello = trello.Trello()

    @gen.coroutine
    def _add_pull_request(self, repo, pull_request, add_member=True):
        db = self.application.db

        # TODO error handling
        number = pull_request['number']
        github_user = pull_request['user']['login']
        title = pull_request['title']
        body = pull_request['body']

        if add_member:
            user = db.query(User)\
                .filter(User.github_user == github_user).first()
        else:
            user = None
        issue = db.query(Issue)\
            .filter(Issue.issue_id == number)\
            .filter(Issue.repo_id == repo.id)\
            .first()

        if issue is not None:
            logging.info(
                "Issue {}/{} #{} already created, ignoring".format(
                    repo.owner,
                    repo.repo,
                    number,
                )
            )
            return

        if user is None:
            members = None
            if add_member is not None:
                logging.warning(
                    "No Trello user found for github user {}".format(
                        github_user
                    )
                )
        else:
            members = [user.trello_user]

        card_id = yield self.trello.add_card(title,
                                             repo.new_list,
                                             desc=body,
                                             members=members)
        issue = Issue(repo_id=repo.id,
                      issue_id=number,
                      card_id=card_id)
        db.add(issue)
        db.commit()

        logging.info(
            "Issue {}/{} #{} created with card id {}".format(
                repo.owner,
                repo.repo,
                number,
                card_id,
            )
        )

    @gen.coroutine
    def post(self, repo_id, event):
        repo = self.get_or_400(repo_id)

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
                logging.info("Pull requested opened! Creating...")
                yield self._add_pull_request(repo, decoded['pull_request'])
            else:
                logging.info('Pull request closed!')
        elif event == 'issues':
            if decoded['issue']['state'] == 'open':
                logging.info('Issue opened! Creating...')
                yield self._add_pull_request(repo,
                                             decoded['issue'],
                                             False)
            else:
                logging.info('Issue closed!')
        elif (event == 'pull_request_review_comment' or
              event == 'issue_comment'):
            logging.info('Comment!')
        else:
            logging.warning("Hook receieved unknown event {}".format(event))


handlers = [URLSpec(r'/hooks/(\d+)/(\w+)', WebHookEndpoint, name='hook')]
