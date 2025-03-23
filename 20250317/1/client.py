import socket
import cmd
import shlex
import cowsay
from common import cow_files, communicate

class MudCmd(cmd.Cmd):
    prompt = "(MUD) "
    intro = "<<< Welcome to Python-MUD 0.1 Client >>>"
    def __init__(self):
        super().__init__()
        self.valid_monsters = cowsay.list_cows() + ["jgsbat"]
        self.weapons = {"sword": 10, "spear": 15, "axe": 20}
        self.sock = None
        self.connect()

    def connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect(('localhost', 12345))
        except Exception:
            self.sock = None
            print("Error: Cannot connect to server")

    def do_move(self, direction):
        if not self.sock:
            self.connect()
            if not self.sock:
                print("Error: Cannot connect to server")
                return
        moves = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}
        if direction not in moves:
            print("Invalid direction")
            return
        dx, dy = moves[direction]
        response = communicate(self.sock, {"type": "move", "dx": dx, "dy": dy})
        if response is None or not isinstance(response, dict) or "type" not in response:
            print("Error: Invalid server response")
            self.sock.close()
            self.sock = None
            return
        if response["type"] == "position":
            print(f"Moved to ({response['x']}, {response['y']})")
        elif response["type"] == "encounter":
            print(cowsay.cowsay(response["hello"], cow=cow_files.get(response["name"], response["name"])))
        elif response["type"] == "error":
            print(f"Error: {response['message']}")
            if "Connection" in response["message"]:
                self.sock.close()
                self.sock = None

    def do_up(self, arg):
        self.do_move("up")

    def do_down(self, arg):
        self.do_move("down")

    def do_left(self, arg):
        self.do_move("left")

    def do_right(self, arg):
        self.do_move("right")

    def do_addmon(self, arg):
        if not self.sock:
            self.connect()
            if not self.sock:
                print("Error: Cannot connect to server")
                return
        parts = shlex.split(arg)
        if len(parts) < 6:
            print("Invalid arguments")
            return
        try:
            name, params = parts[0], {}
            if name not in self.valid_monsters:
                print("Cannot add unknown monster")
                return
            i = 1
            while i < len(parts):
                if parts[i] == "coords" and i + 2 < len(parts):
                    params["x"], params["y"] = int(parts[i + 1]), int(parts[i + 2])
                    i += 3
                elif parts[i] in ("hello", "hp") and i + 1 < len(parts):
                    params[parts[i]] = parts[i + 1] if parts[i] == "hello" else int(parts[i + 1])
                    i += 2
                else:
                    print("Invalid arguments")
                    return
            if not all(k in params for k in ("hello", "hp", "x", "y")):
                print("Missing required arguments")
                return
            if params["hp"] <= 0:
                print("Hitpoints must be positive")
                return
            if not (0 <= params["x"] <= 9 and 0 <= params["y"] <= 9):
                print("Coordinates out of bounds")
                return
            response = communicate(self.sock, {
                "type": "addmon", "x": params["x"], "y": params["y"],
                "name": name, "hello": params["hello"], "hp": params["hp"]
            })
            if response is None or not isinstance(response, dict) or "type" not in response:
                print("Error: Invalid server response")
                self.sock.close()
                self.sock = None
                return
            if response["type"] == "added_monster":
                print(f"Added monster {name} to ({params['x']}, {params['y']}) saying {params['hello']}")
                if response.get("replaced", False):
                    print("Replaced the old monster")
            elif response["type"] == "error":
                print(f"Error: {response['message']}")
                if "Connection" in response["message"]:
                    self.sock.close()
                    self.sock = None
        except ValueError:
            print("Invalid arguments")

    def complete_addmon(self, text, line, begidx, endidx):
        args = shlex.split(line[:begidx])
        if len(args) == 1:
            return [name for name in self.valid_monsters if name.startswith(text)]
        keywords = ["hp", "coords", "hello"]
        used = set(arg for arg in args[1:] if arg in keywords)
        return [kw for kw in keywords if kw not in used and kw.startswith(text)]

    def do_attack(self, arg):
        if not self.sock:
            self.connect()
            if not self.sock:
                print("Error: Cannot connect to server")
                return
        parts = shlex.split(arg)
        if len(parts) < 1 or len(parts) > 3 or (len(parts) == 3 and parts[1] != "with"):
            print("Invalid arguments")
            return
        monster_name = parts[0]
        weapon = "sword" if len(parts) == 1 else parts[2]
        if weapon not in self.weapons:
            print("Unknown weapon")
            return
        response = communicate(self.sock, {"type": "attack", "name": monster_name, "damage": self.weapons[weapon]})
        if response is None or not isinstance(response, dict) or "type" not in response:
            print("Error: Invalid server response")
            self.sock.close()
            self.sock = None
            return
        if response["type"] == "attack_result":
            if not response["success"]:
                print(f"No {monster_name} here")
            else:
                print(f"Attacked {monster_name}, damage {response['damage']} hp")
                if response["remaining_hp"] == 0:
                    print(f"{monster_name} died")
                else:
                    print(f"{monster_name} now has {response['remaining_hp']}")
        elif response["type"] == "error":
            print(f"Error: {response['message']}")
            if "Connection" in response["message"]:
                self.sock.close()
                self.sock = None

    def complete_attack(self, text, line, begidx, endidx):
        args = shlex.split(line[:begidx])
        if len(args) <= 1:
            return [name for name in self.valid_monsters if name.startswith(text)]
        if len(args) == 2:
            return ["with"] if "with".startswith(text) else []
        if len(args) == 3 and args[2] == "with":
            return [w for w in self.weapons if w.startswith(text)]
        return []

    def do_quit(self, arg):
        print("Goodbye!")
        if self.sock:
            self.sock.close()
        return True

    def do_EOF(self, arg):
        print("Goodbye!")
        if self.sock:
            self.sock.close()
        return True

    def emptyline(self):
        pass

if __name__ == "__main__":
    MudCmd().cmdloop()