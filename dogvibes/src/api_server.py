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
        self.active_requests = []

    def set_username(self, username):
        username = username[:-len(EOS)]
        dog = Dog.find(username)
        if dog != None:
            dog.stream.close()
            dogs.remove(dog)
            print "Bye, %s!" % self.username
        dogs.append(self)

        print "Welcome, %s!" % username
        self.username = username

    def command_callback(self, data):
        data = data[:-len(EOS)]
        command, result = data.split(SEP)
        found = None

        for req in self.active_requests:
            if req.request.uri[-len(command):] == command:
                self.active_requests.remove(req)
                found = req
                break

        req = found

        # TODO: add more headers?
        if 'AlbumArt' in command:
            req.set_header("Content-Type", "image/jpeg")
        else:
            req.set_header("Content-Type", "text/javascript")

        req.set_header("Content-Length", len(result))

        try:
            req.write(result)
            req.finish()
        except IOError:
            return # TODO: what to do here?

        if self.active_requests != []:
            self.stream.read_until(EOS, self.command_callback)

    def send_command(self, command, request):
        try:
            print "writing " + command
            self.stream.write(command + EOS)
        except:
            print "Bye, %s!" % self.username
            self.stream.close()
            dogs.remove(self)
            return

        if self.active_requests == []:
            self.active_requests.append(request)
            self.stream.read_until(EOS, self.command_callback)
        else:
            self.active_requests.append(request)

    @classmethod
    def find(self, username):
        for dog in dogs:
            if dog.username == username:
                return dog
        return None

def process_command(handler, username):
    command = handler.request.uri[len(username)+1:]
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
        stream.read_until(EOS, dog.set_username)

class HTTPHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self, username):
        process_command(self, username)

class WSHandler(websocket.WebSocketHandler):
    def open(self, username):
        self.receive_message(self.on_message)

    def on_message(self, command):
        process_command(self.username)
        self.receive_message(self.on_message)

    def send_result(self, data):
        self.send_message(data)

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
            (r"/([a-zA-Z0-9]+)/stream", WSHandler),
            (r"/([a-zA-Z0-9]+).*", HTTPHandler), # TODO: split only on '/', avoids favicon
            ])

    http_server = httpserver.HTTPServer(application)
    http_server.listen(2000)

    io_loop = ioloop.IOLoop.instance()
    setup_dog_socket(io_loop)

    try:
        io_loop.start()
    except KeyboardInterrupt:
        io_loop.stop()
