import socket
import json
import random
import asyncio
import threading
import time
import cowsay
import gettext
import os
from typing import Dict, Tuple, Optional

from ..common.models import Monster, Gamer


class Server:
    """MOOD game server implementation."""
    def __init__(self, host: str = 'localhost', port: int = 12345):
        self.host = host
        self.port = port
        self.game = Game()
        self.sock = None

    def start_server(self) -> None:
        """Start the MOOD game server."""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        threading.Thread(target=start_loop, daemon=True).start()
        threading.Thread(target=schedule_monster_movement, args=(self.game,), daemon=True).start()
        try:
            self.sock.bind((self.host, self.port))
            self.sock.listen(5)
            print(f"Server running on {self.host}:{self.port}")
            accept_connections(self.sock, self.game)
        except Exception as e:
            print(f"Server error: {e}")
        finally:
            self.sock.close()
            loop.call_soon_threadsafe(loop.stop)


class Game:
    """Manages the game state for the MOOD server."""
    def __init__(self):
        self.field: Dict[Tuple[int, int], Monster] = {}
        self.players: Dict[str, Tuple[socket.socket, Gamer, str]] = {}
        self.valid_monsters = cowsay.list_cows() + ["jgsbat"]
        self.start_time = time.time()
        self.moving_monsters = True
        self.locales: Dict[str, gettext.GNUTranslations] = {}
        self.load_locales()

    def load_locales(self):
        """Load available translations."""
        locale_dir = os.path.join(os.path.dirname(__file__), 'locale')
        try:
            ru_trans = gettext.translation('messages', locale_dir, languages=['ru_RU'])
            self.locales['ru_RU'] = ru_trans
            print(f"Loaded translations for ru_RU from {locale_dir}")
        except FileNotFoundError as e:
            print(f"Warning: Could not load translations from {locale_dir}: {e}")

    def get_uptime(self) -> float:
        """Calculate server uptime in seconds."""
        return time.time() - self.start_time

    def add_player(self, username: str, conn: socket.socket) -> bool:
        """Add a player to the game."""
        if username in self.players:
            return False
        self.players[username] = (conn, Gamer(0, 0), 'en_US')
        return True

    def remove_player(self, username: str) -> bool:
        """Remove a player from the game."""
        return self.players.pop(username, None) is not None

    def get_player(self, username: str) -> Optional[Gamer]:
        """Get a player's Gamer object."""
        return self.players.get(username, (None, None, None))[1]

    def get_translation(self, username: str) -> gettext.GNUTranslations:
        """Get translation for a user."""
        _, _, locale = self.players.get(username, (None, None, 'en_US'))
        print(f"Getting translation for user {username}, locale {locale}")
        return self.locales.get(locale, gettext.NullTranslations())

    def add_monster(self, x: int, y: int, name: str, hello: str, hp: int) -> bool:
        """Add a monster to the game field."""
        key, replaced = (x, y), (x, y) in self.field
        self.field[key] = Monster(x, y, name, hello, hp)
        return replaced

    def attack_monster(self, username: str, name: str,
                       weapon: str, dmg: int) -> Tuple[bool, int, int, bool]:
        """Handle a player attacking a monster."""
        p = self.get_player(username)
        if not p:
            return False, 0, 0, False
        pos = p.get_position()
        m = self.field.get(pos)
        if not m or m.name != name:
            return False, 0, 0, False
        d = min(dmg, m.hitpoints)
        m.hitpoints -= d
        killed = m.hitpoints == 0
        if killed:
            del self.field[pos]
        return True, d, m.hitpoints, killed

    def send_to_all(self, msg: Dict) -> None:
        """Send a message to all players with their respective locales."""
        for username, (conn, _, _) in self.players.items():
            data = json.dumps(msg).encode() + b"\n"
            asyncio.run_coroutine_threadsafe(self._send_async(conn, data, username), loop)

    async def _send_async(self, conn: socket.socket, data: bytes, username: str) -> None:
        """Asynchronously send localized data to a connection."""
        try:
            msg = json.loads(data.decode())
            t = self.get_translation(username)
            if msg.get("type") == "broadcast":
                original = msg["message"]
                print(f"Translating broadcast for {username}: {original}")
                if " added " in original and " at " in original:
                    user, rest = original.split(" added ")
                    mon, rest = rest.split(" at ")
                    coords, hello = rest.split(" saying ")
                    x, y = map(int, coords.strip('()').split(','))
                    msg["message"] = t.gettext("%s added %s at (%d,%d) saying %s") % (user, mon, x, y, hello)
                elif original.endswith("joined the game!"):
                    user = original.split()[0]
                    msg["message"] = t.gettext("%s joined the game!") % user
                elif original.endswith("left the game!"):
                    user = original.split()[0]
                    msg["message"] = t.gettext("%s left the game!") % user
                elif "attacked" in original:
                    parts = original.split()
                    user, mon, weapon, dealt = parts[0], parts[2], parts[4].rstrip(','), int(parts[6])
                    if original.endswith("was killed!"):
                        msg["message"] = t.ngettext(
                            "%s attacked %s with %s, dealing %d damage. %s was killed!",
                            "%s attacked %s with %s, dealing %d damage. %s has %d HP remaining.",
                            0
                        ) % (user, mon, weapon, dealt, mon)
                    else:
                        hp = int(parts[-3])
                        msg["message"] = t.ngettext(
                            "%s attacked %s with %s, dealing %d damage. %s was killed!",
                            "%s attacked %s with %s, dealing %d damage. %s has %d HP remaining.",
                            hp
                        ) % (user, mon, weapon, dealt, mon, hp)
                elif " moved to " in original:
                    user, coords = original.split(" moved to ")
                    x, y = map(int, coords.strip('()').split(','))
                    msg["message"] = t.gettext("%s moved to (%d,%d)") % (user, x, y)
                elif "Monster" in original and "moved one cell" in original:
                    name = original.split(" moved")[0].replace("Monster ", "")
                    direction = original.split(" moved one cell ")[1]
                    msg["message"] = t.gettext("Monster %s moved one cell %s") % (name, direction)
            data = json.dumps(msg).encode() + b"\n"
            conn.send(data)
            print(f"Sent to {conn.getpeername()}: {data.decode()}")
        except Exception as e:
            print(f"Send error to {conn.getpeername()}: {e}")

    def move_random_monster(self) -> None:
        """Move a random monster to an adjacent cell if moving_monsters is enabled."""
        if not self.moving_monsters or not self.field:
            return
        directions = [
            ("right", (1, 0)),
            ("left", (-1, 0)),
            ("up", (0, -1)),
            ("down", (0, 1))
        ]
        max_attempts = len(self.field) * len(directions)
        attempts = 0

        while attempts < max_attempts:
            key = random.choice(list(self.field.keys()))
            monster = self.field[key]
            direction, (dx, dy) = random.choice(directions)
            new_x = (monster.x + dx) % 10
            new_y = (monster.y + dy) % 10
            new_pos = (new_x, new_y)

            if new_pos not in self.field or new_pos == key:
                old_pos = (monster.x, monster.y)
                monster.x, monster.y = new_x, new_y
                self.field[new_pos] = self.field.pop(old_pos)
                self.send_to_all({
                    "type": "broadcast",
                    "message": f"Monster {monster.name} moved one cell {direction}"
                })
                for username, (gamer_conn, gamer, _) in list(self.players.items()):
                    if gamer.get_position() == new_pos:
                        if gamer_conn:
                            try:
                                gamer_conn.send(json.dumps({
                                    "type": "encounter",
                                    "name": monster.name,
                                    "hello": monster.hello
                                }).encode() + b"\n")
                            except Exception as e:
                                print(f"Error sending encounter to {username}: {e}")
                                self.remove_player(username)
                break
            attempts += 1

