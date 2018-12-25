import re
import random
import cmd
import os
import shlex

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
                self.modifier = int(regex.group(1))
                self.minus = 1
                self.num_dice = 0
                self.num_sides = 0

    # We'd also like a function that rolls the dice, right?
    def roll(self):
        if self.num_dice < 0 or self.num_sides < 0:
            return -1
        return self.modifier + (0 if self.num_dice == 0 or self.num_sides == 0 else
                                sum([random.randint(1, self.num_sides) for _ in range(self.num_dice)])) * self.minus

    def __str__(self):
        return self.value


#############################################
# A perk is applied to an actor and modifies THIS actor's properties.
class Perk:
    def __init__(self, name, fpr=None, awa=None, psy=None, armour=None, end=None, to_hit=None,
                 weapon_damage=None, spell_damage=None, turns=None, extra_dodge=None):
        self.name = name
        self.turns_remaining = turns or 1500000  # If no turns have been specified, make it "eternal"
        self.values = {
            "FPR": fpr or 0,  # Fighting Prowess
            "AWA": awa or 0,  # Awareness
            "PSY": psy or 0,  # Psychic Ability
            "END": end or 0,  # Endurance
            "Armour": armour or 0,  # Armour
            "To hit": to_hit or "0",  # To hit penalties for Nighthowl
            "Weapon Damage": weapon_damage or "0",  # Weapon damage mods only
            "Spell Damage": spell_damage or "0",  # Spell damage mods only (both blasting and psychic)
            "Dodge": extra_dodge or "0",  # For stuff like Dodging Technique
        }

    #
    # e.g. "Dodging Technique (Dodge +1)" or "Prepared Spells (PSY -1)" or "Skill Amulet (FPR +7, Armour +7)"
    def __str__(self):
        # Get all attributes that the perk modifies
        mods = [attr + " " + ["", "+"][type(val) == str or val > 0] + str(val) for attr, val in self.values.items() if str(val) != "0"]
        return self.name + ("" if len(mods) == 0 else " (" + ", ".join(mods) + ")")


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


