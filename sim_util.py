import re
import random


#############################################
class Dice:
    def __init__(self, value=None):
        self.value = value or "1d6"  # it should be a string
        # Decompile value into number of dice, number of sides, and any modifiers
        regex = re.match(r"(-?)(\d*)d([-+]?\d*)([-+]?\d*)", self.value)  # this is quite wonderful
        if regex is not None:
            self.minus = -1 if regex.group(1) else 1
            self.num_dice = int(regex.group(2) or "1")
            self.num_sides = int(regex.group(3) or "0")
            self.modifier = int(regex.group(4) or "0")  # default value is 1d0+0
        # However, if it's a single digit instead, just set the modifier accordingly
        else:
            regex = re.match("(-?\d+)", self.value)
            if regex is None:
                raise AttributeError("A dice object cannot be initialised with a value of '" + str(value) + "'")
            else:
                self.modifier = regex.group(1)
                self.minus = 1
                self.num_dice = 0
                self.num_sides = 0

    # We'd also like a function that rolls the dice, right?
    def roll(self):
        if self.num_dice < 0 or self.num_sides < 0:
            return -1
        return self.modifier + (0 if self.num_dice == 0 or self.num_sides == 0 else
            sum([random.randint(1, self.num_sides) for _ in range(self.num_dice)])) * self.minus


#############################################
# A perk is applied to an actor and modifies THIS actor's properties.
class Perk:
    def __init__(self, name, fpr=None, awa=None, psy=None, armour=None, end=None,
                 to_hit=None, damage=None, turns=None, extra_dodge=None):
        self.name = name
        self.turns_remaining = turns or 1500000  # If no turns have been specified, make it "eternal"
        self.values = {
            "fpr": fpr or 0,  # Fighting Prowess
            "awa": awa or 0,  # Awareness
            "psy": psy or 0,  # Psychic Ability
            "end": end or 0,  # Endurance
            "armour": armour or 0,  # Armour
            "to_hit": to_hit or Dice("0"),  # To hit penalties for Nighthowl
            "damage": damage or Dice("0"),  # Extra damage or damage penalties
            "extra_dodge": extra_dodge or Dice("0"),  # For stuff like Dodging Technique
        }

    # TODO: define the ToString method.
    # e.g. "Dodging Technique (Dodge +1)" or "Prepared Spells (PSY -1)"


#############################################
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


# Use this to make defining "attack tuple notation" easier to read.
# Tried named tuples, but their optional parameters are version dependent or some other bullshit, not worth it.
# noinspection PyPep8Naming
def Attack(name, to_hit=None, damage=None, attack_type=None, spell_level=None):
    return name, to_hit, damage, attack_type, spell_level


class AttackClass:
    def __init__(self, owner_actor, name=None, to_hit=None, damage=None, attack_type=None, spell_level=None):
        self.owner = owner_actor
        self.name = name or "Default"
        self.to_hit = Dice(to_hit) or Dice("2d6")
        self.damage = Dice(damage) or owner_actor.damage
        self.type = attack_type or "Weapon"
        self.spellLevel = spell_level or 0

    # Easier generator for actor constructors.
    @classmethod
    def default_attack(cls, owner_actor, default_damage):
        return AttackClass(owner_actor, "Default", "2d6", default_damage, "Weapon")

    # This one parses "attack tuple notation", again to make actor constructors cleaner.
    @classmethod
    def parse_tuple(cls, owner_actor, default_damage, x):
        return AttackClass(owner_actor,
                           ("Default"      if x[0] is None else x[0]),  # Name
                           ("2d6"          if x[1] is None else x[1]),  # Dice roll
                           (default_damage if x[2] is None else x[2]),  # Damage
                           ("Weapon"       if x[3] is None else x[3]),  # Type
                           (0              if x[4] is None else x[4]))  # Type

    #
    #
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

    #
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
        roll_string = "(ROLLED " + prettify_ints(rolled_vals) + " " + sign + " " + prettify_ints(target_vals) + ")"
        return True if sign == "=" or sign == "<" else False, roll_string

    #
    # Weapon attacks: roll attack dice + target perks dodge <= own FPR + own perks FPR; affected by armour
    def __weapon_attack(self, target_actor):
        # Roll to hit and damage.
        to_hit = self.to_hit.roll()
        damage = self.damage.roll()
        # Add all of our modifiers to this


        hit, string = __compute_roll()


        return ""

    #
    # Blasting spells: roll attack dice + spell level <= own PSY - spells prepped; affected by armour
    def __blasting_attack(self, target_actor, to_hit, damage):
        return ""

    # Psychic: target rolls 2d6 <= own PSY - spells prepped to resist; not affected by armour.
    def __psychic_attack(self, target_actor, damage):
        return "Not implemented."

    def __str__(self):
        return self.name + ", " + str(self.type) + ", dice: " + self.to_hit.value + ", damage: " + self.damage.value + \
               " (level, if a spell: " + str(self.spellLevel) + ")"

    # I know it's a hack, but I don't care
    def __repr__(self):
        return self.__str__()


