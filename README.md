# epunfold

A visualizer for epistemic unfolding

## Getting Started

### Prerequisites

Requires python 3.

For outputting images, requires a dot renderer, such as `graphiz`, to be both installed and on your path. Essentially, the following command should work to compile a DOT file to a png image.

```
dot -Tpng graph.dot -o graph.png
```

### Install

Navigate to the `epunfold` folder. First, install the prerequisites given in `requirements.txt`.

```
pip install -r requirements.txt
```

Then, build the `homsearch` dependency using the makefile.

```
make
```

The program, `main.py` should now be able to run using python 3.

### Usage

Review the usage of the program by running it with the help flag, `-h` or `--help`.

```
python3 main.py --help
```

In the `games` folder there are some sample games on which to run the program. The following example performs epistemic unfolding on the high-5 game and saves the results to the directory `unfolded_high5`.

```
python3 main.py games/high5.game -d unfolded_high5
```

After this, the directory `unfolded_high5` will contain the visualizations and corresponding DOT files of the input game and the resultant unfolded game. The contents are as follows.

* `input_game.dot` - The DOT file visualizing the input game
* `input_game.png` - The png image visualizing the input game
* `unfolded_game.dot` - The DOT file visualizing the unfolded game
* `unfolded_game.png` - The png image visualizing the unfolded game
* `models` - A subdirectory containing the png images of each model of the unfolding, required by `unfolded_game.dot`

The DOT files are provided so that they can be modified and recompiled into images. This is useful because the unfolded games in particular often result in messy visualizations before manual intervention. Note that the `models` subdirectory and its contents must be preserved in order to recompile the DOT file of the unfolded game, because this DOT file depends on the images therein.

## Authors

* **Martin Nilsson** - mnil2@kth.se

## Acknowledgments

* **Tomas Gavenciak** - *author of [homsearch](https://github.com/gavento/homsearch/), which is used here with some modification for finding the homomorphic cores of graphs* - gavento@ucw.cz
