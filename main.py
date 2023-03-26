"""Perform epistemic unfolding up to homomorphic cores on a game."""
from argparse import ArgumentParser
from collections import defaultdict, deque
from contextlib import contextmanager
import itertools
import math
import os
from subprocess import check_call

import pydot

import distgame
from epmodel import EpistemicModel


def main():
    """Perform epistemic unfolding up to homomorphic cores on a game."""
    args = _parse_cli_args()
    game = distgame.load_game(args.file)
    if args.verbose:
        print("Game successfully loaded.")

    dirpath = args.output_dir
    os.makedirs(dirpath, exist_ok=True)
    game.to_pydot().write_raw(os.path.join(dirpath, "input_game.dot"))
    game.to_pydot().write_png(os.path.join(dirpath, "input_game.png"))
    if args.verbose:
        print("Input game successfully visualized.")
        print("Starting epistemic unfolding...")

    unfold_fully(game, dirpath, verbose=args.verbose, find_core=not args.skip_core)
    with _cd(dirpath):
        check_call(["dot", "-Tpng", "unfolded_game.dot", "-o", "unfolded_game.png"])


def _parse_cli_args():
    argparser = ArgumentParser(
        description="Visualize a game and its epistemic unfolding with both DOT files"
        "and png images."
    )
    argparser.add_argument("file", help="the filepath of the game to unfold")
    argparser.add_argument(
        "-d",
        "--dir",
        dest="output_dir",
        default="main",
        metavar="DIR",
        help='write the results to DIR (defaults to "main")',
    )
    argparser.add_argument(
        "-v",
        "--verbose",
        dest="verbose",
        default=False,
        action="store_true",
        help="print the encountered models of the unfolding",
    )
    argparser.add_argument(
        "-c",
        "--skip-core",
        dest="skip_core",
        default=False,
        action="store_true",
        help="skip finding the homomorphic core of the unfolded game (generally produces unwieldy games)",
    )
    return argparser.parse_args()


def unfold_fully(game, dirpath, verbose=False, find_core=True):
    """Fully epistemically unfold the game and save its DOT visualization to file."""
    init_model = EpistemicModel(game)
    if verbose:
        print("initial model:")
        init_model.print()

    locations = [init_model]
    transitions = defaultdict(list)

    todo = deque([(init_model, 0)])
    while len(todo) != 0:
        model, model_i = todo.popleft()
        successors = model.unfold(find_core)
        if verbose:
            _print_model_dequeue(model, successors)
        for next, action_list in successors:
            if verbose:
                _print_successor_model(next, action_list)
            iso_i = None
            for prev_i in range(len(locations)):
                if next.is_isomorphic(locations[prev_i]):
                    if verbose:
                        _print_model_repetition(locations[prev_i])
                    iso_i = prev_i
                    break
            if iso_i is None:
                locations.append(next)
                next_i = len(locations) - 1
                transitions[model_i, next_i].extend(action_list)
                todo.append((next, next_i))
            else:
                transitions[model_i, iso_i].extend(action_list)
    return _game_to_dot(locations, 0, transitions, dirpath)


def _print_model_dequeue(model, successors):
    print()
    print()
    print("=" * 79)
    print("=" * 79)
    print("=" * 79)
    print("considering new model:")
    model.print()
    print(">" * 79)
    print("UNFOLDED TO", len(successors), "SUCCESSORS:")


def _print_successor_model(model, action_list):
    print("=" * 40)
    print("STRATEGIES:")
    print(action_list)
    model.print()


def _print_model_repetition(model):
    print("MODEL REPETITION: Done unfolding the above model as it is isomorphic to:")
    model.print()


def _game_to_dot(locations, initial_location_index, transitions, dirpath):
    """Dump a DOT graph of a game from just locations and transitions."""
    graph = pydot.Dot(graph_type="digraph")
    model_dirname = "models"
    os.makedirs(os.path.join(dirpath, model_dirname), exist_ok=True)
    for loc_i in range(len(locations)):
        img_path_rel = os.path.join(model_dirname, "model" + str(loc_i) + ".png")
        img_path = os.path.join(dirpath, img_path_rel)
        graph.add_node(pydot.Node(loc_i, label="", shape="box", image=img_path_rel))
        _model_to_dot(locations[loc_i], img_path)
    out_cnt = defaultdict(int)
    for from_i, _ in transitions:
        out_cnt[from_i] += 1
    for (from_i, to_i), actions_list in transitions.items():
        if out_cnt[from_i] == 1:
            actions_label = "⊥"
        else:
            action_strs = sorted(
                [
                    "|".join("(" + ",".join(action) + ")" for action in actions)
                    for actions in actions_list
                ]
            )
            actions_label = action_strs[0]
            for i in range(1, len(action_strs)):
                actions_label += ","
                sqrt = math.ceil(math.sqrt(len(action_strs)))
                if i % sqrt == 0:
                    actions_label += "\n"
                else:
                    actions_label += " "
                actions_label += action_strs[i]
        graph.add_edge(pydot.Edge(from_i, to_i, label=actions_label))
    graph.add_node(pydot.Node("hidden_initial", shape="none", label=""))
    graph.add_edge(pydot.Edge("hidden_initial", initial_location_index))
    graph.write_raw(os.path.join(dirpath, "unfolded_game.dot"))


def _model_to_dot(model, filepath):
    graph = pydot.Dot(graph_type="graph")
    for i in range(len(model._last_states)):
        last_state_name = model._game._state_names[model._last_states[i]]
        graph.add_node(pydot.Node(i, label=last_state_name))
    styles = itertools.cycle(("dashed", "dotted", "bold"))
    colors = itertools.cycle(("red", "blue", "darkgreen", "purple4"))
    for indist_graph, style, color in zip(model._indist_graphs, styles, colors):
        for (u, v) in indist_graph.edges:
            if u == v:
                continue
            graph.add_edge(pydot.Edge(u, v, style=style, color=color))
    graph.write_png(filepath)


@contextmanager
def _cd(newdir):
    prevdir = os.getcwd()
    os.chdir(os.path.expanduser(newdir))
    try:
        yield
    finally:
        os.chdir(prevdir)


if __name__ == "__main__":
    main()
