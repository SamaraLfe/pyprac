import unittest
import multiprocessing
import time
import json
from mood.server.server import Server
from mood.client.client import MudCmd

class TestServerClientInteraction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Start the server and connect a test client."""
        cls.server = Server()
        cls.proc = multiprocessing.Process(target=cls.server.start_server)
        cls.proc.start()
        time.sleep(1)
        cls.client = MudCmd('test_user')

    @classmethod
    def tearDownClass(cls):
        """Close the client connection and terminate the server."""
        cls.client.do_quit('')
        cls.proc.terminate()
        cls.proc.join()

    def setUp(self):
        """Ensure client is connected before each test."""
        self.assertTrue(self.client.connected, "Client is not connected to server")

    def test_add_monster(self):
        """Test adding a monster near the player's initial position (0,0)."""
        self.client.send_command({
            "type": "addmon",
            "x": 1,
            "y": 0,
            "name": "jgsbat",
            "hello": "Greetings!",
            "hp": 25
        })
        time.sleep(0.1)
        data = b""
        while True:
            chunk = self.client.sock.recv(1024)
            data += chunk
            try:
                response = json.loads(data.decode())
                break
            except json.JSONDecodeError:
                continue
        self.assertEqual(response["type"], "added_monster")
        self.assertIn("Added monster at (1, 0)", response["message"])

    def test_move_to_monster(self):
        """Test moving to the monster's position and receiving its greeting."""
        self.client.send_command({
            "type": "addmon",
            "x": 1,
            "y": 0,
            "name": "jgsbat",
            "hello": "Greetings!",
            "hp": 25
        })
        time.sleep(0.1)
        self.client.sock.recv(1024)

        self.client.send_command({"type": "move", "dx": 1, "dy": 0})
        time.sleep(0.1)
        data = b""
        while True:
            chunk = self.client.sock.recv(1024)
            data += chunk
            try:
                response = json.loads(data.decode())
                break
            except json.JSONDecodeError:
                continue
        self.assertEqual(response["type"], "encounter")
        self.assertEqual(response["name"], "jgsbat")
        self.assertEqual(response["hello"], "Greetings!")

    def test_attack_monster(self):
        """Test attacking the monster and checking the response."""
        self.client.send_command({
            "type": "addmon",
            "x": 1,
            "y": 0,
            "name": "jgsbat",
            "hello": "Greetings!",
            "hp": 25
        })
        time.sleep(0.1)
        self.client.sock.recv(1024)

        self.client.send_command({"type": "move", "dx": 1, "dy": 0})
        time.sleep(0.1)
        self.client.sock.recv(1024)

        self.client.send_command({
            "type": "attack",
            "name": "jgsbat",
            "weapon": "sword",
            "damage": 10
        })
        time.sleep(0.1)
        data = b""
        while True:
            chunk = self.client.sock.recv(1024)
            data += chunk
            try:
                response = json.loads(data.decode())
                break
            except json.JSONDecodeError:
                continue
        self.assertEqual(response["type"], "attack_result")
        self.assertIn("Attacked jgsbat, damage 10 hp", response["message"])
        self.assertIn("jgsbat now has 15 hp", response["message"])

if __name__ == '__main__':
    unittest.main()