import random
import cmd
import os
import re
from enum import Enum
from typing import List


class Dice:
    def __init__(self, value=None):
        self.value = value or "1d6"  # it should be a string
        # Decompile value into number of dice, number of sides, and any modifiers
        regex = re.match(r"(-?)(\d*)d([-+]?\d*)([-+]?\d*)", self.value)  # this is quite wonderful
        self.minus = -1 if regex.group(1) else 1
        self.num_dice = int(regex.group(2) or "1")
        self.num_sides = int(regex.group(3) or "0")
        self.modifier = int(regex.group(4) or "0")  # default value is 1d6+0

    # We'd also like a function that rolls the dice, right?
    def roll(self):
        if self.num_dice < 0 or self.num_sides < 0:
            return -1
        return self.modifier + (0 if self.num_dice == 0 or self.num_sides == 0 else
                                sum([random.randint(1, self.num_sides) for _ in range(self.num_dice)])) * self.minus


#############################################
class Attack:
    class Type(Enum):
        Weapon = 1,
        Blasting = 2,
        Psychic = 3

    def __init__(self, owner_actor, name=None, dice=None, damage=None, attack_type=None, spell_level=None):
        self.owner = owner_actor
        self.name = name or "Default"
        self.dice = Dice(dice) or Dice("2d6")
        self.damage = Dice(damage) or owner_actor.damage
        self.type = attack_type if attack_type is not None and \
                                   isinstance(attack_type, Attack.Type) else Attack.Type.Weapon
        self.spellLevel = spell_level or 0

    def resolve(self, target_actor=None):
        roll = self.dice.roll()
        damage_roll = self.damage.roll()
        # Weapon attacks: roll attack dice <= FPR
        if self.type == Attack.Type.Weapon:
            result = "(ROLLED " + str(roll)
            t = str(self.owner.FPR) + ") "
            if roll < self.owner.FPR:
                result += " < " + t + "Hit!"
            elif roll == self.owner.FPR:
                result += " = " + t + "Hit!"
            else:
                result += " > " + t + "Miss!"
            return roll, damage_roll, result, roll <= self.owner.FPR
        # Blasting spells: roll attack dice + level <= PSY - numSpellsPrepared
        elif self.type == Attack.Type.Blasting:
            result = "(ROLLED " + str(roll) + " + " + str(self.spellLevel)
            t = str(self.owner.PSY) + " - " + str(self.owner.numSpellsPrepared) + ") "
            if roll + self.spellLevel < self.owner.PSY - self.owner.numSpellsPrepared:
                result += " < " + t + "Hit!"
            elif roll + self.spellLevel == self.owner.PSY - self.owner.numSpellsPrepared:
                result += " = " + t + "Hit!"
            else:
                result += " > " + t + "Miss!"
            return roll, damage_roll, result, roll + self.spellLevel <= self.owner.PSY - self.owner.numSpellsPrepared
        # Psychic spells: roll
        else:
            # print("Invalid attack type.")
            return 0, 0, "Invalid attack type.", False

    def __str__(self):
        return self.name + ", " + str(self.type) + ", dice: " + self.dice.value + ", damage: " + self.damage.value + \
               " (level, if a spell: " + str(self.spellLevel) + ")"

    # I know it's a hack, but I don't care
    def __repr__(self):
        return self.__str__()


#############################################
# noinspection PyPep8Naming
class Actor:
    def __init__(self, name: str, FPR: int, AWA: int, PSY: int, ARM: int, END: int,
                 damage: str, attacks=None, num_spells_prepared: int=None):
        self.name = name
        self.FPR = FPR  # Fighting Prowess
        self.AWA = AWA  # Awareness
        self.PSY = PSY  # Psychic Ability
        self.ARM = ARM  # Armour rating
        self.END = END  # (Max) Endurance
        self.currentHP = END  # Current Endurance
        self.damage = Dice(damage)  # Regular weapon damage
        self.numSpellsPrepared = num_spells_prepared or 0
        # Custom tuple parsing. Why? Because of reasons...
        if attacks is None:
            self.attacks = [Attack(self, "Default", "2d6", damage, "Weapon")]
        else:
            self.attacks = [Attack(self,
                                   ("Default" if len(x) < 1 or x[0] is None else x[0]),  # Name
                                   ("2d6" if len(x) < 2 or x[1] is None else x[1]),  # Dice roll
                                   (damage if len(x) < 3 or x[2] is None else x[2]),  # Damage
                                   (Attack.Type.Weapon if len(x) < 4 or x[3] is None else Attack.Type[x[3]]),
                                   (0 if len(x) < 5 or x[4] is None else x[4]))  # Type
                            for x in attacks]
            # print(self.attacks)

    #
    #
    def attack(self, target_actor: 'Actor', attack_name: str=None):
        # Select correct attack, if available.
        if attack_name is None:
            attack_name = "Default"
        matching_attacks = [x for x in self.attacks if attack_name.lower() in x.name.lower()]
        # print(matching_attacks)
        attack = next(iter(matching_attacks), self.attacks[0])
        if attack is None:
            print("No such attack found for actor", self.name)
            return "No such attack found for actor " + self.name

        # Print attack statement
        attack_string = self.name + " attacks " + target_actor.name + (
            ". " if attack.name == "Default" else " using " + attack.name + ". ")
        (numRolled, damageDealt, result, attackHit) = attack.resolve()
        attack_string += result

        # If the attack missed, that's it.
        if not attackHit:
            return attack_string
        # But if the attack hit, subtract target armour, adjust health, and report.
        attack_damage = damageDealt - target_actor.ARM if damageDealt - target_actor.ARM > 0 else 0
        target_actor.currentHP -= attack_damage
        attack_string += (" Dealt " + str(damageDealt) + " - " + str(target_actor.ARM) + " = " + str(
            attack_damage) + " damage, " +
                          target_actor.name + " " + str(target_actor.currentHP) + "/" + str(target_actor.END) + ".")
        return attack_string

    def __str__(self):
        return (self.name + " (" + str(self.currentHP) + "/" + str(self.END) + "): FPR " + str(
            self.FPR) + ", AWA " + str(self.AWA) +
                ", PSY " + str(self.PSY) + "; Damage " + str(self.damage.value) + ", Armour rating " + str(self.ARM) +
                ("" if self.numSpellsPrepared == 0 else ", spells prepared: " + str(self.numSpellsPrepared)))


#############################################
class Battlefield:
    def __init__(self, actors=None):
        self.actors = actors or []

    def add(self, actors: List[Actor]):
        self.actors.extend(actors)

    def status(self):
        print("")
        print("BATTLEFIELD STATUS:")
        for i, x in enumerate(self.actors):
            print(i, "|", x)

    def get_actor(self, index) -> Actor:
        # print(index)
        if index.isdigit():
            return self.actors[int(index)]
        else:
            result = next((x for x in self.actors if index.lower() in x.name.lower()), None)
            if result is None:
                print("Invalid actor specified:", index)
            return result


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


def log_string(addition):
    with open("combatLog.txt", "a+", encoding="utf-8") as file:
        file.write(addition)
        file.flush()  # Probably unnecessary.


# noinspection PyMethodMayBeStatic
class Interpreter(cmd.Cmd):
    prompt = "\n>>>>> Awaiting command: "

    def __init__(self):
        cmd.Cmd.__init__(self)

    # noinspection PyUnusedLocal
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
        dice = Dice(arg)
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
