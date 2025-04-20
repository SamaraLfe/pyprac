"""Server implementation for the MOOD game."""
import socket
import json
import cowsay
import asyncio
import threading

from ..common.models import Monster, Gamer


class Game:
    """Manages the game state for the MOOD server.

    Attributes:
        field (dict): Maps (x, y) coordinates to Monster objects.
        players (dict): Maps usernames to (connection, Gamer) tuples.
        valid_monsters (list): List of valid monster names.
    """

    def __init__(self):
        """Initialize the game state."""
        self.field, self.players = {}, {}
        self.valid_monsters = cowsay.list_cows() + ["jgsbat"]

    def add_player(self, username, conn):
        """Add a player to the game.

        Args:
            username (str): The player's username.
            conn (socket.socket): The player's connection.

        Returns:
            bool: True if the player was added, False if the username is taken.
        """
        if username in self.players:
            return False
        self.players[username] = (conn, Gamer(0, 0))
        return True

    def remove_player(self, username):
        """Remove a player from the game.

        Args:
            username (str): The player's username.

        Returns:
            bool: True if the player was removed, False if not found.
        """
        return self.players.pop(username, None) is not None

    def get_player(self, username):
        """Get a player's Gamer object.

        Args:
            username (str): The player's username.

        Returns:
            Gamer: The player's Gamer object, or None if not found.
        """
        return self.players.get(username, (None, None))[1]

    def add_monster(self, x, y, name, hello, hp):
        """Add a monster to the game field.

        Args:
            x (int): The x-coordinate.
            y (int): The y-coordinate.
            name (str): The monster's name.
            hello (str): The monster's greeting message.
            hp (int): The monster's health points.

        Returns:
            bool: True if an existing monster was replaced, False otherwise.
        """
        key, replaced = (x, y), (x, y) in self.field
        self.field[key] = Monster(x, y, name, hello, hp)
        return replaced

    def attack_monster(self, username, name, weapon, dmg):
        """Handle a player attacking a monster.

        Args:
            username (str): The player's username.
            name (str): The monster's name.
            weapon (str): The weapon used.
            dmg (int): The damage dealt.

        Returns:
            tuple: (success, damage_dealt, remaining_hp, killed).
        """
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

    def send_to_all(self, msg):
        """Send a message to all players.

        Args:
            msg (dict): The message to send.
        """
        data = json.dumps(msg).encode() + b"\n"
        for conn, _ in self.players.values():
            asyncio.run_coroutine_threadsafe(self._send_async(conn, data), loop)

    async def _send_async(self, conn, data):
        """Asynchronously send data to a connection.

        Args:
            conn (socket.socket): The connection to send to.
            data (bytes): The data to send.
        """
        try:
            conn.send(data)
        except Exception:
            pass


def handle_move(game, user, cmd):
    """Handle the move command.

    Args:
        game (Game): The game instance.
        user (str): The player's username.
        cmd (dict): The command data.

    Returns:
        dict: Response indicating the new position or an encounter.
    """
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


def handle_addmon(game, user, cmd):
    """Handle the addmon command.

    Args:
        game (Game): The game instance.
        user (str): The player's username.
        cmd (dict): The command data.

    Returns:
        dict: Response indicating the monster was added.
    """
    x, y, n, h, hp = cmd["x"], cmd["y"], cmd["name"], cmd["hello"], cmd["hp"]
    replaced = game.add_monster(x, y, n, h, hp)
    game.send_to_all({
        "type": "broadcast",
        "message": f"{user} added {n} at ({x},{y}) saying {h}"
    })
    return {"type": "added_monster", "x": x, "y": y, "name": n, "replaced": replaced}


def handle_attack(game, user, cmd):
    """Handle the attack command.

    Args:
        game (Game): The game instance.
        user (str): The player's username.
        cmd (dict): The command data.

    Returns:
        dict: Response indicating the attack result.
    """
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


def handle_sayall(game, user, cmd):
    """Handle the sayall command.

    Args:
        game (Game): The game instance.
        user (str): The player's username.
        cmd (dict): The command data with the message.

    Returns:
        dict: Response confirming the message was sent.
    """
    message = cmd["message"]
    game.send_to_all({"type": "broadcast", "message": f"{user}: {message}"})
    return {"type": "sayall_result", "success": True, "message": message}


COMMANDS = {
    "move": handle_move,
    "addmon": handle_addmon,
    "attack": handle_attack,
    "sayall": handle_sayall
}


def handle_client(conn, addr, game, user):
    """Handle a client connection.

    Args:
        conn (socket.socket): The client connection.
        addr (tuple): The client's address.
        game (Game): The game instance.
        user (str): The player's username.
    """
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
                except Exception:
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


def accept_connections(sock, game):
    """Accept incoming client connections.

    Args:
        sock (socket.socket): The server socket.
        game (Game): The game instance.
    """
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
                except Exception:
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


def start_loop():
    """Start the asyncio event loop."""
    asyncio.set_event_loop(loop)
    loop.run_forever()


def main():
    """Run the MOOD server."""
    game = Game()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    threading.Thread(target=start_loop, daemon=True).start()
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
        print("Shutting down")
    finally:
        sock.close()
        loop.call_soon_threadsafe(loop.stop)