def schedule_monster_movement(game: Game) -> None:
    """Schedule periodic monster movement every 30 seconds."""
    game.move_random_monster()
    threading.Timer(30.0, schedule_monster_movement, args=[game]).start()

def handle_move(game: Game, user: str, cmd: Dict) -> Dict:
    """Handle the move command."""
    p = game.get_player(user)
    t = game.get_translation(user)
    if not p:
        return {"type": "error", "message": t.gettext("Player not found")}
    p.move(cmd["dx"], cmd["dy"])
    x, y = p.get_position()
    m = game.field.get((x, y))
    game.send_to_all({"type": "broadcast", "message": f"{user} moved to ({x},{y})"})
    return (
        {"type": "encounter", "name": m.name, "hello": m.hello}
        if m else {"type": "position", "message": t.gettext("Moved to (%d, %d)") % (x, y)}
    )

def handle_addmon(game: Game, user: str, cmd: Dict) -> Dict:
    """Handle the addmon command."""
    t = game.get_translation(user)
    x, y, n, h, hp = cmd["x"], cmd["y"], cmd["name"], cmd["hello"], cmd["hp"]
    replaced = game.add_monster(x, y, n, h, hp)
    game.send_to_all({
        "type": "broadcast",
        "message": f"{user} added {n} at ({x},{y}) saying {h}"
    })
    message = t.gettext("Added monster at (%d, %d)") % (x, y)
    if replaced:
        message += "\n" + t.gettext("Replaced the old monster")
    return {"type": "added_monster", "message": message}

def handle_attack(game: Game, user: str, cmd: Dict) -> Dict:
    """Handle the attack command."""
    t = game.get_translation(user)
    n, dmg, w = cmd["name"], cmd["damage"], cmd.get("weapon", "unknown")
    ok, dealt, hp, dead = game.attack_monster(user, n, w, dmg)
    if ok:
        msg = (
            f"{user} attacked {n} with {w}, dealing {dealt} damage. "
            f"{n} {'was killed!' if dead else f'has {hp} HP remaining.'}"
        )
        game.send_to_all({"type": "broadcast", "message": msg})
        message = t.gettext("Attacked %s, damage %d hp") % (n, dealt)
        if dead:
            message += "\n" + t.gettext("%s died") % n
        elif hp > 0:
            message += "\n" + t.gettext("%s now has %d hp") % (n, hp)
    else:
        message = t.gettext("No %s here") % n
    return {"type": "attack_result", "message": message}

