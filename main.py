import logging
import os
import os.path

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import tornado.httpserver
import tornado.ioloop
from tornado.options import define
from tornado.web import Application, RequestHandler

from models import create_tables
import repo_crud

define("port", default=5000, help="run on the given port", type=int)


class MainHandler(RequestHandler):
    def get(self):
        self.redirect(self.application.reverse_url('repo_list'))


class MyApplication(Application):
    def __init__(self, db_url, **settings):
        if db_url is not None:
            engine = create_engine(db_url,
                                   echo=True,
                                   connect_args={'sslmode': 'require'})
            create_tables(engine)

            self.db = scoped_session(sessionmaker(bind=engine))

        handlers = [
            (r"/", MainHandler),
        ] + repo_crud.handlers

        settings['template_path'] = os.path.join(os.path.dirname(__file__),
                                                 "templates")
        settings['static_path'] = os.path.join(os.path.dirname(__file__),
                                               "static")
        super().__init__(handlers, **settings)


if __name__ == "__main__":
    tornado.options.parse_command_line()

    try:
        db_url = os.environ["DATABASE_URL"]
    except KeyError:
        logging.error("Improperly configured database!")
        #TODO FIXME
        # raise SystemExit(1)
        db_url = None

    app = MyApplication(db_url)

    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(os.environ.get("PORT", 5000))

    # start it up
    tornado.ioloop.IOLoop.instance().start()
