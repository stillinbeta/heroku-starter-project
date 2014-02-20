import json
import logging
import re
import unittest
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
            if add_member:
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
    def _add_members_from_comments(self, repo, issue):
        body = issue['comment']['body']
        issue_number = issue['issue']['number']

        mentions = find_mentions(body)
        if not mentions:
            logging.info(
                "Comment '{}' has no mentions, ignoring.".format(body)
            )
            return

        db = self.application.db

        card = db.query(Issue)\
            .filter(Issue.issue_id == issue_number)\
            .filter(Issue.repo_id == repo.id).first()
        if card is None:
            logging.error("I don't have a card for {}/{} issue #{}".format(
                repo.owner,
                repo.repo,
                issue_number
            ))
            return

        users = self.application.db.query(User)\
            .filter(User.github_user.in_(mentions)).first()
        for user in users:
            # TODO make completely async
            yield self.trello.add_member_to_card(card.card_id,
                                                 user.trello_user)
            mentions.remove(user.github_user)

        if mentions:
            logging.warning(
                "Couldn't find trello user for github users {}".format(
                    ", ".join(mentions)
                )
            )

        logging.info("Added {} users to card {}".format(
            len(users),
            card.card_id
        ))

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
            if 'issue' not in decoded:
                # TODO: pull_request_review_comment events don't have issue
                logging.warning("Issue not found for comment event, ignoring")
            else:
                yield self._add_members_from_comments(repo, decoded)

        else:
            logging.warning("Hook receieved unknown event {}".format(event))


handlers = [URLSpec(r'/hooks/(\d+)/(\w+)', WebHookEndpoint, name='hook')]


def find_mentions(comment):
    """
    As best I can tell there are no restricions what charachters are valid
    in github usernames.
    See the test cases below for what this expression should match
    """
    return re.findall('(?:\s|^)@(\w+)', comment)


class FindMentionsTests(unittest.TestCase):
    def test_find_multiple(self):
        comment = "Hey @lizkf @stillinbeta could you take a look at this?"
        self.assertEqual(find_mentions(comment), ['lizkf', 'stillinbeta'])

    def test_find_start_of_word(self):
        comment = "@lizkf can you pick this up?"
        self.assertEqual(find_mentions(comment), ['lizkf'])

    def test_ignore_emails(self):
        comment = "Hey @lizkf email steve@infocorp.net"
        self.assertEqual(find_mentions(comment), ['lizkf'])

    def test_handle_unicode_usernames(self):
        comment = "Hey @zoë can you take a look at this"
        self.assertEqual(find_mentions(comment), ['zoë'])

    def test_no_matches(self):
        comment = "This is good, merged"
        self.assertEqual(find_mentions(comment), [])

if __name__ == "__main__":
    unittest.main()
