import cmd
import sys

class CommandInterpreter(cmd.Cmd):
    def __init__(self, input_file=None):
        super().__init__(stdin=input_file)
        self.prompt = ""
        self.use_rawinput = False if input_file else True

    def do_bless(self, arg):
        """Print 'Be blessed, <string>!' for the given string."""
        print(f"Be blessed, {arg}!")

    def do_sendto(self, arg):
        """Print 'Go to <string>!' for the given string."""
        print(f"Go to {arg}!")

    def do_EOF(self, arg):
        """Exit the interpreter on EOF."""
        return True

def main():
    if len(sys.argv) == 2:
        try:
            with open(sys.argv[1], 'r') as f:
                interpreter = CommandInterpreter(input_file=f)
                interpreter.cmdloop()
        except FileNotFoundError:
            print(f"File {sys.argv[1]} not found.")
            sys.exit(1)
    else:
        interpreter = CommandInterpreter()
        interpreter.cmdloop()

if __name__ == "__main__":
    main()