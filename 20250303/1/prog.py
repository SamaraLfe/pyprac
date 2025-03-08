import sys
import cowsay


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
        parts = command.strip().split()
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
            if len(parts) != 5:
                print("Invalid arguments")
                return
            try:
                name = parts[1]
                x, y = int(parts[2]), int(parts[3])
                hello = parts[4]
                if name not in cowsay.list_cows():
                    print("Cannot add unknown monster")
                    return
                replaced = self.add_monster(x, y, name, hello)
                print(f"Added monster {name} to ({x}, {y}) saying {hello}")
                if replaced:
                    print("Replaced the old monster")
            except ValueError:
                print("Invalid arguments")
        else:
            print("Invalid command")


def main():
    game = Game()
    for line in sys.stdin:
        game.process_command(line)


if __name__ == "__main__":
    main()