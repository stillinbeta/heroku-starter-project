import json
import logging
from pprint import pprint
import urllib.parse

import tornado.ioloop
from tornado.httpclient import AsyncHTTPClient
from tornado import gen
import tornado.escape

import secrets

LIST_BOARDS_URL = 'https://api.trello.com/1/members/my/boards/'
LIST_LISTS_URL = 'https://api.trello.com/1/boards/{board_id}/lists'
CREATE_CARD_URL = 'https://api.trello.com/1/cards'
ADD_MEMBER_TO_CARD_URL = 'https://api.trello.com/1/cards/{card_id}/idMembers'

try:
    api_key = secrets.TRELLO_API_KEY
    api_secret = secrets.TRELLO_API_SECRET
    token = secrets.TRELLO_TOKEN
except AttributeError:
    logging.error("Incomplete secrets.py!", exc_info=True)
    raise SystemExit(1)

class Trello:
    def __init__(self):
        self.client = AsyncHTTPClient()

    @gen.coroutine
    def make_request(self, url, params=None, body=None):
        if params is None:
            params = {}

        params.update({'key': api_key,
                       'token': token})
        encoded = urllib.parse.urlencode(params)

        # TODO error checking :-/
        if body is None:
            response = yield self.client.fetch(url + '?' + encoded)
        else:
            response = yield self.client.fetch(
                url + '?' + encoded,
                method='POST',
                body=body,
                headers={'content-type': 'application/json'}
            )

        decoded = json.loads(tornado.escape.to_unicode(response.body))

        return decoded

    @gen.coroutine
    def list_boards(self):
        boards = yield self.make_request(LIST_BOARDS_URL)
        return {board['name']: board['id'] for board in boards}

    @gen.coroutine
    def list_lists(self, board_id):
        lists = yield self.make_request(LIST_LISTS_URL.format(board_id=board_id))
        return {list_['name']: list_['id'] for list_ in lists}

    @gen.coroutine
    def add_card(self, name, list_, desc=None, due=None, members=None):
        body = {'name': name,
                'due': due,
                'idList': list_}
        if desc is not None:
            body['desc'] = desc
        if members is not None:
            body['idMembers'] = ','.join(members)

        encoded = json.dumps(body)

        response = yield self.make_request(CREATE_CARD_URL, body=encoded)
        return response.get('id', False)

    @gen.coroutine
    def add_member_to_card(self, card_id, member_id):
        body = {'value': member_id}
        encoded = json.dumps(body)

        response = yield self.make_request(
            ADD_MEMBER_TO_CARD_URL.format(card_id=card_id),
            body=encoded
        )

        return response

if __name__ == "__main__":
    @gen.coroutine
    def test_all():
        t = Trello()
        boards = yield t.list_boards()
        pprint(boards)
        a_board = list(boards.values())[0]
        lists = yield t.list_lists(a_board)
        pprint(lists)
        a_list = list(lists.values())[0]
        card = yield t.add_card("Just a test", a_list, 'doot doot doo')
        print(card)

    ioloop = tornado.ioloop.IOLoop.instance()
    ioloop.run_sync(test_all)
