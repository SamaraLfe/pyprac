import sys
import cowsay
import shlex
from io import StringIO

jgsbat = cowsay.read_dot_cow(StringIO("""
$the_cow = <<EOC;
    ,_                    _,
    ) '-._  ,_    _,  _.-' (
    )  _.-'.|\\--//|.'-._  (
     )'   .'\\/o\\/o\\/'.   `(
      ) .' . \\====/ . '. (
       )  / <<    >> \\  (
        '-._/``  ``\\_.-'
  jgs     __\\'--'//__
         (((""`  `"")))
EOC
"""))


class Person:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def get_position(self):
        return (self.x, self.y)


class Monster(Person):
    def __init__(self, x, y, name, hello, hitpoints):
        super().__init__(x, y)
        self.name = name
        self.hello = hello
        self.hitpoints = hitpoints

    def encounter(self):
        if self.name == "jgsbat":
            print(cowsay.cowsay(self.hello, cowfile=jgsbat))
        else:
            print(cowsay.cowsay(self.hello, cow=self.name))


class Gamer(Person):
    def __init__(self, x, y):
        super().__init__(x, y)

    def move(self, direction):
        if direction == "up":
            self.y = (self.y - 1) % 10
        elif direction == "down":
            self.y = (self.y + 1) % 10
        elif direction == "left":
            self.x = (self.x - 1) % 10
        elif direction == "right":
            self.x = (self.x + 1) % 10


class Game:
    def __init__(self):
        self.field = {}
        self.player = Gamer(0, 0)
        self.valid_monsters = cowsay.list_cows() + ["jgsbat"]

    def add_monster(self, x, y, name, hello, hitpoints):
        if not (0 <= x <= 9 and 0 <= y <= 9):
            return False
        if hitpoints <= 0:
            return False
        key = (x, y)
        replaced = key in self.field
        self.field[key] = Monster(x, y, name, hello, hitpoints)
        return replaced

    def process_command(self, command):
        parts = shlex.split(command.strip())
        if not parts:
            print("Invalid command")
            return

        cmd = parts[0]
        if cmd in ["up", "down", "left", "right"]:
            if len(parts) != 1:
                print("Invalid arguments")
                return
            self.player.move(cmd)
            x, y = self.player.get_position()
            print(f"Moved to ({x}, {y})")
            if (x, y) in self.field:
                self.field[(x, y)].encounter()
        elif cmd == "addmon":
            if len(parts) < 7:
                print("Invalid arguments")
                return
            try:
                name = parts[1]
                if name not in self.valid_monsters:
                    print("Cannot add unknown monster")
                    return
                hello = None
                hitpoints = None
                x = None
                y = None
                i = 2
                while i < len(parts):
                    if parts[i] == "hello" and i + 1 < len(parts):
                        hello = parts[i + 1]
                        i += 2
                    elif parts[i] == "hp" and i + 1 < len(parts):
                        hitpoints = int(parts[i + 1])
                        i += 2
                    elif parts[i] == "coords" and i + 2 < len(parts):
                        x = int(parts[i + 1])
                        y = int(parts[i + 2])
                        i += 3
                    else:
                        print("Invalid arguments")
                        return
                if hello is None or hitpoints is None or x is None or y is None:
                    print("Missing required arguments")
                    return
                if hitpoints <= 0:
                    print("Hitpoints must be positive")
                    return
                replaced = self.add_monster(x, y, name, hello, hitpoints)
                print(f"Added monster {name} to ({x}, {y}) saying {hello}")
                if replaced:
                    print("Replaced the old monster")
            except ValueError:
                print("Invalid arguments")
        else:
            print("Invalid command")


def main():
    print("<<< Welcome to Python-MUD 0.1 >>>")
    game = Game()
    for line in sys.stdin:
        game.process_command(line)


if __name__ == "__main__":
    main()