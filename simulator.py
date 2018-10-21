import random
import cmd
import os
import re
from enum import Enum


class Dice:
    def __init__(self, value=None):
        self.value = value or "1d6"  # it should be a string
        # Decompile value into number of dice, number of sides, and any modifiers
        regex = re.match(r"(\d*)d(\d*)([-+]?\d*)", self.value) # this is quite wonderful
        self.numDice = int(regex.group(1) or "1")
        self.numSides = int(regex.group(2) or "6")
        self.modifier = int(regex.group(3) or "0") # default value is 1d6+0

    # We'd also like a function that rolls the dice, right?
    def Roll(self):
        return self.modifier + (0 if self.numDice == 0 else
            sum([random.randint(1, self.numSides) for _ in range(self.numDice)]))

#############################################
class Attack:
    class Type(Enum):
        Weapon = 0,
        Blasting = 1,
        Psychic = 2

    def __init__(self, ownerActor, name=None, dice=None, damage=None, type=None, spellLevel=None):
        self.owner = ownerActor
        self.name = name or "Default"
        self.dice = Dice(dice) or Dice("2d6")
        self.damage = Dice(damage) or ownerActor.damage
        self.type = type if type is not None and isinstance(type, Attack.Type) else Attack.Type.Weapon
        self.spellLevel = spellLevel or 0

    def Resolve(self):
        roll = self.dice.Roll()
        result = ""
        damageRoll = self.damage.Roll()
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
            return (roll, damageRoll, result, roll <= self.owner.FPR)
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
            return roll, damageRoll, result, roll + self.spellLevel <= self.owner.PSY - self.owner.numSpellsPrepared
        # Psychic spells require knowledge of the target's PSY to calculate. Todo?
        else:
            # print("Invalid attack type.")
            return 0, 0, "Invalid attack type.", False

    def __str__(self):
        return self.name + ", " + str(self.type) + ", dice: " + self.dice.value + ", damage: " + self.damage.value + " (level, if a spell: " + str(
            self.spellLevel) + ")"

    # I know it's a hack, but I don't care
    def __repr__(self):
        return self.__str__()


#############################################
class Actor:
    def __init__(self, name, FPR, AWA, PSY, ARM, END, damage, attacks=None, numSpellsPrepared=None):
        self.name = name
        self.FPR = FPR  # Fighting Prowess
        self.AWA = AWA  # Awareness
        self.PSY = PSY  # Psychic Ability
        self.ARM = ARM  # Armour rating
        self.END = END  # (Max) Endurance
        self.currentHP = END  # Current Endurance
        self.damage = Dice(damage)  # Regular weapon damage
        self.numSpellsPrepared = numSpellsPrepared or 0
        # Custom tuple parsing. Why? Because of reasons...
        if attacks is None:
            self.attacks = [Attack(self, "Default", "2d6", damage, "Weapon")]
        else:
            self.attacks = [Attack(self,
                                   ("Default"           if len(x) < 1 or x[0] is None else x[0]),  # Name
                                   ("2d6"               if len(x) < 2 or x[1] is None else x[1]),  # Dice roll
                                   (damage              if len(x) < 3 or x[2] is None else x[2]),  # Damage
                                   (Attack.Type.Weapon  if len(x) < 4 or x[3] is None else Attack.Type[x[3]]),
                                   (0                   if len(x) < 5 or x[4] is None else x[4]))  # Type
                            for x in attacks]
            # print(self.attacks)

    #
    #
    def Attack(self, targetActor, attackName=None):
        # Select correct attack, if available.
        if attackName is None:
            attackName = "Default"
        matchingAttacks = [x for x in self.attacks if attackName.lower() in x.name.lower()]
        # print(matchingAttacks)
        attack = next(iter(matchingAttacks), self.attacks[0])
        if attack is None:
            print("No such attack found for actor", self.name)
            return "No such attack found for actor " + self.name

        # Print attack statement
        attackString = self.name + " attacks " + targetActor.name + (
            ". " if attack.name == "Default" else " using " + attack.name + ". ")
        (numRolled, damageDealt, result, attackHit) = attack.Resolve()
        attackString += result

        # If the attack missed, that's it.
        if not attackHit:
            return attackString
        # But if the attack hit, subtract target armour, adjust health, and report.
        attackDamage = damageDealt - targetActor.ARM if damageDealt - targetActor.ARM > 0 else 0
        targetActor.currentHP -= attackDamage
        attackString += (" Dealt " + str(damageDealt) + " - " + str(targetActor.ARM) + " = " + str(
            attackDamage) + " damage, " +
                         targetActor.name + " " + str(targetActor.currentHP) + "/" + str(targetActor.END) + ".")
        return attackString

    def __str__(self):
        return (self.name + " (" + str(self.currentHP) + "/" + str(self.END) + "): FPR " + str(
            self.FPR) + ", AWA " + str(self.AWA) +
                ", PSY " + str(self.PSY) + "; Damage " + str(self.damage.value) + ", Armour rating " + str(self.ARM) +
                ("" if self.numSpellsPrepared == 0 else ", spells prepared: " + str(self.numSpellsPrepared)))


