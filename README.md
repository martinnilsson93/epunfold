# epunfold

A visualizer for epistemic unfolding

## Getting Started

### Prerequisites

Requires python 3.

For outputting images, requires a dot renderer, such as `graphiz`, to be both installed and on your path. Essentially, the following command should work to compile a DOT file to a png image.

```
dot -Tpng graph.dot -o graph.png
```

### Quickstart

Install via

```
pip install <path to epunfold project folder>
```

Use via

```
epunfold <input game file> -d <output folder>
```

### Detailed installation

It is recommended to install the tool conveniently as a pip package, according to alternative 1. Then, the tool may be run from anywhere via `epunfold` or `python3 -m epunfold` on the command line. But if there are technical difficulties, alternative 2 describes how to install and run the tool more manually.

#### Alternative 1

```
pip install <path to epunfold project folder>
```

This installs the tool as a pip package, `epunfold`, ready to run either via `epunfold` or via `python3 -m epunfold`. Also compatible with pipx.

#### Alternative 2

First, navigate to the `epunfold` project folder. After installing the dependencies and building the extension, the tool should be ready to run from this folder via `python3 -m epunfold`.

##### Install dependencies

Install the dependencies given in `requirements.txt` with the following command.

```
pip install -r requirements.txt
```

##### Build extension

```
python3 setup.py build_ext --inplace
```

Building the extension - `epunfold.homsearch.homsearch_interface` - is only transitively required because of the `homsearch` submodule, which comprises a Cython extension. Unfortunately, building extensions may prove an extreme headache on some setups. It is therefore possible to skip this step, but still run the program, by disabling finding the homomorphic core of the resultant game, by passing `--skip-core` or `-c`. This typically results in prohibitively unwieldy games, but nonetheless finds the complete epistemic unfolding of the input game without having to compile anything.

### Detailed usage

If installed as a pip package (alt 1), the program may be run using `epunfold` or `python3 -m epunfold`. If not (alt 2), the program may be run only using `python3 -m epunfold` from the project folder. Review the usage of the program by running it with the help flag, `-h` or `--help`.

```
epunfold --help
```

In the `games` folder there are some sample games on which to run the program. The following example performs epistemic unfolding on the high-5 game and saves the results to the directory `unfolded_high5`.

```
epunfold games/high5.game -d unfolded_high5
```

After this, the directory `unfolded_high5` will contain the visualizations and corresponding DOT files of the input game and the resultant unfolded game. The contents are as follows.

* `input_game.dot` - The DOT file visualizing the input game
* `input_game.png` - The png image visualizing the input game
* `unfolded_game.dot` - The DOT file visualizing the unfolded game
* `unfolded_game.png` - The png image visualizing the unfolded game
* `models` - A subdirectory containing the png images of each model of the unfolding, required by `unfolded_game.dot`

The DOT files are provided so that they can be modified and recompiled into images. This is useful because the unfolded games in particular often result in messy visualizations before manual intervention. Note that the `models` subdirectory and its contents must be preserved in order to recompile the DOT file of the unfolded game, because this DOT file depends on the images therein.

## Game format

Use the games in the `games` folder as templates or examples of the format expected by the program.

### Sections

* The `Alphabet:` section labels the actions of each agent, as one comma-separated line of strings per agent. For example, `'raise', 'call', 'fold'`, although it is generally recommended for readability to use abbrevations here

* The `Base states:` section names and labels each state of the graph, as one line per state: `<ID>`=`<NAME>`. For example, `0='Start'`

* The initial state section defines the initial state by id: `Initial State: <STATE_ID>`. For example, `Initial State: 0`

* The `Observations:` section defines, for each agent, the indistinguishability relation over the states. That is, the equivalence relation such that two states are equivalent iff the agent cannot distinguish between the two. The format is one `|`-separated line per agent of the equivalence classes. Each equivalence class is a comma-separated list of state ids. For example, `2,1|0|3`, wherein the agent cannot distinguish between states `2´ and `1` in a game of four states

* The `Transitions:` section lists all transitions of the game as `<START_STATE_ID> <JOINT_ACTION_TUPLE> <DESTINATION_STATE_ID>`. That is, given a current state, if the following joint action (action per agent on the same turn) is performed, the following state is reached. Actions are identified by the zero-based index of its order of occurance in the alphabet section, across all agents. For example, in a game with two agents with three actions each, `0 1,3 1` is the transition such that, if the current state is `0`, and the first agent performs its second action and the second agent performs its first action, the game will transition to state `1`

## Authors

* **Martin Nilsson** - mnil2@kth.se

## Acknowledgments

* **Tomas Gavenciak** - *author of [homsearch](https://github.com/gavento/homsearch/), which is used here with some modification for finding the homomorphic cores of graphs* - gavento@ucw.cz
