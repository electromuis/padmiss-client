import websockets
import time, json, socket, logging
from mako.template import Template
from http.server import BaseHTTPRequestHandler, HTTPServer, SimpleHTTPRequestHandler
from .thread_utils import CancellableThrowingThread
from .api import TournamentApi
from .fsr import fsrio
from .util import resource_path
from urllib.parse import urlparse, parse_qs
import os

log = logging.getLogger(__name__)
web_path = resource_path('web')
config = None

class ServiceException(Exception):
    pass

class RestServer(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        """This handler uses server.base_path instead of always using os.getcwd()"""

    def get_poller_driver(self, side):
        if len(RestServer.pollers) < side or RestServer.pollers[side - 1].mounted:
            raise ServiceException('Side not available')

        poller = RestServer.pollers[side - 1]
        return poller.getDriver('web')

    def translate_path(self, path):
        path = SimpleHTTPRequestHandler.translate_path(self, path)
        relpath = os.path.relpath(path, os.getcwd())
        fullpath = os.path.join(web_path, relpath)
        return fullpath

    def do_OPTIONS(self):
        self.send_response(200)

        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.send_header('Content-Type', 'application/json')

        self.end_headers()

    def do_HEAD(self):
        self.send_response(200)

        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.send_header('Content-Type', 'application/json')

        self.end_headers()

    def do_GET(self):
        response = self.respond(None)
        if response == False:
            return super().do_GET()

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

        self.respond(data)

    def handle_http(self, data):
        resp = {'status': 'OK'}
        uri = urlparse(self.path)
        path = uri.path
        query = parse_qs(uri.query)
        status_code = 200

        try:
            if path == '/info':
                resp['name'] = 'Padmiss daemon'
                resp['version'] = '1.0'
                resp['ip'] = config.webserver.host + ':' + str(config.webserver.port)
            elif path == '/home':
                tpl = Template(filename=resource_path('web/index.html'))
                resp = tpl.render(cabApiUrl='http://' + config.webserver.host + ':' + str(config.webserver.port))
            elif path == '/pads/list':
                pads = []
                i = 1

                for p in fsrio.detectPads():
                    pads.append({
                        'side': p.side,
                        'number': i,
                        'port': p.port
                    })
                    i += 1

                resp['pads'] = pads
            elif path == '/pads/gui':
                if 'pad' in query:
                    pad = fsrio.getPad(query['pad'][0])
                    if pad == False:
                        raise ServiceException('Pad not found')

                    tpl = Template(filename=resource_path('web/pad.html'))
                    resp = tpl.render(pad = pad)
                else:
                    tpl = Template(filename=resource_path('web/pads.html'))
                    resp = tpl.render(pads = fsrio.detectPads())

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
                driver = self.get_poller_driver(side)
                if driver == None:
                    raise ServiceException('Side not available')

                try:
                    driver.togglePlayer(data['player'], 'in')
                except Exception as e:
                    raise ServiceException(str(e))

                resp['message'] = 'Checked in'

            elif path == '/check_out':
                if data is None or not 'side' in data:
                    raise ServiceException('Side or player not provided')

                side = int(data['side'])
                driver = self.get_poller_driver(side)
                if driver == None:
                    raise ServiceException('Side not available')

                try:
                    driver.togglePlayer(data['player'], 'out')
                except Exception as e:
                    raise ServiceException(str(e))

                resp['message'] = 'Checked out'

            else:
                return False

        except ServiceException as e:
            status_code = 500
            resp['status'] = 'ERR'
            resp['message'] = str(e)

        self.send_response(status_code)
        self.send_header('Access-Control-Allow-Headers', '*')
        self.send_header('Access-Control-Allow-Origin', '*')

        if type(resp) == str:
            content = resp
        else:
            self.send_header('Content-Type', 'application/json')
            content = json.dumps(resp)

        self.send_header('Content-Length', len(content))
        self.end_headers()

        return bytes(content, 'UTF-8')

    def respond(self, data):
        response = self.handle_http(data)
        if response == False:
            return response

        self.wfile.write(response)
        return True


class RestServerThread(CancellableThrowingThread):
    def __init__(self, pollers, setConfig):
        self.pollers = pollers
        config = setConfig
        self.config = setConfig
        self.api = TournamentApi(config)

        super().__init__()
        self.setName('Rest server')

    def exc_run(self):

        RestServer.pollers = self.pollers
        httpd = HTTPServer((self.config.webserver.host, self.config.webserver.port), RestServer)
        lastPing = 0

        while not self.stop_event.wait(0.2):
            httpd.timeout = 0.2
            httpd.handle_request()

            if self.config.webserver.broadcast:
                if time.time() > (lastPing + 25):
                    self.api.broadcast()
                    lastPing = time.time()

        httpd.server_close()
