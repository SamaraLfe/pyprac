"""Main entry point for running the MOOD game client."""
import sys

from .client import MudCmd


def main():
    """Run the MOOD client with a provided username.

    Args:
        None (uses sys.argv for username).

    Exits:
        If username is not provided or contains spaces.
    """
    if len(sys.argv) != 2:
        print("Usage: python3 -m mood.client <username>")
        sys.exit(1)
    if " " in sys.argv[1]:
        print("Error: Username cannot contain spaces")
        sys.exit(1)
    MudCmd(sys.argv[1]).cmdloop()


if __name__ == "__main__":
    main()
