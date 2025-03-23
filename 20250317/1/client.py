import socket
import json
import cmd
import shlex
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

cow_files = {"jgsbat": jgsbat}

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
            self.sock.settimeout(1.0)
            self.sock.connect(('localhost', 12345))
        except Exception as e:
            self.sock = None

    def send_command(self, command):
        if self.sock is None:
            self.connect()
            if self.sock is None:
                return {"type": "error", "message": "Cannot connect to server"}
        try:
            self.sock.send(json.dumps(command).encode() + b"\n")
            data = b""
            while True:
                try:
                    chunk = self.sock.recv(1024)
                    if not chunk:
                        self.sock.close()
                        self.sock = None
                        return {"type": "error", "message": "Server disconnected"}
                    data += chunk
                    try:
                        response = json.loads(data.decode())
                        return response
                    except json.JSONDecodeError:
                        continue
                except socket.timeout:
                    self.sock.close()
                    self.sock = None
                    return {"type": "error", "message": "No response from server"}
                except ConnectionError:
                    self.sock.close()
                    self.sock = None
                    return {"type": "error", "message": "Connection error"}
        except Exception as e:
            self.sock.close()
            self.sock = None
            return {"type": "error", "message": str(e)}

    def _move(self, direction, arg):
        if arg:
            print("Invalid arguments")
            return
        dx, dy = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}[direction]
        response = self.send_command({"type": "move", "dx": dx, "dy": dy})
        if response["type"] == "position":
            print(f"Moved to ({response['x']}, {response['y']})")
        elif response["type"] == "encounter":
            cowfile = cow_files.get(response["name"], response["name"])
            print(cowsay.cowsay(response["hello"], cow=cowfile))
        elif response["type"] == "error":
            print(f"Error: {response['message']}")

    def do_up(self, arg):
        self._move("up", arg)

    def do_down(self, arg):
        self._move("down", arg)

    def do_left(self, arg):
        self._move("left", arg)

    def do_right(self, arg):
        self._move("right", arg)

    def do_addmon(self, arg):
        parts = shlex.split(arg)
        if len(parts) < 6:
            print("Invalid arguments")
            return
        try:
            name = parts[0]
            if name not in self.valid_monsters:
                print("Cannot add unknown monster")
                return
            params = {}
            i = 1
            while i < len(parts):
                if parts[i] in ("hello", "hp", "coords") and i + 1 < len(parts):
                    if parts[i] == "coords" and i + 2 < len(parts):
                        params["x"], params["y"] = int(parts[i + 1]), int(parts[i + 2])
                        i += 3
                    else:
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
            response = self.send_command({
                "type": "addmon",
                "x": params["x"],
                "y": params["y"],
                "name": name,
                "hello": params["hello"],
                "hp": params["hp"]
            })
            if response["type"] == "added_monster":
                print(f"Added monster {name} to ({params['x']}, {params['y']}) saying {params['hello']}")
                if response.get("replaced", False):
                    print("Replaced the old monster")
            elif response["type"] == "error":
                print(f"Error: {response['message']}")
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
        parts = shlex.split(arg)
        if len(parts) < 1 or len(parts) > 3 or (len(parts) == 3 and parts[1] != "with"):
            print("Invalid arguments")
            return
        monster_name = parts[0]
        weapon = "sword" if len(parts) == 1 else parts[2]
        if weapon not in self.weapons:
            print("Unknown weapon")
            return
        response = self.send_command({"type": "attack", "name": monster_name, "damage": self.weapons[weapon]})
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