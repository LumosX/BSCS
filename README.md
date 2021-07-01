# BSCS: Blood Sword Combat Simulator
This is a simple utility that semi-automates combat encounters for the [Blood Sword gamebooks](https://en.wikipedia.org/wiki/Blood_Sword_(gamebook_series)).


![image](https://user-images.githubusercontent.com/17273782/124195687-d828df80-dac2-11eb-96cd-8235d25cd2d3.png)


## Features
* Attack roll simulation; weapon attacks and blasting spells
* Different attacks with different attack dice and damage outputs (e.g. the Sage's Quarterstaff Technique)
* Battlefields: sets of actors (players or enemies) that facilitate simple attacking logic
* Maintaining actor states across rounds (HP tracking)
* All output is logged to a text file automatically
* Custom statement logging (useful for leaving yourself notes or otherwise modifying the output log file)
* All spells supported (blasting & psychic)
* Perks and status effects, such as the trickster's Dodge ability, can be added or removed manually at any time


## TODO:
* Track turns and initiative orders, plus automatic adding and removal of effects like Nighthowl)
* An "undo" function?
* Pretty "help" screen that lists commands and aliases -- right now it's there but not informative
* Tab-completion when selecting attacks or filling in actor names.