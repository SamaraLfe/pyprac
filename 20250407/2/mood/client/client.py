"""Client implementation for the MOOD game."""
import socket
import cmd
import shlex
import cowsay
import json
import sys
import threading
import readline
import time
from typing import Optional, TextIO

from ..common.models import cow_files


class MudCmd(cmd.Cmd):
    """Command-line interface for the MOOD game client.

    Attributes:
        username (str): The player's username.
        valid_monsters (list): List of valid monster names from cowsay and jgsbat.
        weapons (dict): Mapping of weapon names to their damage values.
        sock (Optional[socket.socket]): Socket for server communication.
        connected (bool): Indicates if the client is connected to the server.
        receiver_thread (Optional[threading.Thread]): Thread for receiving server messages.
        last_command_time (float): Timestamp of the last sent command for delay enforcement.
    """
    try:
        prompt = "(" + sys.argv[1] + ") "
    except Exception:
        prompt = "(MUD) "

    def __init__(self, username: str, stdin: Optional[TextIO] = None):
        """Initialize the MOOD client.

        Args:
            username: The player's username.
            stdin: Optional file object to read commands from (default: sys.stdin).
        """
        super().__init__(stdin=stdin)
        self.username = username
        self.valid_monsters = cowsay.list_cows() + ["jgsbat"]
        self.weapons = {"sword": 10, "spear": 15, "axe": 20}
        self.sock: Optional[socket.socket] = None
        self.connected = False
        self.receiver_thread: Optional[threading.Thread] = None
        self.last_command_time = 0.0
        if not self.connect():
            print("Failed to connect to server. Exiting.")
            sys.exit(1)

    def connect(self) -> bool:
        """Connect to the MOOD server.

        Returns:
            bool: True if connection is successful, False otherwise.
        """
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
            self.receiver_thread = threading.Thread(
                target=self.receive_messages, daemon=True
            )
            self.receiver_thread.start()
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            if self.sock:
                self.sock.close()
            return False

    def receive_messages(self) -> None:
        """Receive and process messages from the server."""
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
                        sys.stdout.write('\r' + ' ' * (
                            len(self.prompt) + len(current_line)
                        ) + '\r')
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

    def display_message(self, message: dict) -> None:
        """Display server messages to the user.

        Args:
            message: The message received from the server.
        """
        t = message.get("type", "")
        if t == "broadcast":
            print(f"\n[BROADCAST] {message.get('message')}")
        elif t == "position":
            print(f"\nMoved to ({message['x']}, {message['y']})")
        elif t == "encounter":
            print("\n" + cowsay.cowsay(
                message["hello"],
                cow=cow_files.get(message["name"], message["name"])
            ))
        elif t == "attack_result":
            if not message["success"]:
                print(f"\nNo {message.get('name', 'monster')} here")
            else:
                print(
                    f"\nAttacked {message.get('name', 'monster')}, "
                    f"damage {message['damage']} hp"
                )
                if message.get("killed", message.get("remaining_hp", 0) == 0):
                    print(f"{message.get('name', 'Monster')} died")
                else:
                    print(
                        f"{message.get('name', 'Monster')} now has "
                        f"{message['remaining_hp']}"
                    )
        elif t == "added_monster":
            print(f"\nAdded monster at ({message['x']}, {message['y']})")
            if message.get("replaced", False):
                print("Replaced the old monster")
        elif t == "sayall_result":
            if message.get("success"):
                print(f"\nmessage \"{message.get('message')}\" sent")
        elif t == "timer_result":
            print(f"\nServer uptime: {message['uptime']} seconds")
        elif t == "monster_move":
            print(f"\nMonster {message['name']} moved one cell {message['direction']}")
        elif t == "error":
            print(f"\nError: {message.get('message', 'Unknown error')}")

    def send_command(self, cmd_obj: dict) -> bool:
        """Send a command to the server with a minimum 1-second delay.

        Args:
            cmd_obj: The command to send.

        Returns:
            bool: True if the command was sent successfully, False otherwise.
        """
        if not self.connected:
            print("Not connected to server")
            return False

        # Enforce 1-second delay between commands
        current_time = time.time()
        if current_time - self.last_command_time < 1:
            time.sleep(1 - (current_time - self.last_command_time))
        self.last_command_time = time.time()

        try:
            self.sock.send(json.dumps(cmd_obj).encode() + b"\n")
            return True
        except Exception as e:
            print(f"Error sending command: {e}")
            self.connected = False
            return False

    def do_move(self, direction: str) -> None:
        """Move the player in the specified direction.

        Args:
            direction: The direction to move ('up', 'down', 'left', 'right').
        """
        moves = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}
        if direction not in moves:
            print("Invalid direction")
            return
        dx, dy = moves[direction]
        self.send_command({"type": "move", "dx": dx, "dy": dy})

    def do_up(self, arg: str) -> None:
        """Move the player up."""
        self.do_move("up")

    def do_down(self, arg: str) -> None:
        """Move the player down."""
        self.do_move("down")

    def do_left(self, arg: str) -> None:
        """Move the player left."""
        self.do_move("left")

    def do_right(self, arg: str) -> None:
        """Move the player right."""
        self.do_move("right")

    def do_addmon(self, arg: str) -> None:
        """Add a monster to the game field.

        Args:
            arg: Command arguments in the format '<name> coords <x> <y> hello <msg> hp <value>'.
        """
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
                    params[parts[i]] = (
                        parts[i + 1] if parts[i] == "hello" else int(parts[i + 1])
                    )
                    i += 2
                else:
                    print("Invalid arguments")
                    return
            if not all(k in params for k in ("hello", "hp", "x", "y")) or \
               params["hp"] <= 0 or not (0 <= params["x"] <= 9 and 0 <= params["y"] <= 9):
                print("Invalid parameters")
                return
            self.send_command({
                "type": "addmon",
                "x": params["x"],
                "y": params["y"],
                "name": name,
                "hello": params["hello"],
                "hp": params["hp"]
            })
        except ValueError:
            print("Invalid arguments")

    def complete_addmon(self, text: str, line: str, begidx: int, endidx: int) -> list[str]:
        """Provide tab completion for the addmon command.

        Args:
            text: The current text being typed.
            line: The full command line.
            begidx: The start index of the text being completed.
            endidx: The end index of the text being completed.

        Returns:
            list[str]: Possible completions for the current input.
        """
        args = shlex.split(line[:begidx])
        if len(args) == 1:
            return [m for m in self.valid_monsters if m.startswith(text)]
        keywords = ["hp", "coords", "hello"]
        used = set(a for a in args[1:] if a in keywords)
        return [k for k in keywords if k not in used and k.startswith(text)]

    def do_attack(self, arg: str) -> None:
        """Attack a monster with a specified weapon.

        Args:
            arg: Command arguments in the format '<monster> [with <weapon>]'.
        """
        parts = shlex.split(arg)
        if len(parts) < 1 or len(parts) > 3 or (len(parts) == 3 and parts[1] != "with"):
            print("Invalid arguments")
            return
        monster = parts[0]
        weapon = "sword" if len(parts) == 1 else parts[2]
        if weapon not in self.weapons:
            print("Unknown weapon")
            return
        self.send_command({
            "type": "attack",
            "name": monster,
            "weapon": weapon,
            "damage": self.weapons[weapon]
        })

    def complete_attack(self, text: str, line: str, begidx: int, endidx: int) -> list[str]:
        """Provide tab completion for the attack command.

        Args:
            text: The current text being typed.
            line: The full command line.
            begidx: The start index of the text being completed.
            endidx: The end index of the text being completed.

        Returns:
            list[str]: Possible completions for the current input.
        """
        args = shlex.split(line[:begidx])
        if len(args) <= 1:
            return [m for m in self.valid_monsters if m.startswith(text)]
        if len(args) == 2:
            return ["with"] if "with".startswith(text) else []
        if len(args) == 3 and args[1] == "with":
            return [w for w in self.weapons if w.startswith(text)]
        return []

    def do_sayall(self, arg: str) -> None:
        """Send a message to all players.

        Args:
            arg: The message, either a single word or a quoted string.
        """
        parts = shlex.split(arg)
        if len(parts) != 1:
            print("Invalid arguments: provide a single word or a quoted string")
            return
        message = parts[0]
        self.send_command({"type": "sayall", "message": message})

    def do_timer(self, arg: str) -> None:
        """Request the server uptime.

        Args:
            arg: Should be empty.
        """
        if arg:
            print("Timer command takes no arguments")
            return
        self.send_command({"type": "timer"})

    def complete_timer(self, text: str, line: str, begidx: int, endidx: int) -> list[str]:
        """Provide tab completion for the timer command.

        Args:
            text: The current text being typed.
            line: The full command line.
            begidx: The start index of the text being completed.
            endidx: The end index of the text being completed.

        Returns:
            list[str]: Possible completions for the current input.
        """
        return []

    def do_quit(self, arg: str) -> bool:
        """Quit the game.

        Args:
            arg: Ignored.

        Returns:
            bool: True to exit the command loop.
        """
        print("Goodbye!")
        self.connected = False
        if self.sock:
            self.sock.close()
        return True

    def do_EOF(self, arg: str) -> bool:
        """Handle EOF (Ctrl+D or end of file) to quit the game.

        Args:
            arg: Ignored.

        Returns:
            bool: True to exit the command loop.
        """
        print("Goodbye!")
        self.connected = False
        if self.sock:
            self.sock.close()
        return True

    def emptyline(self) -> None:
        """Handle empty line input."""
        pass