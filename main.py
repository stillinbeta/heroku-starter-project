import logging
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import tornado.httpserver
import tornado.ioloop
import tornado.web

from models import create_tables

from tornado.options import define
define("port", default=5000, help="run on the given port", type=int)


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.set_header('content-type', 'text/plain')
        self.write("Hello, world")


class MyApplication(tornado.web.Application):
    def __init__(self, db_url, **settings):
        engine = create_engine(db_url, echo=True)
        create_tables(engine)

        self.db = scoped_session(sessionmaker(bind=engine))

        handlers = [
            (r"/", MainHandler),
        ]

        super().__init__(handlers, **settings)


if __name__ == "__main__":
    tornado.options.parse_command_line()

    try:
        db_url = os.environ["DATABASE_URL"]
    except KeyError:
        logging.error("Improperly configured database!")
        raise SystemExit(1)

    app = MyApplication(db_url)

    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(os.environ.get("PORT", 5000))

    # start it up
    tornado.ioloop.IOLoop.instance().start()
