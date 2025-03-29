import socket
import json
import cowsay
from common import Monster, Gamer, communicate

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

def handle_move(game, command):
    dx, dy = command["dx"], command["dy"]
    game.player.move(dx, dy)
    x, y = game.player.get_position()
    response = {"type": "position", "x": x, "y": y}
    if (x, y) in game.field:
        monster = game.field[(x, y)]
        response = {"type": "encounter", "name": monster.name, "hello": monster.hello}
    return response

def handle_addmon(game, command):
    x, y, name, hello, hp = command["x"], command["y"], command["name"], command["hello"], command["hp"]
    replaced = game.add_monster(x, y, name, hello, hp)
    return {"type": "added_monster", "x": x, "y": y, "name": name, "replaced": replaced}

def handle_attack(game, command):
    name, damage = command["name"], command["damage"]
    success, damage_dealt, remaining_hp = game.attack_monster(name, damage)
    return {"type": "attack_result", "success": success, "damage": damage_dealt, "remaining_hp": remaining_hp}

COMMAND_HANDLERS = {
    "move": handle_move,
    "addmon": handle_addmon,
    "attack": handle_attack
}

def handle_client(conn, addr, game):
    print(f"Client connected: {addr}")
    while True:
        command = communicate(conn)
        if command["type"] == "error":
            print(f"Client disconnected: {addr}")
            break
        handler = COMMAND_HANDLERS.get(command["type"], lambda g, c: {"type": "error", "message": "Unknown command"})
        response = handler(game, command)
        conn.send(json.dumps(response).encode() + b"\n")
    conn.close()
    print(f"Client disconnected: {addr}")

def main():
    game = Game()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server.bind(('localhost', 12345))
        server.listen(1)
        print("Server started on localhost:12345")
        while True:
            conn, addr = server.accept()
            handle_client(conn, addr, game)
    except KeyboardInterrupt:
        print("Shutting down server")
    finally:
        server.close()

if __name__ == "__main__":
    main()