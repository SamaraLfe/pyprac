import unittest
from unittest.mock import patch, MagicMock
from mood.client.client import MudCmd
import json

class TestClientCommandParsing(unittest.TestCase):
    def setUp(self):
        """Set up a MudCmd instance with mocked socket and input."""
        self.mock_socket = MagicMock()
        self.mock_socket.recv.side_effect = [
            json.dumps({"type": "welcome", "message": "Welcome, test_user!"}).encode() + b"\n"
        ]
        with patch('socket.socket') as mock_socket_class:
            mock_socket_class.return_value = self.mock_socket
            self.client = MudCmd('test_user')
        self.mock_socket.send.reset_mock()

    def test_addmon_valid_parameters_1(self):
        """Test addmon command with valid parameters (jgsbat at 1,0)."""
        with patch('shlex.split', return_value=['jgsbat', 'hello', 'Greetings!', 'hp', '25', 'coords', '1', '0']):
            self.client.do_addmon('jgsbat hello Greetings! hp 25 coords 1 0')
        self.mock_socket.send.assert_called_once()
        sent_data = self.mock_socket.send.call_args[0][0].decode()
        expected = {
            "type": "addmon",
            "x": 1,
            "y": 0,
            "name": "jgsbat",
            "hello": "Greetings!",
            "hp": 25
        }
        self.assertEqual(json.loads(sent_data), expected)

    def test_addmon_valid_parameters_2(self):
        """Test addmon command with valid parameters (cow at 2,3)."""
        with patch('shlex.split', return_value=['cow', 'hello', 'Moo!', 'hp', '50', 'coords', '2', '3']):
            self.client.do_addmon('cow hello Moo! hp 50 coords 2 3')
        self.mock_socket.send.assert_called_once()
        sent_data = self.mock_socket.send.call_args[0][0].decode()
        expected = {
            "type": "addmon",
            "x": 2,
            "y": 3,
            "name": "cow",
            "hello": "Moo!",
            "hp": 50
        }
        self.assertEqual(json.loads(sent_data), expected)

    def test_addmon_invalid_parameters(self):
        """Test addmon command with invalid parameters (negative hp)."""
        with patch('shlex.split', return_value=['jgsbat', 'hello', 'Greetings!', 'hp', '-5', 'coords', '1', '0']):
            with patch('builtins.print') as mock_print:
                self.client.do_addmon('jgsbat hello Greetings! hp -5 coords 1 0')
        mock_print.assert_called_with("Invalid parameters")
        self.mock_socket.send.assert_not_called()

    def test_attack_valid_parameters_1(self):
        """Test attack command with valid parameters (jgsbat with sword)."""
        with patch('shlex.split', return_value=['jgsbat', 'with', 'sword']):
            self.client.do_attack('jgsbat with sword')
        self.mock_socket.send.assert_called_once()
        sent_data = self.mock_socket.send.call_args[0][0].decode()
        expected = {
            "type": "attack",
            "name": "jgsbat",
            "weapon": "sword",
            "damage": 10
        }
        self.assertEqual(json.loads(sent_data), expected)

    def test_attack_valid_parameters_2(self):
        """Test attack command with valid parameters (cow with axe)."""
        with patch('shlex.split', return_value=['cow', 'with', 'axe']):
            self.client.do_attack('cow with axe')
        self.mock_socket.send.assert_called_once()
        sent_data = self.mock_socket.send.call_args[0][0].decode()
        expected = {
            "type": "attack",
            "name": "cow",
            "weapon": "axe",
            "damage": 20
        }
        self.assertEqual(json.loads(sent_data), expected)

if __name__ == '__main__':
    unittest.main()