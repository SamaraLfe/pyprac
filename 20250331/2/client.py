import socket, cmd, shlex, cowsay, json, sys, threading, readline
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
    prompt = "(" + sys.argv[1] + ") "

    def __init__(self, username):
        super().__init__()
        self.username = username
        self.valid_monsters = cowsay.list_cows() + ["jgsbat"]
        self.weapons = {"sword": 10, "spear": 15, "axe": 20}
        self.sock = None
        self.connected = False
        self.receiver_thread = None
        if not self.connect():
            print("Failed to connect to server. Exiting.")
            sys.exit(1)

    def connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect(('localhost', 12345))
            self.sock.send(json.dumps({"username": self.username}).encode() + b"\n")

            data = b""
            while True:
                chunk = self.sock.recv(1024)
                if not chunk:
                    self.sock.close()
                    return False
                data += chunk
                try:
                    response = json.loads(data.decode())
                    break
                except json.JSONDecodeError:
                    continue

            if response.get("type") == "error":
                print(f"Authentication error: {response.get('message')}")
                self.sock.close()
                return False

            print(response.get("message", "Connected to server"))
            self.connected = True
            self.receiver_thread = threading.Thread(target=self.receive_messages, daemon=True)
            self.receiver_thread.start()
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            if self.sock: self.sock.close()
            return False

    def receive_messages(self):
        while self.connected:
            try:
                data = b""
                while self.connected:
                    chunk = self.sock.recv(1024)
                    if not chunk:
                        print("\nDisconnected from server")
                        self.connected = False
                        break
                    data += chunk
                    try:
                        message = json.loads(data.decode())
                        data = b""

                        current_line = readline.get_line_buffer()
                        sys.stdout.write('\r' + ' ' * (len(self.prompt) + len(current_line)) + '\r')
                        sys.stdout.flush()

                        self.display_message(message)

                        sys.stdout.write(self.prompt + current_line)
                        sys.stdout.flush()

                        readline.redisplay()
                        break
                    except json.JSONDecodeError:
                        continue
            except Exception as e:
                print(f"\nError receiving message: {e}")
                self.connected = False

    def display_message(self, message):
        t = message.get("type", "")
        if t == "broadcast":
            print(f"\n[BROADCAST] {message.get('message')}")
        elif t == "position":
            print(f"\nMoved to ({message['x']}, {message['y']})")
        elif t == "encounter":
            print("\n" + cowsay.cowsay(message["hello"], cow=cow_files.get(message["name"], message["name"])))
        elif t == "attack_result":
            if not message["success"]:
                print(f"\nNo {message.get('name', 'monster')} here")
            else:
                print(f"\nAttacked {message.get('name', 'monster')}, damage {message['damage']} hp")
                if message.get("killed", message.get("remaining_hp", 0) == 0):
                    print(f"{message.get('name', 'Monster')} died")
                else:
                    print(f"{message.get('name', 'Monster')} now has {message['remaining_hp']}")
        elif t == "added_monster":
            print(f"\nAdded monster at ({message['x']}, {message['y']})")
            if message.get("replaced", False):
                print("Replaced the old monster")
        elif t == "sayall_result":
            if message.get("success"):
                print(f"\nmessage \"{message.get('message')}\" sent")
        elif t == "error":
            print(f"\nError: {message.get('message', 'Unknown error')}")

    def send_command(self, cmd_obj):
        if not self.connected:
            print("Not connected to server")
            return False
        try:
            self.sock.send(json.dumps(cmd_obj).encode() + b"\n")
            return True
        except Exception as e:
            print(f"Error sending command: {e}")
            self.connected = False
            return False

    def do_move(self, direction):
        moves = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}
        if direction not in moves:
            print("Invalid direction")
            return
        dx, dy = moves[direction]
        self.send_command({"type": "move", "dx": dx, "dy": dy})

    def do_up(self, arg): self.do_move("up")
    def do_down(self, arg): self.do_move("down")
    def do_left(self, arg): self.do_move("left")
    def do_right(self, arg): self.do_move("right")

    def do_addmon(self, arg):
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
                if parts[i] == "coords" and i+2 < len(parts):
                    params["x"], params["y"] = int(parts[i+1]), int(parts[i+2])
                    i += 3
                elif parts[i] in ("hello","hp") and i+1 < len(parts):
                    params[parts[i]] = parts[i+1] if parts[i]=="hello" else int(parts[i+1])
                    i += 2
                else:
                    print("Invalid arguments")
                    return
            if not all(k in params for k in ("hello","hp","x","y")) or params["hp"]<=0 or not (0<=params["x"]<=9 and 0<=params["y"]<=9):
                print("Invalid parameters")
                return
            self.send_command({"type":"addmon","x":params["x"],"y":params["y"],"name":name,"hello":params["hello"],"hp":params["hp"]})
        except ValueError:
            print("Invalid arguments")

    def complete_addmon(self, text, line, begidx, endidx):
        args = shlex.split(line[:begidx])
        if len(args) == 1:
            return [m for m in self.valid_monsters if m.startswith(text)]
        keywords = ["hp","coords","hello"]
        used = set(a for a in args[1:] if a in keywords)
        return [k for k in keywords if k not in used and k.startswith(text)]

    def do_attack(self, arg):
        parts = shlex.split(arg)
        if len(parts)<1 or len(parts)>3 or (len(parts)==3 and parts[1]!="with"):
            print("Invalid arguments")
            return
        monster = parts[0]
        weapon = "sword" if len(parts)==1 else parts[2]
        if weapon not in self.weapons:
            print("Unknown weapon")
            return
        self.send_command({"type":"attack","name":monster,"weapon":weapon,"damage":self.weapons[weapon]})

    def complete_attack(self, text, line, begidx, endidx):
        args = shlex.split(line[:begidx])
        if len(args)<=1:
            return [m for m in self.valid_monsters if m.startswith(text)]
        if len(args)==2:
            return ["with"] if "with".startswith(text) else []
        if len(args)==3 and args[2]=="with":
            return [w for w in self.weapons if w.startswith(text)]
        return []

    def do_sayall(self, arg):
        parts = shlex.split(arg)
        if len(parts) != 1:
            print("Invalid arguments: provide a single word or a quoted string")
            return
        message = parts[0]
        self.send_command({"type": "sayall", "message": message})

    def do_quit(self, arg):
        print("Goodbye!")
        self.connected = False
        if self.sock: self.sock.close()
        return True

    def do_EOF(self, arg):
        print("Goodbye!")
        self.connected = False
        if self.sock: self.sock.close()
        return True

    def emptyline(self): pass

if __name__=="__main__":
    if len(sys.argv)!=2:
        print("Usage: python client.py <username>")
        sys.exit(1)
    if " " in sys.argv[1]:
        print("Error: Username cannot contain spaces")
        sys.exit(1)
    MudCmd(sys.argv[1]).cmdloop()