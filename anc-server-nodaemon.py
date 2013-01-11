#!/usr/bin/python

__author__ = 'behemot'

import subprocess
import urlparse
import daemon
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

if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 8080), GetHandler)
    print 'Starting server, use <Ctrl-C> to stop'
    server.serve_forever()
