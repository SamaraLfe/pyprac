import socket
import json
from io import StringIO
import cowsay

jgsbat = cowsay.read_dot_cow(StringIO("""
$the_cow = <<EOC;
    ,_                    _,
    ) '-._  ,_    _,  _.-' (
    )  _.-'.|\\--//|.'-._  (
     )'   .'\\/o\\/o\\/'.   `(
      ) .' . \\====/ . '. (
       )  / <<    >> \\  (
        '-._/``  ``\\_.-'
  jgs     __\\'--'//__
         (((""`  `"")))
EOC
"""))

cow_files = {"jgsbat": jgsbat}

class Person:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def get_position(self):
        return (self.x, self.y)

class Monster(Person):
    def __init__(self, x, y, name, hello, hitpoints):
        super().__init__(x, y)
        self.name = name
        self.hello = hello
        self.hitpoints = hitpoints

class Gamer(Person):
    def __init__(self, x, y):
        super().__init__(x, y)

    def move(self, dx, dy):
        self.x = (self.x + dx) % 10
        self.y = (self.y + dy) % 10

def communicate(sock, command=None):
    try:
        if command is not None:
            sock.send(json.dumps(command).encode() + b"\n")
        data = b""
        while True:
            chunk = sock.recv(1024)
            if not chunk:
                return {"type": "error", "message": "Connection closed"}
            data += chunk
            try:
                return json.loads(data.decode())
            except json.JSONDecodeError:
                continue
    except Exception as e:
        return {"type": "error", "message": str(e)}