#############################################
class Actor:
    def __init__(self, name, fpr, awa, psy, armour, end, damage, attacks=None, perks=None, spells_prepared=None):
        self.name = name
        # Parse basic attributes
        self.attributes = {
            'fpr': fpr,  # Fighting Prowess
            'awa': awa,  # Awareness
            'psy': psy,  # Psychic Ability
            'end': end,  # Base Endurance (max HP before any modifiers)
            'armour': armour,  # Armour
            'damage': Dice(damage)  # Default weapon damage
        }
        # Now parse attacks.
        if attacks is None:
            self.attacks = [AttackClass.default_attack(self, damage)]
        else:
            self.attacks = [AttackClass.parse_tuple(self, damage, x) for x in attacks]
        # And perks. If it's a list of perks, use it; if it's a single perk, make it a list; else ignore
        self.perks = []
        if type(perks) is list:
            self.perks = perks
        elif isinstance(perks, Perk):

            self.perks = [perks]
        # Spells prepared: Rig this as a perk, because why not?
        if spells_prepared is not None and spells_prepared > 0:
            self.perks.append(Perk("Prepared Spells", psy=-1 * spells_prepared))

        # Current endurance is last, taking all perks into account.
        total_endurance = sum(self.list_attribute('end'))
        self.end = total_endurance
        self.currentHP = total_endurance

    #
    #
    # Produces a list of all modifiers of a particular attribute.
    def list_attribute(self, attribute):
        result = [self.attributes.get(attribute)] + [x.values.get(attribute) for x in self.perks]
        # Filter out all zeroes, but return a single zero if the list is empty (all were zeroes)
        return list(filter(None, result)) or [0]

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
        # Prepared spells are special
        spells_prepared = next((x.values.get('psy', 0) * -1 for x in self.perks if x.name == "Prepared Spells"), 0)
        # And so is damage, because it consists of "Dice" objects.
        total_damage = " + ".join([x.value for x in self.list_attribute('damage') if x != 0 and x.value != "0"])
        # And also perks: if we're affected by any perks, list them.
        perks = "" if len(self.perks) == 0 else "\n    Affected by: " + ", ".join(map(lambda x: x.name, self.perks))

        return (self.name + " (" + str(self.currentHP) + "/" + str(self.end) + ")" +
                ", FPR " + prettify_ints(self.list_attribute('fpr')) +
                ", AWA " + prettify_ints(self.list_attribute('awa')) +
                ", PSY " + prettify_ints(self.list_attribute('psy')) +
                "; Damage " + total_damage +
                ", Armour rating " + prettify_ints(self.list_attribute('armour')) +
                ("" if spells_prepared == 0 else ", spells prepared: " + str(spells_prepared))) + perks


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