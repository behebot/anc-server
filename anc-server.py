#!/usr/bin/python

__author__ = 'behemot'

import subprocess
import urlparse
import argparse
import daemon
import socket
from BaseHTTPServer import (BaseHTTPRequestHandler, HTTPServer)
from IPy import IP

def check_address(address):
    p1 = subprocess.Popen(["/sbin/ip", "addr", "sh"], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(["/bin/grep", address], stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()
    output,err = p2.communicate()
    return p2.returncode

class GetHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse.urlparse(self.path)

        # parse query to dict
        params = urlparse.parse_qs(parsed_path.query)

        # get first value for parameter 'address'
        try:
            address = params.get('address')[0]
        except:
            # if there is no any, answer with 404
            result_code = 254
            response_code = 404
        else:
            # check if it is valid IP address
            try:
                IP(address)
            except:
                # if no, answer with 404
                result_code = 255
                response_code = 404
            finally:
                # if yes, check is it present in system
                result_code = check_address(address)
                if result_code == 0:
                    response_code = 200
                else:
                    response_code = 404

        message_parts = []
        message_parts.append(str(result_code))
        message_parts.append('')
        message = '\r\n'.join(message_parts)

        self.send_response(response_code)
        self.end_headers()
        self.wfile.write(message)
        return

class HTTPServerV6(HTTPServer):
    address_family = socket.AF_INET6

def parse_arguments():
    parser = argparse.ArgumentParser(description='Run anc-server')
    parser.add_argument('-p', '--port', help='Port number to use. Default: 8080', required=False, default=8080)
    parser.add_argument('-ipv4', '--ipv4', help='IPv4 address to bind to.', required=True)
    parser.add_argument('-ipv6', '--ipv6', help='IPv6 address to bind to. Should not be ::', required=False)
    args = vars(parser.parse_args())
    return args

def check_valid_IP(address):
    try:
        IP(address)
    except:
        result = False
    else:
        result = True
    return result

if __name__ == '__main__':
    args = parse_arguments()
    port = args['port']
    ipv4 = args['ipv4']
    ipv6 = args['ipv6']
    files_to_preserve = []
    if check_valid_IP(ipv4):
        v4server = HTTPServer((ipv4, port), GetHandler)
        files_to_preserve.append(v4server.fileno())
        if ipv6:
            if check_valid_IP(ipv6):
                v6server = HTTPServerV6((ipv6, port), GetHandler)
                files_to_preserve.append(v6server.fileno())
        # daemonization part
        daemon_context = daemon.DaemonContext()
        daemon_context.files_preserve = files_to_preserve

        with daemon_context:
            v4server.serve_forever()
            if ipv6:
                v6server.server_forever()
