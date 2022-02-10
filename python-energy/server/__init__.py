#!/usr/bin/env python

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

import server.energy_generation as generation
import server.energy_usage as usage
import server.utils as utils


class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-type', 'text/json')
        self.end_headers()
        response = {
            'usage': {},
            'generation': {},
        }
        for source in usage.sources:
            response['usage'][source.id] = {
                'name': source.name,
                'joules': source.joules,
                'watts': source.watts,
                'wattsOverTime': list(source.watts_over_time),
                'longTermJoules': source.long_term_joules,
            }
        response['generation'] = {
            'storage': list(map(lambda info: info.storage, generation.infos)),
            'renewable': list(map(lambda info: info.renewable, generation.infos)),
            'nonRenewable': list(map(lambda info: info.non_renewable, generation.infos)),
            'unknown': list(map(lambda info: info.unknown, generation.infos)),
        }
        self.wfile.write(bytes(json.dumps(response), 'utf-8'))
        self.wfile.write(bytes('\n', 'utf-8'))


def run():
    Thread(target=usage.monitor, args=()).start()
    Thread(target=generation.monitor, args=()).start()

    web_server = HTTPServer(('localhost', 35396), MyServer)
    print('Server started at http://%s:%s' % ('localhost', 35396))

    try:
        web_server.serve_forever()
    except KeyboardInterrupt:
        pass

    web_server.server_close()
    print('Server stopped. Interrupt again to also stop generation and usage monitors.')
