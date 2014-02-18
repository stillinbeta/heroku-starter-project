import logging
import os
import os.path

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import tornado.httpserver
import tornado.ioloop
from tornado.web import Application, RequestHandler, URLSpec, HTTPError


from models import create_tables, Repository

from tornado.options import define
define("port", default=5000, help="run on the given port", type=int)


class MainHandler(RequestHandler):
    def get(self):
        self.redirect(self.application.reverse_url('repo_list'))


class RepositoryMixin:
    def update_db(self, repository=None):
        db = self.application.db

        owner = self.get_body_argument('repo_owner', default=None)
        repo = self.get_body_argument('repo_name', default=None)
        board = self.get_body_argument('board_id', default=None)
        new_list = self.get_body_argument('list_id', default=None)

        if repository is None:
            repository = Repository(owner=owner,
                                    repo=repo,
                                    board=board,
                                    new_list=new_list)
        else:
            repository.owner = owner
            repository.repo = repo
            repository.board = board
            repository.new_list = new_list

        db.add(repository)
        db.commit()  # TODO error checking

        self.redirect(self.application.reverse_url('repo_edit', repository.id))

    def get_or_400(self, id_):
        repo = self.application.db.query(Repository).get(id_)
        if repo is None:
            raise HTTPError(404, "Couldn't find repo w/ id {}".format(id_))

        return repo


class RepoAdd(RequestHandler, RepositoryMixin):
    def get(self):
        self.render(
            "add_repo.html",
            verb="Add",
            repo_owner='',
            repo_name='',
            board_id='',
            list_id='',
        )

    def post(self):
        return self.update_db()


class RepoEdit(RequestHandler, RepositoryMixin):
    def get(self, id_):
        repo = self.get_or_400(id_)
        self.render(
            "add_repo.html",
            verb="Edit",
            repo_owner=repo.owner,
            repo_name=repo.repo,
            board_id=repo.board,
            list_id=repo.new_list,
        )

    def post(self, id_):
        repo = self.get_or_400(id_)
        self.update_db(repo)


class RepoList(RequestHandler):
    def get(self):
        links = []
        for repo in self.application.db.query(Repository):
            links.append(('{}/{}'.format(repo.owner, repo.repo),
                         self.application.reverse_url('repo_edit', repo.id)))

        self.render('repo_list.html',
                    create=self.application.reverse_url('repo_add'),
                    links=links)


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
            URLSpec(r"/repos", RepoList, name='repo_list'),
            URLSpec(r"/repos/add", RepoAdd, name='repo_add'),
            URLSpec(r"/repos/(\d+)", RepoEdit, name='repo_edit'),
        ]

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
