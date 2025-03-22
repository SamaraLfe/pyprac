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

cow_files = {"jgsbat": jgsbat}

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
        print(cowsay.cowsay(self.hello, cowfile=cow_files.get(self.name, self.name)))


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

    def _move(self, direction, arg):
        if arg:
            print("Invalid arguments")
            return
        self.game.player.move(direction)
        x, y = self.game.player.get_position()
        print(f"Moved to ({x}, {y})")
        if (x, y) in self.game.field:
            self.game.field[(x, y)].encounter()

    def do_up(self, arg):
        self._move("up", arg)

    def do_down(self, arg):
        self._move("down", arg)

    def do_left(self, arg):
        self._move("left", arg)

    def do_right(self, arg):
        self._move("right", arg)

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

            params = {}
            i = 1
            while i < len(parts):
                if parts[i] in ("hello", "hp", "coords") and i + 1 < len(parts):
                    if parts[i] == "coords" and i + 2 < len(parts):
                        params["x"], params["y"] = int(parts[i + 1]), int(parts[i + 2])
                        i += 3
                    else:
                        params[parts[i]] = parts[i + 1] if parts[i] == "hello" else int(parts[i + 1])
                        i += 2
                else:
                    print("Invalid arguments")
                    return

            if not all(k in params for k in ("hello", "hp", "x", "y")):
                print("Missing required arguments")
                return
            if params["hp"] <= 0:
                print("Hitpoints must be positive")
                return
            if not (0 <= params["x"] <= 9 and 0 <= params["y"] <= 9):
                print("Coordinates out of bounds")
                return

            replaced = self.game.add_monster(params["x"], params["y"], name, params["hello"], params["hp"])
            print(f"Added monster {name} to ({params['x']}, {params['y']}) saying {params['hello']}")
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
        if len(args) == 2:
            return ["with"] if "with".startswith(text) else []
        if len(args) == 3 and args[2] == "with":
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