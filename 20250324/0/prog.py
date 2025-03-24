import sys
import socket
from http.server import test, SimpleHTTPRequestHandler

HOST = socket.gethostbyname(socket.gethostname())
PORT = sys.argv[1] if len(sys.argv) > 1 else '8000'
print(HOST)
test(SimpleHTTPRequestHandler, port=int(PORT))