# Generic function for the "(ROLLED X <=> Y)" output we need for everything.
# Returns true if the roll is equal to or under the target
def compute_roll(rolled_vals, target_vals):
    roll_total = sum([int(x) for x in rolled_vals])
    roll_target = sum([int(x) for x in target_vals])

    sign = "="
    if roll_total < roll_target:
        sign = "<"
    elif roll_total > roll_target:
        sign = ">"
    roll_string = "(ROLLED " + prettify_ints(rolled_vals) + " " + sign + " " + prettify_ints(target_vals) + ") "
    hit = sign == "=" or sign == "<"
    roll_string += "Hit!" if hit else "Miss!"
    return hit, roll_string


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
        self.damage = damage or owner_actor.damage
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
                           (0              if x[4] is None else x[4]))  # Spell level

    #
    # Resolves an attack. By calling the specific function for each type of attack.
    def resolve(self, target_actor):
        # Now break this up into functions to make it more palatable,
        if self.type == "Weapon":
            return self.__weapon_attack(target_actor)
        elif self.type == "Blasting":
            return self.__blasting_attack(target_actor)
        elif self.type == "Psychic":
            return self.__psychic_attack(target_actor)
        elif self.type == "GuaranteedDamage":
            return self.__guaranteed_attack(target_actor)
        elif self.type == "GuaranteedIgnoreArmour":
            return self.__guaranteed_ap_attack(target_actor)
        else:
            print("Invalid attack type specified:", self.type)
            return

    #
    # Weapon attacks: roll attack dice + target perks dodge <= own FPR + own perks FPR; affected by armour
    # noinspection PyPep8Naming
    def __weapon_attack(self, target_actor):
        # Roll to hit first and add all relevant modifiers to this
        rolled_vals = [self.to_hit.roll()] + target_actor.list_attribute("Dodge", False)
        target_vals = self.owner.list_attribute("FPR")
        # At this point string holds "(rolled X <=> Y) Hit!/Miss!"
        hit, string = compute_roll(rolled_vals, target_vals)
        # If we missed, we're good. If we hit, roll damage and subtract target armour.
        if hit:
            # Calculate and deal damage.
            target_armour_neg = [-x for x in target_actor.list_attribute("Armour", True)]
            all_attrs = [self.damage] + self.owner.list_attribute("Weapon Damage", False)
            damage_vals = list(map(lambda x: Dice(x).roll(), all_attrs)) + target_armour_neg
            damage_dealt = max(0, sum(damage_vals))
            string += " Dealt " + prettify_ints(damage_vals) + " = " + str(damage_dealt) + " damage; "
            # Deal damage to the actor and report status.
            string += target_actor.take_damage(damage_dealt)
        return string

    #
    # Blasting spells: roll attack dice + spell level <= own PSY - spells prepped; affected by armour
    def __blasting_attack(self, target_actor):
        # Similar to the one above. Roll to hit, add all modifiers, check to see if we hit.
        rolled_vals = [self.to_hit.roll(), self.spellLevel] # Dodge doesn't work on targets when casting spells
        target_vals = self.owner.list_attribute("PSY")
        # At this point string holds "(rolled X <=> Y) Hit!/Miss!"
        hit, string = compute_roll(rolled_vals, target_vals)
        if hit:
            # Calc and deal damage again, armour is a thing here.
            target_armour_neg = [-x for x in target_actor.list_attribute("Armour", True)]
            all_attrs = [self.damage] + self.owner.list_attribute("Spell Damage", False)
            damage_vals = list(map(lambda x: Dice(x).roll(), all_attrs)) + target_armour_neg
            damage_dealt = max(0, sum(damage_vals))
            string += " Dealt " + prettify_ints(damage_vals) + " = " + str(damage_dealt) + " damage; "
            # Deal damage to the actor and report status.
            string += target_actor.take_damage(damage_dealt)
        return string

    # Psychic: target rolls 2d6 <= own PSY - spells prepped to resist; not affected by armour.
    def __psychic_attack(self, target_actor):
        return "Not implemented."
        
    # "Guaranteed, Armour-Piercing": Icon's Retributive Fire. Always hits and ignores armour.
    def __guaranteed_ap_attack(self, target_actor):
        # Calc and deal damage, no rolls.
        all_attrs = [self.damage] + self.owner.list_attribute("Spell Damage", False)
        damage_vals = list(map(lambda x: Dice(x).roll(), all_attrs))
        damage_dealt = max(0, sum(damage_vals))
        string = "Dealt " + str(damage_dealt) + " damage; "
        # Deal damage to the actor and report status.
        string += target_actor.take_damage(damage_dealt)
        return string
        
    # "Guaranteed": Hacky usage. Always hits, but takes armour into account
    def __guaranteed_attack(self, target_actor):
        # Calc and deal damage, no rolls.
        all_attrs = [self.damage] + self.owner.list_attribute("Spell Damage", False)
        target_armour_neg = [-x for x in target_actor.list_attribute("Armour", True)]
        damage_vals = list(map(lambda x: Dice(x).roll(), all_attrs)) + target_armour_neg
        damage_dealt = max(0, sum(damage_vals))
        string = "Dealt " + prettify_ints(damage_vals) + " = " + str(damage_dealt) + " damage; "
        # Deal damage to the actor and report status.
        string += target_actor.take_damage(damage_dealt)
        return string

    def __str__(self):
        return self.name + ", " + str(self.type) + \
               ", dice: " + self.to_hit.value + \
               ", damage: " + self.damage.value + \
               " (level, if a spell: " + str(self.spellLevel) + ")"

    # I know it's a hack, but I don't care
    def __repr__(self):
        return self.__str__()


