import pytest
import socket
import json
import time
import multiprocessing
from mood.server.server import Server


def run_server(port):
    """Функция для запуска сервера в отдельном процессе."""
    server = Server('localhost', port)
    server.start_server()


@pytest.fixture
def server():
    """Запуск сервера в отдельном процессе и подключение клиента."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('localhost', 0))
    port = sock.getsockname()[1]
    sock.close()

    # Запускаем сервер
    proc = multiprocessing.Process(target=run_server, args=(port,))
    proc.start()
    time.sleep(1)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('localhost', port))

    # Аутентификация
    username = "test_user"
    sock.send(json.dumps({"username": username}).encode() + b"\n")
    response = receive_response(sock, expected_type="welcome")
    assert "Welcome" in response["message"], "Не удалось подключиться к серверу"

    yield sock, username, port

    sock.close()
    proc.terminate()
    proc.join(timeout=2)
    if proc.is_alive():
        proc.kill()


def receive_response(sock, expected_type=None, timeout=5):
    """Получение ответа от сервера с фильтрацией по типу."""
    start_time = time.time()
    data = b""
    while time.time() - start_time < timeout:
        chunk = sock.recv(1024)
        if not chunk:
            break
        data += chunk
        try:
            response = json.loads(data.decode())
            data = b""  # Сбрасываем буфер после успешного декодирования
            if expected_type and response["type"] != expected_type:
                continue  # Пропускаем неподходящие сообщения
            return response
        except json.JSONDecodeError:
            continue
    return None


def test_add_monster(server):
    """Проверка команды установки монстра."""
    sock, username, port = server
    command = {
        "type": "addmon",
        "x": 1,
        "y": 1,
        "name": "cow",
        "hello": "Moo!",
        "hp": 50
    }
    sock.send(json.dumps(command).encode() + b"\n")
    response = receive_response(sock, expected_type="added_monster")
    assert response["type"] == "added_monster"
    assert "Added monster at (1, 1)" in response["message"]


def test_move_to_monster(server):
    """Проверка движения к монстру и получения приветствия."""
    sock, username, port = server
    command = {
        "type": "addmon",
        "x": 1,
        "y": 1,
        "name": "cow",
        "hello": "Moo!",
        "hp": 50
    }
    sock.send(json.dumps(command).encode() + b"\n")
    receive_response(sock, expected_type="added_monster")  # Пропускаем ответ на addmon

    command = {
        "type": "move",
        "dx": 1,
        "dy": 1
    }
    sock.send(json.dumps(command).encode() + b"\n")
    response = receive_response(sock, expected_type="encounter")
    assert response["type"] == "encounter"
    assert response["name"] == "cow"
    assert response["hello"] == "Moo!"


def test_attack_monster(server):
    """Проверка атаки на монстра."""
    sock, username, port = server
    command = {
        "type": "addmon",
        "x": 1,
        "y": 1,
        "name": "cow",
        "hello": "Moo!",
        "hp": 50
    }
    sock.send(json.dumps(command).encode() + b"\n")
    receive_response(sock, expected_type="added_monster")

    command = {
        "type": "move",
        "dx": 1,
        "dy": 1
    }
    sock.send(json.dumps(command).encode() + b"\n")
    receive_response(sock, expected_type="encounter")

    command = {
        "type": "attack",
        "name": "cow",
        "weapon": "sword",
        "damage": 10
    }
    sock.send(json.dumps(command).encode() + b"\n")
    response = receive_response(sock, expected_type="attack_result")
    assert response["type"] == "attack_result"
    assert "Attacked cow, damage 10 hp" in response["message"]
    assert "cow now has 40 hp" in response["message"]