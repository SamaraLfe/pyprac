import sys
import cowsay

class Person:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def get_position(self):
        return (self.x, self.y)

class Monster(Person):
    def __init__(self, x, y, hello):
        super().__init__(x, y)
        self.hello = hello

    def encounter(self):
        print(cowsay.cowsay(self.hello))

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

    def add_monster(self, x, y, hello):
        if not (0 <= x <= 9 and 0 <= y <= 9):
            return False
        key = (x, y)
        replaced = key in self.field
        self.field[key] = Monster(x, y, hello)
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
            if len(parts) != 4:
                print("Invalid arguments")
                return
            try:
                x, y = int(parts[1]), int(parts[2])
                hello = parts[3]
                replaced = self.add_monster(x, y, hello)
                print(f"Added monster to ({x}, {y}) saying {hello}")
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