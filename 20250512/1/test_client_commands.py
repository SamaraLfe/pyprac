import pytest
from unittest.mock import Mock, patch
import json
from mood.client.client import MudCmd

@pytest.fixture
def client():
    """Создание клиента с замоканными вводом и сокетом."""
    username = "test_user"
    with patch.object(MudCmd, 'connect', return_value=True):
        client = MudCmd(username)
        client.connected = True
        client.sock = Mock()
        return client

def test_addmon_valid_input_1(client):
    """Проверка преобразования команды addmon с первыми параметрами."""
    with patch('builtins.input', side_effect=['addmon tux coords 1 2 hello "Hi!" hp 50']):
        client.do_addmon('tux coords 1 2 hello "Hi!" hp 50')
        client.sock.send.assert_called_with(
            json.dumps({
                "type": "addmon",
                "x": 1,
                "y": 2,
                "name": "tux",
                "hello": "Hi!",
                "hp": 50
            }).encode() + b"\n"
        )

def test_addmon_valid_input_2(client):
    """Проверка преобразования команды addmon с другими параметрами."""
    with patch('builtins.input', side_effect=['addmon milk coords 3 4 hello "Roar!" hp 100']):
        client.do_addmon('milk coords 3 4 hello "Roar!" hp 100')
        client.sock.send.assert_called_with(
            json.dumps({
                "type": "addmon",
                "x": 3,
                "y": 4,
                "name": "milk",
                "hello": "Roar!",
                "hp": 100
            }).encode() + b"\n"
        )

def test_addmon_invalid_input(client, capsys):
    """Проверка обработки некорректных параметров для addmon."""
    with patch('builtins.input', side_effect=['addmon tux coords -1 2 hello "Hi!" hp 50']):
        client.do_addmon('tux coords -1 2 hello "Hi!" hp 50')
        captured = capsys.readouterr()
        assert "Invalid parameters" in captured.out
        client.sock.send.assert_not_called()

def test_attack_valid_input_1(client):
    """Проверка преобразования команды attack с мечом."""
    with patch('builtins.input', side_effect=['attack tux with sword']):
        client.do_attack('tux with sword')
        client.sock.send.assert_called_with(
            json.dumps({
                "type": "attack",
                "name": "tux",
                "weapon": "sword",
                "damage": 10
            }).encode() + b"\n"
        )

def test_attack_valid_input_2(client):
    """Проверка преобразования команды attack с копьём."""
    with patch('builtins.input', side_effect=['attack milk with spear']):
        client.do_attack('milk with spear')
        client.sock.send.assert_called_with(
            json.dumps({
                "type": "attack",
                "name": "milk",
                "weapon": "spear",
                "damage": 15
            }).encode() + b"\n"
        )