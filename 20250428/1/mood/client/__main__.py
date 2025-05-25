"""Main entry point for running the MOOD game client."""
import sys
import argparse
import os

from .client import MudCmd


def main():
    """Run the MOOD client with a provided username and optional script file.

    Args:
        None (uses sys.argv for username and optional --file).

    Exits:
        If username is not provided, contains spaces, or file is invalid.
    """
    parser = argparse.ArgumentParser(description="MOOD game client")
    parser.add_argument("username", help="Player's username")
    parser.add_argument("--file", help="Path to .mood script file to execute")
    args = parser.parse_args()

    if " " in args.username:
        print("Error: Username cannot contain spaces")
        sys.exit(1)

    if args.file:
        if not args.file.endswith(".mood"):
            print("Error: Script file must have .mood extension")
            sys.exit(1)
        if not os.path.exists(args.file):
            print(f"Error: File {args.file} does not exist")
            sys.exit(1)
        try:
            with open(args.file, 'r') as f:
                client = MudCmd(args.username, stdin=f)
                client.prompt = ""
                client.use_rawinput = False
                client.cmdloop()
        except Exception as e:
            print(f"Error reading file {args.file}: {e}")
            sys.exit(1)
    else:
        client = MudCmd(args.username)
        client.cmdloop()


if __name__ == "__main__":
    main()