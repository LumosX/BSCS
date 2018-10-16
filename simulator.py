import random
from os import system


class Dice:
    def __init__(self, value=None):
        self.value = value or "1d6"  # it should be a string
        # Decompile value into number of dice, number of sides, and any modifiers
        arr = self.value.split("d")  # index 0 = num dice; index 1 = num sizes +/- any modifiers
        self.numDice = int(arr[0])
        modifier = "0"
        if "+" in arr[1]:
            modifierMult = 1
            t = arr[1].split("+")
            self.numSides = int(t[0])
            modifier = t[1]
        elif "-" in arr[1]:
            modifierMult = -1
            t = arr[1].split("-")
            self.numSides = int(t[0])
            modifier = t[1]
        else:
            self.numSides = int(arr[1])
            modifierMult = 0
        self.modifier = int(modifier) * modifierMult

    # We'd also like a function that rolls the dice, right?
    def Roll(self):
        total = 0
        for _ in range(self.numDice):
            total += random.randint(1, self.numSides)
        total += self.modifier
        return total


#############################################
class Attack:
    def __init__(self, ownerActor, name=None, dice=None, damage=None, type=None, spellLevel=None):
        self.owner = ownerActor
        self.name = name or "Default"
        self.dice = Dice(dice) or Dice("2d6")
        self.damage = Dice(damage) or ownerActor.damage
        self.type = type or "Weapon"
        self.spellLevel = spellLevel or 0

    def Resolve(self):
        roll = self.dice.Roll()
        result = ""
        damageRoll = self.damage.Roll()
        # Weapon attacks: roll attack dice <= FPR
        if self.type == "Weapon":
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
        elif self.type == "Blasting":
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
        return self.name + ", " + self.type + ", dice: " + self.dice.value + ", damage: " + self.damage.value + " (level, if a spell: " + str(
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
        if attacks is None:
            self.attacks = [Attack(self, "Default", "2d6", damage, "Weapon")]
        else:
            self.attacks = [Attack(self,
                                   ("Default" if len(x) < 1 or x[0] is None else x[0]),  # Name
                                   ("2d6" if len(x) < 2 or x[1] is None else x[1]),  # Dice roll
                                   (damage if len(x) < 3 or x[2] is None else x[2]),  # Damage
                                   ("Weapon" if len(x) < 4 or x[3] is None else x[3]),
                                   (0 if len(x) < 5 or x[4] is None else x[4]))  # Type
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


def PrintCommands():
    print("COMMANDS:")
    print("> 's' or 'status' or 'battlefield' = displays the situation on the battlefield.")
    print("> 'h' or 'help' = displays this list.")
    print(
        "> 'a <X> <Y> [name]' (or 'attack') = makes actor X attack actor Y with attack [name] (default one if none specified). X and Y can be the IDs from the status list, or (partial) names.")
    print("> 'cls' or 'clear' = clears the terminal screen (use the one for your OS)")
    print("> 'print <string>' = adds the argument to the output file. Use this for notes and so on.")
    print("> 'q' or 'x' or 'quit' or 'exit' = quits simulator")
    print(
        "> 'exec <code>' = executes the code supplied afterwards. Can be used to modify the battlefield directly. Use at your own risk.")


print("")
print("BLOOD SWORD COMBAT SIMULATOR")
print("(created by Lumos, 2018)")
print("Edit the script file to set up your battlefield with greater ease.")
print("")
battlefield.Status()
print("")


def LogString(addition):
    with open("combatLog.txt", "w", encoding="utf-8") as file:
        file.write(addition)
        file.flush()


done = False

while done is False:
    print("")
    print(">>>>> Awaiting command: ", end="")
    cmd = input()
    # print("")
    if cmd in ['q', 'x', 'quit', 'exit']:
        done = True
    elif cmd in ['s', 'status', 'battlefield']:
        battlefield.Status()
    elif cmd in ['h', 'help']:
        PrintCommands()
    # elif cmd.startswith("? ")
    ## TODO: LIST ATTACKS
    # elif cmd.startswith("log health")
    ## TODO: LOG ALL ACTORS' HEALTH TO FILE
    elif cmd in ['cls', 'clear']:
        system(cmd)
    elif cmd.startswith("print "):
        LogString(result + "\n")
        print("Line added to the combat log.")
    elif cmd.startswith("exec "):
        exec(cmd.split(" ", 1)[1])
        print("Command executed.")
    # And now for the actual fighting commands:
    elif cmd.startswith("a ") or cmd.startswith("attack "):
        params = cmd.split(" ")  # a <actor> <target> [attack]
        actor = battlefield.GetActor(params[1])
        target = battlefield.GetActor(params[2])
        attack = params[3] if len(params) >= 4 else None
        # print(actor)
        # print(target)
        if actor is None or target is None:
            print("Invalid combatants specified. Try again.")
            continue
        # If all's well, attack
        result = actor.Attack(target, attack)
        LogString(result + "\n")
        print(result)
