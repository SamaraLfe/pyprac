import socket
import json
import cowsay
from io import StringIO

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

class Game:
    def __init__(self):
        self.field = {}
        self.player = Gamer(0, 0)
        self.valid_monsters = cowsay.list_cows() + ["jgsbat"]

    def add_monster(self, x, y, name, hello, hitpoints):
        key = (x, y)
        replaced = key in self.field
        self.field[key] = Monster(x, y, name, hello, hitpoints)
        return replaced

    def attack_monster(self, monster_name, damage):
        pos = self.player.get_position()
        if pos not in self.field or self.field[pos].name != monster_name:
            return False, 0, 0
        monster = self.field[pos]
        actual_damage = min(damage, monster.hitpoints)
        monster.hitpoints -= actual_damage
        remaining_hp = monster.hitpoints
        if monster.hitpoints == 0:
            del self.field[pos]
        return True, actual_damage, remaining_hp

def handle_client(conn, addr, game):
    print(f"Client connected: {addr}")
    conn.settimeout(1.0)
    while True:
        try:
            data = b""
            while True:
                try:
                    chunk = conn.recv(1024)
                    if not chunk:
                        print(f"Client disconnected: {addr}")
                        return
                    data += chunk
                    try:
                        command = json.loads(data.decode())
                        break
                    except json.JSONDecodeError:
                        continue
                except socket.timeout:
                    continue
                except ConnectionError:
                    print(f"Client disconnected: {addr}")
                    return
            cmd_type = command["type"]
            response = {}

            if cmd_type == "move":
                dx, dy = command["dx"], command["dy"]
                game.player.move(dx, dy)
                x, y = game.player.get_position()
                response = {"type": "position", "x": x, "y": y}
                if (x, y) in game.field:
                    monster = game.field[(x, y)]
                    response = {"type": "encounter", "name": monster.name, "hello": monster.hello}

            elif cmd_type == "addmon":
                x, y, name, hello, hp = command["x"], command["y"], command["name"], command["hello"], command["hp"]
                replaced = game.add_monster(x, y, name, hello, hp)
                response = {"type": "added_monster", "x": x, "y": y, "name": name, "replaced": replaced}

            elif cmd_type == "attack":
                name, damage = command["name"], command["damage"]
                success, damage_dealt, remaining_hp = game.attack_monster(name, damage)
                response = {"type": "attack_result", "success": success, "damage": damage_dealt, "remaining_hp": remaining_hp}

            else:
                response = {"type": "error", "message": "Unknown command"}

            conn.send(json.dumps(response).encode() + b"\n")
        except Exception as e:
            print(f"Client disconnected: {addr}")
            break
    conn.close()

def main():
    game = Game()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server.bind(('localhost', 12345))
        server.listen(1)
        print("Server started on localhost:12345")
        while True:
            try:
                conn, addr = server.accept()
                handle_client(conn, addr, game)
            except KeyboardInterrupt:
                print("Shutting down server")
                break
    finally:
        server.close()

if __name__ == "__main__":
    main()