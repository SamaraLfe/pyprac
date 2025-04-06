"""Common classes and constants for the MOOD game."""
import cowsay
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
    """Base class for game entities with a position.

    Attributes:
        x (int): The x-coordinate of the entity.
        y (int): The y-coordinate of the entity.
    """

    def __init__(self, x, y):
        """Initialize a Person with coordinates.

        Args:
            x (int): The x-coordinate.
            y (int): The y-coordinate.
        """
        self.x, self.y = x, y

    def get_position(self):
        """Get the current position of the entity.

        Returns:
            tuple: The (x, y) coordinates.
        """
        return self.x, self.y


class Monster(Person):
    """A monster entity in the game.

    Attributes:
        name (str): The name of the monster.
        hello (str): The message the monster displays.
        hitpoints (int): The monster's health points.
    """

    def __init__(self, x, y, name, hello, hp):
        """Initialize a Monster with position and attributes.

        Args:
            x (int): The x-coordinate.
            y (int): The y-coordinate.
            name (str): The monster's name.
            hello (str): The monster's greeting message.
            hp (int): The monster's health points.
        """
        super().__init__(x, y)
        self.name, self.hello, self.hitpoints = name, hello, hp


class Gamer(Person):
    """A player entity in the game."""

    def move(self, dx, dy):
        """Move the player by the given offsets.

        Args:
            dx (int): Change in x-coordinate.
            dy (int): Change in y-coordinate.
        """
        self.x = (self.x + dx) % 10
        self.y = (self.y + dy) % 10
