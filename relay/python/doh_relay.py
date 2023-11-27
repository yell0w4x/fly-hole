#/usr/bin/env python3

from aiohttp import web
from aiohttp.web import HTTPBadRequest, HTTPBadGateway, HTTPMethodNotAllowed
from base64 import b64decode
import asyncio
import binascii


ADDRESS = '0.0.0.0'
PORT = 8000
DNS_ENDPOINT = '127.0.0.1', 53
DNS_SOCK_TIMEOUT = 5


class RelayProtocol:
    def __init__(self, message, on_connection_lost, on_response, on_error):
        self.__message = message
        self.__on_connection_lost = on_connection_lost
        self.__on_response = on_response
        self.__on_error = on_error
        self.__transport = None

    def connection_made(self, transport):
        self.__transport = transport
        transport.sendto(self.__message)

    def datagram_received(self, data, addr):
        self.__transport.close()
        self.__on_response.set_result(data)

    def error_received(self, exc):
        self.__on_error.set_exception(exc)

    def connection_lost(self, exc):
        self.__on_connection_lost.set_result(True)    


async def dns_relay(dns_req):
    loop = asyncio.get_running_loop()
    on_connection_lost = loop.create_future()
    on_response = loop.create_future()
    on_error = loop.create_future()

    transport, _ = await loop.create_datagram_endpoint(
        lambda: RelayProtocol(dns_req, on_connection_lost, on_response, on_error),
        remote_addr=DNS_ENDPOINT)

    try:
        done, pending = await asyncio.wait([on_response, on_connection_lost, on_error], 
                                           timeout=DNS_SOCK_TIMEOUT, return_when=asyncio.FIRST_COMPLETED)
    finally:
        transport.close()

    if on_response not in done:
        raise HTTPBadGateway()
    
    return on_response.result()


def create_view():
    DNS_MESSAGE_TYPE = 'application/dns-message'

    routes = web.RouteTableDef()

    @routes.view('/')
    class RelayHandler(web.View):
        async def get(self):
            request = self.request
            if 'dns' not in request.query:
                raise HTTPBadRequest()

            dns_req_b64 = request.query['dns']
            if not dns_req_b64:
                raise HTTPBadRequest()

            try:
                dns_req = b64decode(f'{dns_req_b64}==')
            except binascii.Error:
                raise HTTPBadRequest
            else:
                return await self.__handle(dns_req)

        async def post(self):
            PAYLOAD_LIMIT = 2 ** 17
            request = self.request
            if request.content_type != DNS_MESSAGE_TYPE:
                raise HTTPBadRequest()

            dns_req = await request.content.read(PAYLOAD_LIMIT)
            if not dns_req:
                raise HTTPBadRequest()

            return await self.__handle(dns_req)

        async def __handle(self, dns_req):
            dns_resp = await dns_relay(dns_req)
            return web.Response(body=dns_resp, content_type=DNS_MESSAGE_TYPE)

    return routes


def main():
    app = web.Application()
    app.router.add_routes(create_view())
    web.run_app(app, host=ADDRESS, port=PORT)


if __name__ == '__main__':
    main()
