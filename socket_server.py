import asyncio
import websockets
import time
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from thread_utils import CancellableThrowingThread
import config
from api import TournamentApi
import socket

import logging

log = logging.getLogger(__name__)

HOST_NAME = 'localhost'
PORT_NUMBER = 9000

class ServiceException(Exception):
    pass

class RestServer(BaseHTTPRequestHandler):
    def do_HEAD(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    def do_GET(self):
        paths = {
            '/info': {'status': 200}
        }

        if self.path in paths:
            self.respond(paths[self.path], None)
        else:
            self.respond({'status': 404}, None)

    def do_POST(self):
        paths = {
            '/check_in': {'status': 200},
            '/check_out': {'status': 200}
        }

        data = None

        content_length = int(self.headers.get('content-length'))  # <--- Gets the size of data
        post_data = self.rfile.read(content_length)  # <--- Gets the data itself

        if post_data:
            try:
                data = json.loads(post_data)
            except:
                log.debug('Invalid json received')
                data = None

        if self.path in paths:
            self.respond(paths[self.path], data)
        else:
            self.respond({'status': 404}, data)

    def handle_http(self, status_code, path, data):
        resp = {'status': 'OK'}

        try:
            if path == '/info':
                resp['name'] = 'Padmiss daemon'
                resp['version'] = '1.0'
                resp['ip'] = socket.gethostbyname(socket.gethostname())
            elif path == '/players':
                players = {}
                i = 1
                for p in RestServer.pollers:
                    if p.mounted:
                        players[i] = p.mounted.__dict__
                    else:
                        players[i] = None
                    i += 1
                resp['players'] = players
            elif path == '/check_in':
                if data is None or (not 'side' in data) or (not 'player' in data):
                    raise ServiceException('Side or player not provided')

                side = int(data['side'])
                if len(RestServer.pollers) < side or RestServer.pollers[side - 1].mounted:
                    raise ServiceException('Side not available')

                poller = RestServer.pollers[side - 1]
                p = poller.api.get_player(playerId=data['player'])
                if p:
                    p.mountType = 'service'
                    poller.processUser(p, 'service')
                else:
                    raise ServiceException('Player not found for: ' + data['player'])

                resp['message'] = 'Checked in'

            elif path == '/check_out':
                if data is None or not 'side' in data or not 'player' in data:
                    raise ServiceException('Side or player not provided')

                side = int(data['side'])
                if len(RestServer.pollers) < side:
                    raise ServiceException('Side not available')

                poller = RestServer.pollers[side - 1]
                if poller.mounted:
                    poller.processUser(None, 'card')
                resp['message'] = 'Checked out'

            else:
                raise ServiceException('Unknown action')

        except ServiceException as e:
            status_code = 500
            resp['status'] = 'ERR'
            resp['message'] = str(e)

        content = json.dumps(resp)

        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(content))
        self.end_headers()

        return bytes(content, 'UTF-8')

    def respond(self, opts, data):
        response = self.handle_http(opts['status'], self.path, data)
        self.wfile.write(response)


class RestServerThread(CancellableThrowingThread):
    def __init__(self, pollers):
        super().__init__()
        self.setName('Rest server')
        self.pollers = pollers
        self.api = TournamentApi(config.PadmissConfigManager().load_config())

    def exc_run(self):
        RestServer.pollers = self.pollers
        httpd = HTTPServer((HOST_NAME, PORT_NUMBER), RestServer)
        lastPing = 0

        while not self.stop_event.wait(1):
            httpd.timeout = 2
            httpd.handle_request()

            if time.time() > (lastPing + 25):
                # self.api.broadcast()
                lastPing = time.time()

        httpd.server_close()
