from util import *


##############################################################################################################
# Arguments have names listed to make it easier to remember. It's also more cluttered, but what can you do...
warrior = Actor("Sir Richard", fpr=9, awa=7, psy=6, armour=4, end=37, damage="2d6+2", attacks=[
    Attack("the Enchanted Sword", fpr_bonus=1),
    Attack("his Enchanted Axe", damage="3d6+2")
], perks=[
    Perk("Invulnerability", invulnerability_threshold=6),
    Perk("Resist All", resist_all=True),
])
trickster = Actor("Trickster", fpr=7, awa=8, psy=7, armour=4, end=36, damage="2d6+1", attacks=[
    Attack("his Enchanted Axe", damage="3d6+1"),
    Attack("the Dagger of Vislet", to_hit="2d6", damage="1d6", attack_type="Weapon"),
    Attack("his Magic Bow +3", "2d6", "1d6+4", "Weapon"),
    Attack("the Blood Sword", damage="4d6+1", fpr_bonus=3),
], perks=[
    Perk("Dodging Technique", extra_dodge=1),
    Perk("Resist All", resist_all=True),
])
sage = Actor("Mentok", fpr=8, awa=8, psy=9, armour=6, end=40, damage="2d6+1", attacks=[
    Attack("his Steel Quarterstaff", damage="2d6+4"),
    Attack("the Magic Bow", to_hit="2d6", damage="1d6+1", attack_type="Weapon"),
    Attack("Quarterstaff Technique", "2d8", "3d6+4", "Weapon"),
], perks=[
    Perk("Invulnerability", invulnerability_threshold=6),
    Perk("Resist All", resist_all=True),
])
enchanter = Actor("Enchanter", fpr=4, awa=7, psy=12, armour=5, end=30, damage="1d6+3", attacks=[
    Attack("his sword"),
    Attack("Swordthrust", to_hit="2d6", damage="3d6+3", attack_type="Blasting", spell_level=2),
    Attack("Nemesis Bolt", "2d6", "7d6+7", "Blasting", 5),
    Attack("Sheet Lightning", "2d6", "2d6+2", "Blasting", 4),
], perks=[
    Perk("Prepared Spells", psy=-1),  # Remember to update the number of prepared spells here!
    Perk("Resist All", resist_all=True),
])


battlefield = Battlefield([
    warrior, trickster, sage, enchanter,
    # Actor("Susurrien", fpr=8, awa=9, psy=10, armour=0, end=80, damage="4d6"),

    # Icon in book 3
    # Actor("Icon", fpr=9, awa=9, psy=9, armour=2, end=55, damage="5d6", attacks=[
        # Attack("his sword"),
        # Attack("Retributive Fire", to_hit="0", damage="1", attack_type="GuaranteedIgnoreArmour"),
    # ]),
    # Icon in Doomwalk
    Actor("Icon", fpr=9, awa=9, psy=9, armour=0, end=55, damage="5d6", attacks=[
        Attack("his sword"),
    ], perks=[
        Perk("Prepared Spells", psy=-1),
    ]),


])


##############################################################################################################


print("")
print("BLOOD SWORD COMBAT SIMULATOR")
print("(created by Lumos, 2018)")
print("Edit the script file to set up your battlefield with greater ease.")
battlefield.status()

# trickster.attack(warrior, "dagg")

interpreter = Interpreter()
interpreter.cmdloop()
