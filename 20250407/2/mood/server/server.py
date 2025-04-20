"""Server implementation for the MOOD game.

This module manages the game state, handles client connections, and processes player
commands for the MOOD (Multiplayer Online Dungeon) game. It supports a 10x10 game field
with wrapped boundaries, allowing players to move, add monsters, attack, and broadcast
messages. Additionally, it implements wandering monsters that move every 30 seconds to a
random adjacent cell, triggering encounters if they land on a cell with players.
"""
import socket
import json
import random
import asyncio
import threading
import time
import cowsay
from typing import Dict, Tuple, Optional

from ..common.models import Monster, Gamer


class Game:
    """Manages the game state for the MOOD server.

    Attributes:
        field (Dict[Tuple[int, int], Monster]):
        Maps (x, y) coordinates to Monster objects.
        players (Dict[str, Tuple[socket.socket, Gamer]]):
        Maps usernames to (connection, Gamer) tuples.
        valid_monsters (list):
        List of valid monster names from python-cowsay and jgsbat.
        start_time (float):
        Time when the server started (Unix timestamp).
    """

    def __init__(self):
        """Initialize the game state."""
        self.field: Dict[Tuple[int, int], Monster] = {}
        self.players: Dict[str, Tuple[socket.socket, Gamer]] = {}
        self.valid_monsters = cowsay.list_cows() + ["jgsbat"]
        self.start_time = time.time()

    def get_uptime(self) -> float:
        """Calculate server uptime in seconds.

        Returns:
            float: Server uptime in seconds.
        """
        return time.time() - self.start_time

    def add_player(self, username: str, conn: socket.socket) -> bool:
        """Add a player to the game."""
        if username in self.players:
            return False
        self.players[username] = (conn, Gamer(0, 0))
        return True

    def remove_player(self, username: str) -> bool:
        """Remove a player from the game."""
        return self.players.pop(username, None) is not None

    def get_player(self, username: str) -> Optional[Gamer]:
        """Get a player's Gamer object."""
        return self.players.get(username, (None, None))[1]

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
        """Send a message to all players."""
        data = json.dumps(msg).encode() + b"\n"
        for conn, _ in self.players.values():
            asyncio.run_coroutine_threadsafe(self._send_async(conn, data), loop)

    async def _send_async(self, conn: socket.socket, data: bytes) -> None:
        """Asynchronously send data to a connection."""
        try:
            conn.send(data)
            print(f"Sent to {conn.getpeername()}: {data.decode()}")
        except Exception as e:
            print(f"Send error to {conn.getpeername()}: {e}")

    def move_random_monster(self) -> None:
        """Move a random monster to an adjacent cell."""
        if not self.field:
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
                    "type": "monster_move",
                    "name": monster.name,
                    "direction": direction
                })
                for username, (gamer_conn, gamer) in list(self.players.items()):
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
    if not p:
        return {"type": "error", "message": "Player not found"}
    p.move(cmd["dx"], cmd["dy"])
    x, y = p.get_position()
    m = game.field.get((x, y))
    return (
        {"type": "encounter", "name": m.name, "hello": m.hello}
        if m else {"type": "position", "x": x, "y": y}
    )


def handle_addmon(game: Game, user: str, cmd: Dict) -> Dict:
    """Handle the addmon command."""
    x, y, n, h, hp = cmd["x"], cmd["y"], cmd["name"], cmd["hello"], cmd["hp"]
    replaced = game.add_monster(x, y, n, h, hp)
    game.send_to_all({
        "type": "broadcast",
        "message": f"{user} added {n} at ({x},{y}) saying {h}"
    })
    return {
        "type": "added_monster",
        "x": x,
        "y": y,
        "name": n,
        "replaced": replaced
    }


def handle_attack(game: Game, user: str, cmd: Dict) -> Dict:
    """Handle the attack command."""
    n, dmg, w = cmd["name"], cmd["damage"], cmd.get("weapon", "unknown")
    ok, dealt, hp, dead = game.attack_monster(user, n, w, dmg)
    if ok:
        msg = (
            f"{user} attacked {n} with {w}, dealing {dealt} damage. "
            f"{n} {'was killed!' if dead else f'has {hp} HP remaining.'}"
        )
        game.send_to_all({"type": "broadcast", "message": msg})
    return {
        "type": "attack_result",
        "success": ok,
        "damage": dealt,
        "remaining_hp": hp,
        "killed": dead
    }


def handle_sayall(game: Game, user: str, cmd: Dict) -> Dict:
    """Handle the sayall command."""
    message = cmd["message"]
    game.send_to_all({"type": "broadcast", "message": f"{user}: {message}"})
    return {"type": "sayall_result", "success": True, "message": message}


def handle_timer(game: Game, user: str, cmd: Dict) -> Dict:
    """Handle the timer command."""
    uptime = int(game.get_uptime())
    return {"type": "timer_result", "uptime": uptime}


COMMANDS = {
    "move": handle_move,
    "addmon": handle_addmon,
    "attack": handle_attack,
    "sayall": handle_sayall,
    "timer": handle_timer
}


def handle_client(conn: socket.socket, addr: Tuple[str, int],
                  game: Game, user: str) -> None:
    """Handle a client connection."""
    conn.send(json.dumps({
        "type": "welcome",
        "message": f"Welcome, {user}!"
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
                lambda g, u, c: {"type": "error", "message": "Unknown command"}
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


def main() -> None:
    """Run the MOOD game server."""
    game = Game()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    threading.Thread(target=start_loop, daemon=True).start()
    threading.Thread(target=schedule_monster_movement,
                     args=(game,), daemon=True).start()
    try:
        sock.bind(("localhost", 12345))
        sock.listen(5)
        print("Server on localhost:12345")
        threading.Thread(
            target=accept_connections,
            args=(sock, game),
            daemon=True
        ).start()
        while True:
            input()
    except KeyboardInterrupt:
        print("Shutting down server")
    finally:
        sock.close()
        loop.call_soon_threadsafe(loop.stop)
