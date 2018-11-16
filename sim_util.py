import re
import random


class Dice:
    def __init__(self, value = None):
        self.value = value or "1d6"  # it should be a string
        # Decompile value into number of dice, number of sides, and any modifiers
        regex = re.match(r"(-?)(\d*)d([-+]?\d*)([-+]?\d*)", self.value)  # this is quite wonderful
        self.minus = -1 if regex.group(1) else 1
        self.num_dice = int(regex.group(2) or "1")
        self.num_sides = int(regex.group(3) or "0")
        self.modifier = int(regex.group(4) or "0")  # default value is 1d0+0

    # We'd also like a function that rolls the dice, right?
    def roll(self):
        if self.num_dice < 0 or self.num_sides < 0:
            return -1
        return self.modifier + (0 if self.num_dice == 0 or self.num_sides == 0 else
            sum([random.randint(1, self.num_sides) for _ in range(self.num_dice)])) * self.minus


#############################################
class Perk:
    def __init__(self, FPR=None, AWA=None, PSY=None, ARM=None, END=None, damage):







# This converts lists of positive and negative ints to a pretty string.
def prettify_ints(int_list):
    int_list = int_list if isinstance(int_list, list) else [int_list]
    # [1,2,-3,4] => 1 + 2 - 3 + 4
    # [-1,2,3,4] => -1 + 2 - 3 + 4
    result = str(int_list[0])
    for x in int_list[1:]:
        result += " + " if x > 0 else " - "
        result += str(abs(x))
    return result




class Attack:
    def __init__(self, owner_actor, name=None, dice=None, damage=None, attack_type=None, spell_level=None):
        self.owner = owner_actor
        self.name = name or "Default"
        self.dice = Dice(dice) or Dice("2d6")
        self.damage = Dice(damage) or owner_actor.damage
        self.type = attack_type or "Weapon"
        self.spellLevel = spell_level or 0

    def resolve(self, target_actor=None):
        # Now break this up into functions to make it more palatable,
        if self.type == "Weapon":
            return self.__weapon_attack(target_actor)
        elif self.type == "Blasting":
            return self.__blasting_attack(target_actor)
        elif self.type == "Psychic":
            return self.__psychic_attack(target_actor)
        else:
            print("Invalid attack type specified:", self.type)
            return

    # Generic function for the "(ROLLED X <=> Y)" output we need for everything.
    # Returns true if the roll is equal to or under the target
    def __compute_roll(self, rolled_vals, target_vals):
        roll_total = sum([int(x) for x in rolled_vals])
        roll_target = sum([int(x) for x in target_vals])

        sign = "="
        if roll_total < roll_target:
            sign = "<"
        elif roll_total > roll_target:
            sign = ">"
        roll_string = "(ROLLED " + prettify_ints(rolled) + " " + sign + " " + prettify_ints(target) + ")"
        return True if sign == "=" or sign == "<" else False, roll_string

    # Weapon attacks: roll attack dice + target perks <= own FPR + own perks; affected by armour
    def __weapon_attack(self, target_actor):
        # Roll to hit and damage.
        to_hit = self.dice.roll()

        # Add all of our modifiers to this

        hit, string = __compute_roll()


        return ""

    # Blasting spells: roll attack dice + spell level <= own PSY - spells prepped; affected by armour
    def __blasting_attack(self, target_actor, to_hit, damage):
        return ""

    # Psychic: target rolls 2d6 <= own PSY - spells prepped to resist; not affected by armour.
    def __psychic_attack(self, target_actor, damage):
        return "Not implemented."













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
class Actor:
    def __init__(self, name, FPR, AWA, PSY, ARM, END, damage, attacks=None, perks=None, num_spells_prepared=None):
        self.name = name
        self.FPR = FPR  # Fighting Prowess
        self.AWA = AWA  # Awareness
        self.PSY = PSY  # Psychic Ability
        self.ARM = ARM  # Armour rating
        self.END = END  # (Max) Endurance
        self.currentHP = END  # Current Endurance
        self.damage = Dice(damage)  # Regular weapon damage
        self.numSpellsPrepared = num_spells_prepared or 0
        self.perks = perks  # "Perks" currently active
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
    def attack(self, target_actor, attack_name=None):
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

    def add(self, actors):
        self.actors.extend(actors)

    def status(self):
        print("")
        print("BATTLEFIELD STATUS:")
        for i, x in enumerate(self.actors):
            print(i, "|", x)

    def get_actor(self, index):
        # print(index)
        if index.isdigit():
            return self.actors[int(index)]
        else:
            result = next((x for x in self.actors if index.lower() in x.name.lower()), None)
            if result is None:
                print("Invalid actor specified:", index)
            return result