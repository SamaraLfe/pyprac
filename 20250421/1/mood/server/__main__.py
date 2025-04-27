"""Main entry point for running the MOOD game server."""
from .server import Server


if __name__ == "__main__":
    server = Server()
    try:
        server.start_server()
    except KeyboardInterrupt:
        print("Shutting down server")