def handle_sayall(game: Game, user: str, cmd: Dict) -> Dict:
    """Handle the sayall command."""
    t = game.get_translation(user)
    message = cmd["message"]
    game.send_to_all({"type": "broadcast", "message": f"{user}: {message}"})
    return {"type": "sayall_result", "message": t.gettext("Message \"%s\" sent") % message}

def handle_timer(game: Game, user: str, cmd: Dict) -> Dict:
    """Handle the timer command."""
    t = game.get_translation(user)
    uptime = int(game.get_uptime())
    return {"type": "timer_result", "message": t.gettext("Server uptime: %d seconds") % uptime}

def handle_movemonsters(game: Game, user: str, cmd: Dict) -> Dict:
    """Handle the movemonsters command."""
    t = game.get_translation(user)
    state = cmd.get("state")
    if state not in ("on", "off"):
        return {"type": "error", "message": t.gettext("Invalid state: use 'on' or 'off'")}
    game.moving_monsters = state == "on"
    return {"type": "movemonsters_result", "message": t.gettext("Moving monsters: %s") % state}

def handle_locale(game: Game, user: str, cmd: Dict) -> Dict:
    """Handle the locale command."""
    t = game.get_translation(user)
    locale = cmd.get("locale")
    if locale not in ["en_US", "ru_RU"]:
        return {"type": "error", "message": t.gettext("Unsupported locale: %s") % locale}
    conn, gamer, _ = game.players[user]
    game.players[user] = (conn, gamer, locale)
    t = game.get_translation(user)
    print(f"Set locale for {user} to {locale}")
    return {"type": "locale_result", "message": t.gettext("Set up locale: %s") % locale}

def handle_help(game: Game, user: str, cmd: Dict) -> Dict:
    """Handle the help command."""
    t = game.get_translation(user)
    command = cmd.get("command", "")
    commands = [
        "attack", "help", "locale", "movemonsters", "right", "timer",
        "addmon", "down", "left", "move", "sayall", "up", "quit", "EOF"
    ]
    if not command:
        message = t.gettext("Available commands: %s") % ", ".join(commands)
        message += "\n" + t.gettext("Type 'help <command>' for more information")
    elif command in commands:
        message = t.gettext(f"help_{command}")
    else:
        message = t.gettext("Unknown command: %s") % command
    return {"type": "help_result", "message": message}

COMMANDS = {
    "move": handle_move,
    "addmon": handle_addmon,
    "attack": handle_attack,
    "sayall": handle_sayall,
    "timer": handle_timer,
    "movemonsters": handle_movemonsters,
    "locale": handle_locale,
    "help": handle_help
}

def handle_client(conn: socket.socket, addr: Tuple[str, int], game: Game, user: str) -> None:
    """Handle a client connection."""
    t = game.get_translation(user)
    conn.send(json.dumps({
        "type": "welcome",
        "message": t.gettext("Welcome, %s!") % user
    }).encode() + b"\n")
    game.send_to_all({"type": "broadcast", "message": f"{user} joined the game!"})
    try:
        while True:
            data = b""
            while True:
                chunk = conn.recv(1024)
                if not chunk:
                    raise ConnectionError
                data += chunk
                try:
                    cmd = json.loads(data.decode())
                    break
                except json.JSONDecodeError:
                    continue
            h = COMMANDS.get(
                cmd["type"],
                lambda g, u, c: {"type": "error", "message": g.get_translation(u).gettext("Unknown command")}
            )
            res = h(game, user, cmd)
            conn.send(json.dumps(res).encode() + b"\n")
    except Exception as e:
        print(f"{user} disconnected: {e}")
    finally:
        game.remove_player(user)
        game.send_to_all({"type": "broadcast", "message": f"{user} left the game!"})
        conn.close()

def accept_connections(sock: socket.socket, game: Game) -> None:
    """Accept incoming client connections."""
    while True:
        try:
            conn, addr = sock.accept()
            data = b""
            while True:
                chunk = conn.recv(1024)
                if not chunk:
                    raise ConnectionError
                data += chunk
                try:
                    auth = json.loads(data.decode())
                    break
                except json.JSONDecodeError:
                    continue
            user = auth.get("username")
            if not user:
                conn.send(json.dumps({
                    "type": "error",
                    "message": "Username required"
                }).encode() + b"\n")
                conn.close()
                continue
            if not game.add_player(user, conn):
                conn.send(json.dumps({
                    "type": "error",
                    "message": "Username taken"
                }).encode() + b"\n")
                conn.close()
                continue
            t = threading.Thread(
                target=handle_client,
                args=(conn, addr, game, user),
                daemon=True
            )
            t.start()
        except Exception as e:
            print(f"Accept error: {e}")

loop = asyncio.new_event_loop()

def start_loop() -> None:
    """Start the asyncio event loop."""
    asyncio.set_event_loop(loop)
    loop.run_forever()

