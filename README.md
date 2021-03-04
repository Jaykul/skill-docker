# opsdroid skill random

A skill for [opsdroid](https://github.com/opsdroid/opsdroid) to perform random events like flipping a coin or rolling a dice.

## Requirements

None.

## Configuration

None.

## Usage

#### `flip a coin`

Flips a coin.

> user: flip a coin
>
> opsdroid: It landed on heads

#### `roll a die`

Rolls a die.

> user: roll a die
>
> opsdroid: You rolled a 4

#### `roll a d20`

Does full DnD-style dice rolls:

> user: roll 3d8+2
>
> opsdroid: You rolled 3d8 (4, 2, 2) + 2 = 10

Even supports "keep highest" (or lowest), minimums, and re-rolls (see [d20](https://github.com/avrae/d20)).
> user: roll 3d20kh1
>
> opsdroid: You rolled 3d20kh1 (15, 14, 11) = 15

### Magic 8 Ball

Picks a random clairvoyant style answer:

> user: magic 8 ball, should I go to bed now?
>
> opsdroid: Without a doubt