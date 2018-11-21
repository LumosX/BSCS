import cmd
import os
from sim_util import *


##############################################################################################################
# Arguments have names listed to make it easier to remember. It's also more cluttered, but what can one do...
warrior = Actor("Sir Richard", fpr=10, awa=7, psy=6, armour=3, end=25, damage="2d6", attacks=[
    Attack("the Enchanted Sword"),
])
trickster = Actor("Trickster", fpr=7, awa=8, psy=7, armour=2, end=24, damage="1d6+2", attacks=[
    Attack("his sword"),
    Attack("the Dagger of Vislet", to_hit="2d6", damage="1d6", attack_type="Weapon"),
    Attack("his bow", "2d6", "1d6", "Weapon"),
], perks=[
    Perk("Dodging Technique", extra_dodge=1)
])
sage = Actor("Mentok", fpr=7, awa=7, psy=8, armour=3, end=20, damage="1d6+2", attacks=[
    Attack("his quarterstaff"),
    Attack("the Magic Bow", to_hit="2d6", damage="1d6+1", attack_type="Weapon"),
    Attack("Quarterstaff Technique", "2d8", "2d6+2", "Weapon"),
])
enchanter = Actor("Enchanter", fpr=4, awa=7, psy=12, armour=2, end=20, damage="1d6+1", attacks=[
    Attack("his sword"),
    Attack("Swordthrust", to_hit="2d6", damage="3d6+3", attack_type="Blasting", spell_level=2),
    Attack("Nemesis Bolt", "2d6", "7d6+7", "Blasting", 5),
], spells_prepared=1)

battlefield = Battlefield([
    warrior, trickster, sage, enchanter,
    Actor("Thulander 1", fpr=8, awa=7, psy=6, armour=0, end=30, damage="2d6+1"),
    Actor("Thulander 2", fpr=8, awa=7, psy=6, armour=0, end=30, damage="2d6+1"),
])


##############################################################################################################
def log_string(addition):
    with open("combatLog.txt", "a+", encoding="utf-8") as file:
        file.write(addition)
        file.flush()


# noinspection PyMethodMayBeStatic,PyUnusedLocal,SpellCheckingInspection
class Interpreter(cmd.Cmd):
    prompt = "\n>>>>> Awaiting command: "

    def __init__(self):
        cmd.Cmd.__init__(self)

    def do_exit(self, *args):
        """Exit the simulator."""
        return True
    do_EOF = do_x = do_q = do_quit = do_exit

    def do_status(self):
        """Displays the current status of the battlefield."""
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
        """Clears the screen from previous application output."""
        os.system('cls' if os.name == 'nt' else 'clear')
    do_cls = do_clear

    def do_help(self, arg):
        """List available commands."""
        # TODO This needs to be replaced completely with something that looks better.
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



