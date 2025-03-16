import cowsay
import shlex
import cmd
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
        self.weapons = {"sword": 10, "spear": 15, "axe": 20}

    def add_monster(self, x, y, name, hello, hitpoints):
        if not (0 <= x <= 9 and 0 <= y <= 9):
            return False
        if hitpoints <= 0:
            return False
        key = (x, y)
        replaced = key in self.field
        self.field[key] = Monster(x, y, name, hello, hitpoints)
        return replaced

    def attack_monster(self, monster_name, damage):
        pos = self.player.get_position()
        if pos not in self.field or self.field[pos].name != monster_name:
            print(f"No {monster_name} here")
            return
        monster = self.field[pos]
        actual_damage = min(damage, monster.hitpoints)
        monster.hitpoints -= actual_damage
        print(f"Attacked {monster.name}, damage {actual_damage} hp")
        if monster.hitpoints == 0:
            print(f"{monster.name} died")
            del self.field[pos]
        else:
            print(f"{monster.name} now has {monster.hitpoints}")


class MudCmd(cmd.Cmd):
    prompt = "(MUD) "
    intro = "<<< Welcome to Python-MUD 0.1 >>>"

    def __init__(self):
        super().__init__()
        self.game = Game()

    def do_up(self, arg):
        if arg:
            print("Invalid arguments")
            return
        self.game.player.move("up")
        x, y = self.game.player.get_position()
        print(f"Moved to ({x}, {y})")
        if (x, y) in self.game.field:
            self.game.field[(x, y)].encounter()

    def do_down(self, arg):
        if arg:
            print("Invalid arguments")
            return
        self.game.player.move("down")
        x, y = self.game.player.get_position()
        print(f"Moved to ({x}, {y})")
        if (x, y) in self.game.field:
            self.game.field[(x, y)].encounter()

    def do_left(self, arg):
        if arg:
            print("Invalid arguments")
            return
        self.game.player.move("left")
        x, y = self.game.player.get_position()
        print(f"Moved to ({x}, {y})")
        if (x, y) in self.game.field:
            self.game.field[(x, y)].encounter()

    def do_right(self, arg):
        if arg:
            print("Invalid arguments")
            return
        self.game.player.move("right")
        x, y = self.game.player.get_position()
        print(f"Moved to ({x}, {y})")
        if (x, y) in self.game.field:
            self.game.field[(x, y)].encounter()

    def do_addmon(self, arg):
        parts = shlex.split(arg)
        if len(parts) < 6:
            print("Invalid arguments")
            return
        try:
            name = parts[0]
            if name not in self.game.valid_monsters:
                print("Cannot add unknown monster")
                return
            hello = None
            hitpoints = None
            x = None
            y = None
            i = 1
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
            replaced = self.game.add_monster(x, y, name, hello, hitpoints)
            print(f"Added monster {name} to ({x}, {y}) saying {hello}")
            if replaced:
                print("Replaced the old monster")
        except ValueError:
            print("Invalid arguments")

    def complete_addmon(self, text, line, begidx, endidx):
        args = shlex.split(line[:begidx])
        if len(args) == 1:
            return [name for name in self.game.valid_monsters if name.startswith(text)]
        keywords = ["hp", "coords", "hello"]
        used = set(arg for arg in args[1:] if arg in keywords)
        return [kw for kw in keywords if kw not in used and kw.startswith(text)]

    def do_attack(self, arg):
        parts = shlex.split(arg)
        if len(parts) < 1 or len(parts) > 3 or (len(parts) == 3 and parts[1] != "with"):
            print("Invalid arguments")
            return
        monster_name = parts[0]
        weapon = "sword"
        if len(parts) == 3:
            weapon = parts[2]
            if weapon not in self.game.weapons:
                print("Unknown weapon")
                return
        self.game.attack_monster(monster_name, self.game.weapons[weapon])

    def complete_attack(self, text, line, begidx, endidx):
        args = shlex.split(line[:begidx])
        if len(args) <= 1:
            return [name for name in self.game.valid_monsters if name.startswith(text)]
        elif len(args) == 2:
            return ["with"] if "with".startswith(text) else []
        elif len(args) == 3 and args[2] == "with":
            return [w for w in self.game.weapons if w.startswith(text)]
        return []

    def do_quit(self, arg):
        print("Goodbye!")
        return True

    def do_EOF(self, arg):
        print("Goodbye!")
        return True


if __name__ == "__main__":
    MudCmd().cmdloop()