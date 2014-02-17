import os

import tornado.httpserver
import tornado.ioloop
import tornado.web

from tornado.options import define, options
define("port", default=5000, help="run on the given port", type=int)

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.set_header('content-type', 'text/plain')
        self.write("Hello, world")

application = tornado.web.Application([
    (r"/", MainHandler),
])

if __name__ == "__main__":
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(os.environ.get("PORT", 5000))

# start it up
    tornado.ioloop.IOLoop.instance().start()