#############################################
class Actor:
    def __init__(self, name, fpr, awa, psy, armour, end, damage, attacks=None, perks=None):
        self.name = name
        # Parse basic attributes
        self.attributes = {
            'FPR': fpr,  # Fighting Prowess
            'AWA': awa,  # Awareness
            'PSY': psy,  # Psychic Ability
            'END': end,  # Base Endurance (max HP before any modifiers)
            'Armour': armour,  # Armour
            'Damage': damage  # Default weapon damage
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

        # Current endurance is last, taking all perks into account.
        total_endurance = sum(self.list_attribute('END'))
        self.max_HP = total_endurance
        self.cur_HP = total_endurance

    #
    #
    # Produces a list of all modifiers of a particular attribute.
    def list_attribute(self, attribute, return_zero_if_empty=None):
        if return_zero_if_empty is None:
            return_zero_if_empty = True
        result = [self.attributes.get(attribute)] + \
                 [x.values.get(attribute) for x in self.perks if x.turns_remaining > 0]
        # Filter out all zeroes by default...
        result = list(filter(lambda x: x is not None and str(x) != '0', result))
        # ... but return a single zero if the final list is empty and the option is selected
        return result or ([0] if return_zero_if_empty else result)

    #
    #
    def attack(self, target_actor, attack=None):
        # If we've fed this method an attack definition instead of an attack name, use it directly.
        if isinstance(attack, AttackClass):
            target_attack = attack
        else:
            # Select correct attack, if available.
            if attack is None:
                attack = "Default"
            matching_attacks = [x for x in self.attacks if attack.lower() in x.name.lower()]
            # print(matching_attacks)
            target_attack = next(iter(matching_attacks), self.attacks[0])
            if target_attack is None:
                print("No such attack found for actor", self.name)
                return "No such attack found for actor " + self.name

        # Print attack statement
        attack_string = self.name + " attacks " + target_actor.name + \
                        ("" if target_attack.name == "Default" else " using " + target_attack.name) + ". "
        return attack_string + target_attack.resolve(target_actor)

    #
    # A method for taking damage. Returns current HP/max HP, and whether the target is dead (if it is).
    def take_damage(self, damage_dealt):
        self.cur_HP -= damage_dealt
        dead = self.cur_HP <= 0
        new_HP_str = str(self.cur_HP) + "/" + str(self.max_HP)
        return self.name + (" is dead. (" + new_HP_str + ")" if dead else " " + new_HP_str)

    #
    def __str__(self):
        # And so is damage, because it consists of "Dice" objects.
        total_damage = " + ".join([x for x in self.list_attribute('Damage') if x != 0 and x != "0"])
        # And also perks: if we're affected by any perks, list them. One on each line, prettily indented.
        perks = "" if len(self.perks) == 0 \
                   else "\n    Affected by: " + (",\n" + " " * 17).join(map(lambda x: str(x), self.perks))

        return (self.name + " (" + str(self.cur_HP) + "/" + str(self.max_HP) + ")" +
                ", FPR " + prettify_ints(self.list_attribute('FPR')) +
                ", AWA " + prettify_ints(self.list_attribute('AWA')) +
                ", PSY " + prettify_ints(self.list_attribute('PSY')) +
                "; Damage " + total_damage +
                ", Armour rating " + prettify_ints(self.list_attribute('Armour')) +
                perks)


#############################################
class Battlefield:
    # This is a very ham-fisted quote-unquote "singleton" implementation. Why? Because.
    active_battlefield = None

    def __init__(self, actors=None):
        self.actors = actors or []
        Battlefield.active_battlefield = self

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

    def do_status(self, *args):
        """Displays the current status of the battlefield."""
        Battlefield.active_battlefield.status()

    do_s = do_battlefield = do_status

    def do_log(self, arg):
        log_string(arg + "\n")

    def do_roll(self, arg):
        dice = Dice(arg)
        print("Rolling", dice.value + "; got", dice.roll())

    do_r = do_roll

    def do_attack(self, args):
        params = shlex.split(args)
        actor = Battlefield.active_battlefield.get_actor(params[0])
        targets = params[1].split(",")
        attack = params[2] if len(params) >= 3 else None
        # Natively supports multiattacks
        for t in targets:
            target = Battlefield.active_battlefield.get_actor(t)
            if actor is None or target is None:
                print("Invalid combatants specified. Try again.")
            else:
                # If all's well, do the attack
                result = actor.attack(target, attack)
                log_string(result + "\n")
                print(result)

    do_a = do_attack
    
    #
    # This is a way for an actor to deal guaranteed damage to another one, bypassing attacks
    def do_damage(self, args):
        params = shlex.split(args)
        actor = Battlefield.active_battlefield.get_actor(params[0])
        targets = params[1].split(",")
        damage = params[2]
        name = params[3] if len(params) > 3 else "an ability"
        attack = AttackClass(actor, name=name, damage=damage, attack_type="GuaranteedDamage")
        # Natively supports multiattacks
        for t in targets:
            target = Battlefield.active_battlefield.get_actor(t)
            if actor is None or target is None:
                print("Invalid combatant specified. Try again.")
            else:
                # If all's well, do the attack
                result = actor.attack(target, attack)
                log_string(result + "\n")
                print(result)
              
    #
    # And this is the same, but the damage is armour-piercing.
    def do_ap_damage(self, args):
        params = shlex.split(args)
        actor = Battlefield.active_battlefield.get_actor(params[0])
        targets = params[1].split(",")
        damage = params[2] or 0
        name = params[3] if len(params) > 3 else "an ability"
        attack = AttackClass(actor, name=name, damage=damage, attack_type="GuaranteedIgnoreArmour", spell_level=0)
        # Natively supports multiattacks
        for t in targets:
            target = Battlefield.active_battlefield.get_actor(t)
            if actor is None or target is None:
                print("Invalid combatant specified. Try again.")
            else:
                # If all's well, do the attack
                result = actor.attack(target, attack)
                log_string(result + "\n")
                print(result)
                
    #
    def do_heal(self, args):
        params = shlex.split(args)
        actor = Battlefield.active_battlefield.get_actor(params[0])
        amount = max(0, int(params[1]) if len(params) > 1 else 0)
        result = actor.name + " is healed for " + str(amount) + "; " + actor.take_damage(-1 * amount)
        log_string(result + "\n")
        print(result)
    
    
    #
    def do_exec(self, args):
        exec(args)
        print("Command executed.")

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