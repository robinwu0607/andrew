#!/usr/bin/python3
import os
import sys
import django
import json
import pickle
import socketserver

# add django setting, then could use django ORM/setting and so on.
sys.path.append('/opt/andrew')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

channel_layer = get_channel_layer()

HOST, PORT = '127.0.0.1', 9999


class UDPHandler(socketserver.BaseRequestHandler):

    def handle(self):
        msg = pickle.loads(self.request[0])
        if 'SEQ_LOG' in msg['target']:  # It is SEQ message
            data = msg['levelname'] + msg['msg'] + '\n'
        else:   # It is connection message
            data = msg['msg']
        if data:
            # print(data)
            station, container, conn = msg['target'].split(":")
            message = {
                'type': 'udp.message',
                'text':  json.dumps({
                    'testLogController': conn,
                    'testLog': data,
                })
            }
            group = '.ws.genius.{}.{}'.format(station, container).lower()
            # print(group)
            async_to_sync(channel_layer.group_send)(group, message)


def start_udp_server():
    with socketserver.UDPServer((HOST, PORT), UDPHandler) as server:
        server.serve_forever()
