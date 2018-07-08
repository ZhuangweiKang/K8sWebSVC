#!/usr/bin/python3
# Author: Zhuangwei Kang
# -*- coding: utf-8 -*-

import os
import zmq

config_file = '/etc/haproxy/haproxy.cfg'


def fetch():
    records = []
    # Read file into a list
    with open(config_file, 'r') as robj:
        for line in robj:
            records.append(line)
    return records


def write_back(records):
    # Write new configuration info back
    with open(config_file, 'w') as wobj:
        for line in records:
            wobj.write(line)
    print('HAproxy configuration file has been changed.')


def hot_reload():
    sf_reload = 'haproxy -f /etc/haproxy/haproxy.cfg -p /var/run/haproxy.pid -sf $(cat /var/run/haproxy.pid)'
    os.system(sf_reload)


def add_server(backend, host_name, address, port):
    records = fetch()
    hasBackend = False
    # insert new server info into list if expected backend is avaliable
    for i, line in enumerate(records[:]):
        if line.strip().startswith('backend ' + backend):
            hasBackend = True
        if i != len(records) - 1 and line.strip().startswith('server') and records[i + 1].strip().startswith(
                'server') is False:
            new_record = '    server ' + host_name + ' ' + address + ':' + str(port) + ' check inter 100 maxconn 256\n'
            records.insert(i + 1, new_record)
            print('Insert new server under backend %s.' % backend)
            break

    # if expected backend is unavailable, insert a new backend at the end of file
    if hasBackend is False:
        print(
            'Expected backend is unavailable, backend %s will be inserted at the end of configuration file.' % backend)
        new_records = 'backend ' + backend + '\n' + '    mode tcp\n    fullconn 10000\n    balance source\n' + '    server ' + host_name + ' ' + address + ':' + str(
            port) + ' check inter 100 maxconn 256\n'
        records.append(new_records)

    write_back(records)

    # hot reload haproxy
    hot_reload()


def delete_server(backend, host_name):
    records = []
    records = fetch()
    hasBackend = False
    for i, line in enumerate(records[:]):
        if line.strip().startswith('backend ' + backend):
            hasBackend = True
        if line.strip().startswith('server ' + host_name):
            del records[i]
    if hasBackend is False:
        print('Specified backend is unavailable.')
    else:
        write_back(records)

    # hot reload haproxy
    hot_reload()


# Listen messages from Master node.
def build_socket(port):
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind('tcp://*:' + port)
    return socket


def listen_update(port):
    socket = build_socket(port)
    while True:
        msg = socket.recv_json()
        socket.send_string('Ack')
        option = msg['option']
        backend = msg['backend']
        host_name = msg['host_name']
        address = msg['address']
        port = msg['port']
        if option == 'scale-in':
            add_server(backend, host_name, address, port)
        elif option == 'scale-out':
            delete_server(backend, host_name)