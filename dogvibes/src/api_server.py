import tornado.ioloop
import tornado.web

import errno
import functools
import socket
from tornado import ioloop, iostream, httpserver, websocket

import re

dogs = []

EOS = r'[[EOS]]'
SEP = r'[[SEP]]'

class Dog():
    def __init__(self, stream):
        self.stream = stream
        self.active_handlers = []

    def set_username(self, username):
        username = username[:-len(EOS)]
        dog = Dog.find(username)
        if dog != None:
            dog.stream.close()
            dogs.remove(dog)
            print "Bye, %s!" % dog.username
        dogs.append(self)

        print "Welcome, %s!" % username
        self.username = username

    def command_callback(self, data):
        data = data[:-len(EOS)]
        nbr, raw, result = data.split(SEP)

        # clean up dangling requests to they are garbage collected
        self.active_handlers = [ h for h in self.active_handlers if h.active() ]

        for handler in self.active_handlers:
            if handler.nbr == nbr: # TODO: and command for HTTP
                handler.send_result(raw, result)

        if not self.stream.reading():
            self.stream.read_until(EOS, self.command_callback)

    def send_command(self, command, handler):
        try:
            self.stream.write(handler.nbr + SEP + command + EOS)
        except:
            print "Bye, %s!" % self.username
            self.stream.close()
            dogs.remove(self)
            return

        if not self.stream.reading():
            self.stream.read_until(EOS, self.command_callback)

    @classmethod
    def find(self, username):
        for dog in dogs:
            if dog.username == username:
                return dog
        return None

def process_command(handler, username, command):
    dog = Dog.find(username)
    if dog == None:
        return "ERROR!" # FIXME
    dog.send_command(command, handler)

def connection_ready(sock, fd, events):
    while True:
        try:
            connection, address = sock.accept()
        except socket.error, e:
            if e[0] not in (errno.EWOULDBLOCK, errno.EAGAIN):
                raise
            return
        connection.setblocking(0)
        stream = iostream.IOStream(connection)

        dog = Dog(stream)
        # The first thing a Dog will send is its username. Catch it!
        stream.read_until(EOS, dog.set_username)

nbr = 0
def assign_nbr():
    global nbr
    nbr = nbr + 1
    return str(nbr)

class HTTPHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self, username):
        dog = Dog.find(username)
        if dog == None:
            print "Someone tried to access %s, but it's not connected" % username
            return
        self.dog = dog
        # a HTTP connection can be reused so don't add it more than once
        if self not in dog.active_handlers:
            dog.active_handlers.append(self)
            self.nbr = assign_nbr()

        command = self.request.uri[len(username)+1:]
        process_command(self, username, command)

    def send_result(self, raw, data):
        self.set_header("Content-Length", len(data))
        if raw == '1':
            self.set_header("Content-Type", "image/png")
        else:
            self.set_header("Content-Type", "text/javascript")

        try:
            self.write(data)
            self.finish()
        except IOError:
            print "Could not write to HTTP client %s" % self.nbr
            # handler will be removed later when called active()
            return

    def active(self):
        return not self._finished

class WSHandler(websocket.WebSocketHandler):
    def open(self, username):
        self.username = username
        self.nbr = assign_nbr()
        dog = Dog.find(username)
        if dog == None:
            print "Someone tried to access %s, but it's not connected" % username
            return
        dog.active_handlers.append(self)
        self.receive_message(self.on_message)

    def on_message(self, command):
        process_command(self, self.username, command)
        self.receive_message(self.on_message)

    def send_result(self, raw, data):
        try:
            self.write_message(data)
        except IOError:  # TODO: will this happen?
            print "Could not write to WS client %s" % self.nbr
            # TODO unregister, will break when using push
            return

    def active(self):
        return True

def setup_dog_socket(io_loop):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setblocking(0)
    sock.bind(("", 11111))
    sock.listen(5000)

    callback = functools.partial(connection_ready, sock)
    io_loop.add_handler(sock.fileno(), callback, io_loop.READ)

if __name__ == '__main__':
    application = tornado.web.Application([
            (r"/stream/([a-zA-Z0-9]+).*", WSHandler),
            (r"/([a-zA-Z0-9]+).*", HTTPHandler), # TODO: split only on '/', avoids favicon
            ])

    http_server = httpserver.HTTPServer(application)
    http_server.listen(2000)

    io_loop = ioloop.IOLoop.instance()
    setup_dog_socket(io_loop)

    print "Dogvibes API server started"

    try:
        io_loop.start()
    except KeyboardInterrupt:
        io_loop.stop()
