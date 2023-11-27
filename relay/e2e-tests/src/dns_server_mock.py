import signal
import multiprocessing
from socketserver import UDPServer, BaseRequestHandler
import sys


class DnsMockUdpHandler(BaseRequestHandler):
    def handle(self):
        print(f'{self.server.populate_error=}')
        if self.server.populate_error:
            # no response, make timeout occur
            return

        data, sock = self.request
        sock.sendto(bytes(reversed(data)), self.client_address)


def server_run(populate_error):
    SERVER_ENDPOINT = '127.0.0.1', 53
    
    with UDPServer(SERVER_ENDPOINT, DnsMockUdpHandler) as server:
        server.populate_error = populate_error
        server.serve_forever(poll_interval=0.1)