#############################################
class Battlefield:
    def __init__(self, actors=None):
        self.actors = actors or []

    def Add(self, actors):
        self.actors.extend(actors)

    def Status(self):
        print("")
        print("BATTLEFIELD STATUS:")
        for i, x in enumerate(self.actors):
            print(i, "|", x)

    def GetActor(self, index):
        #print(index)
        if index.isdigit():
            return self.actors[int(index)]
        else:
            result = next((x for x in self.actors if index.lower() in x.name.lower()), None)
            if result is None:
                print("Invalid actor specified:", index)
            return result


##############################################################################################################
warrior = Actor("Sir Richard", 10, 5, 6, 3, 18, "1d6+2", [
    ("the Enchanted Sword", None, None, None),
])
trickster = Actor("Trickster", 6, 8, 6, 2, 18, "1d6+1", [
    ("his sword", None, None, None),
    ("the Dagger of Vislet", "2d6", "1d6", "Weapon"),
    ("his bow", "2d6", "1d6", "Weapon"),
])
sage = Actor("Mentok", 7, 6, 7, 3, 15, "1d6+1", [
    ("his quarterstaff", None, None, None),
    ("the Magic Bow", "2d6", "1d6+1", "Weapon"),
    ("Quarterstaff Technique", "2d8", "2d6+1", "Weapon"),
])
enchanter = Actor("Enchanter", 2, 7, 12, 2, 15, "1d6", [
    ("his sword", None, None, None),
    ("Swordthrust", "2d6", "3d6+3", "Blasting", 2),
    ("Nemesis Bolt", "2d6", "7d6+7", "Blasting", 5),
], 1)

s1 = Actor("Skeleton 1", 9, 9, 9, 3, 21, "2d6")
s2 = Actor("Skeleton 2", 9, 9, 9, 3, 21, "2d6")
s3 = Actor("Skeleton 3", 9, 9, 9, 3, 21, "2d6")
s4 = Actor("Skeleton 4", 9, 9, 9, 3, 21, "2d6")

battlefield = Battlefield([warrior, trickster, sage, enchanter, s1, s2, s3, s4])


def LogString(addition):
    with open("combatLog.txt", "w", encoding="utf-8") as file:
        file.write(addition)
        file.flush()


class Interpreter(cmd.Cmd):
    prompt = "\n>>>>> Awaiting command: "

    def __init__(self):
        cmd.Cmd.__init__(self)

    def do_exit(self, *args):
        """Exit the simulator."""
        return True
    do_EOF = do_x = do_q = do_quit = do_exit

    def do_status(self):
        battlefield.Status()
    do_s = do_battlefield = do_status

    def do_log(self, arg):
        LogString(arg + "\n")

    def do_attack(self, args):
        #print(args)
        params = args.split(" ")
        actor = battlefield.GetActor(params[0])
        target = battlefield.GetActor(params[1])
        attack = params[2] if len(params) >= 3 else None
        if actor is None or target is None:
            print("Invalid combatants specified. Try again.")
            return False
        # If all's well, do the attack
        result = actor.Attack(target, attack)
        LogString(result + "\n")
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
        cmd, arg, line = self.parseline(line)
        print(f'Invalid command: "{cmd}"')


print("")
print("BLOOD SWORD COMBAT SIMULATOR")
print("(created by Lumos, 2018)")
print("Edit the script file to set up your battlefield with greater ease.")
battlefield.Status()
interpreter = Interpreter()
interpreter.cmdloop()



