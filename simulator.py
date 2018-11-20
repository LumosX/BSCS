import cmd
import os
from sim_util import *

##############################################################################################################

warrior = Actor("Sir Richard", 10, 7, 6, 3, 25, "2d6", [
    ("the Enchanted Sword", None, None, None),
])
trickster = Actor("Trickster", 7, 8, 7, 2, 24, "1d6+2", [
    ("his sword", None, None, None),
    ("the Dagger of Vislet", "2d6", "1d6", "Weapon"),
    ("his bow", "2d6", "1d6", "Weapon"),
])
sage = Actor("Mentok", 7, 7, 8, 3, 20, "1d6+2", [
    ("his quarterstaff", None, None, None),
    ("the Magic Bow", "2d6", "1d6+1", "Weapon"),
    ("Quarterstaff Technique", "2d8", "2d6+2", "Weapon"),
])
enchanter = Actor("Enchanter", 4, 7, 12, 2, 20, "1d6+1", [
    ("his sword", None, None, None),
    ("Swordthrust", "2d6", "3d6+3", "Blasting", 2),
    ("Nemesis Bolt", "2d6", "7d6+7", "Blasting", 5),
], 1)

battlefield = Battlefield([warrior, trickster, sage, enchanter,
    Actor("Thulander 1", 8, 7, 6, 0, 30, "2d6+1"),
    Actor("Thulander 2", 8, 7, 6, 0, 30, "2d6+1"),
])

##############################################################################################################

def log_string(addition):
    with open("combatLog.txt", "a+", encoding="utf-8") as file:
        file.write(addition)
        file.flush()


# noinspection PyMethodMayBeStatic
class Interpreter(cmd.Cmd):
    prompt = "\n>>>>> Awaiting command: "

    def __init__(self):
        cmd.Cmd.__init__(self)

    def do_exit(self, *args):
        """Exit the simulator."""
        return True
    do_EOF = do_x = do_q = do_quit = do_exit

    def do_status(self):
        battlefield.status()
    do_s = do_battlefield = do_status

    def do_log(self, arg):
        log_string(arg + "\n")
        
    def do_roll(self, arg):
        dice =  Dice(arg)
        print("Rolling", dice.value + "; got", dice.roll())
    do_r = do_roll

    def do_attack(self, args):
        params = args.split(" ")
        actor = battlefield.get_actor(params[0])
        target = battlefield.get_actor(params[1])
        attack = params[2] if len(params) >= 3 else None
        if actor is None or target is None:
            print("Invalid combatants specified. Try again.")
            return False
        # If all's well, do the attack
        result = actor.attack(target, attack)
        log_string(result + "\n")
        print(result)
    do_a = do_attack

    def do_clear(self, _):
        os.system('cls' if os.name == 'nt' else 'clear')
    do_cls = do_clear

    def do_help(self, arg):
        """List available commands."""
        # TODO fix aliases up somehow
        cmd.Cmd.do_help(self, arg)
    do_h = do_help



    def emptyline(self):
        pass

    def default(self, line):
        command, arg, line = self.parseline(line)
        print('Invalid command: "' + command + '"')


print("")
print("BLOOD SWORD COMBAT SIMULATOR")
print("(created by Lumos, 2018)")
print("Edit the script file to set up your battlefield with greater ease.")
battlefield.status()
interpreter = Interpreter()
interpreter.cmdloop()



