"""Comprises a class defining a multiplayer game of imperfect information.

Classes:
    DistributedGame: A multiplayer game of imperfect information.

Functions:
    load_game: Return a multiplayer game of imperfect information from file.

"""
from collections import defaultdict
import itertools
import math
from string import whitespace

import networkx as nx
import pydot


class DistributedGame:
    """A distributed game, ie. a multiplayer game of imperfect information.

    The imperfect information is modeled as an equivalence relation for each player
    such that any two states in the same equivalance class are indistinguishable to
    that player. These classes are denoted as indistinguishability classes.

    Since there are multiple players, a single move is decided by the joint actions of
    the entire coalation of players. A joint action is a tuple of the actions of every
    player.

    Note that the game may be non-deterministic. This is modeled by allowing a single
    move to lead to multiple successor states.

    Attributes:
        states: All state ids.
        state_names: All state names.
        inital_state: The initial state id.
        players: All player ids.
        joint_actions: A generator of all joint actions.

    Methods:
        __setitem__: Set a move, mapping a state and a joint action to successor states.
        __getitem__: Get the successor states mapped from a state and a joint action.
        get_actions: Return all the actions available to a player.
        are_distinguishable: Return whether a player can distinguish between two states.
        to_pydot: Return a pydot graph of the game.

    """

    def __init__(self, state_names, initial_state, actions_list, indist_classes_list):
        """Initialize a multiplayer game of imperfect information.

        Args:
            state_names: A list of all the game state names. The index of a name in this
                list becomes the state id of that name.
            initial_state: The initial game state id.
            actions_list: A list such that each element with index _i_ is a container
                containing all the actions available to player _i_.
            indist_classes_list: A list defining the indistinguishable states for each
                player. Each list element is a nested container such that each inner
                container defines the set of state ids that are indistinguishable. Any
                omitted state id is implicitly placed in a singleton class. That is,
                omitted states are perfectly distinguishable.

        Raises:
            ValueError: Args are internally inconsistent. First, the initial state id
                must be a list index for _state_names_. Second, _actions_list_ and
                _indist_classes_list_ must be of the length. These two lists must be
                the same length because they each contain one element per player.
                Finally, each element of _indist_classes_list_ must partition the list
                indices of _state_names_, except that state ids may be omitted.

        """
        self._state_names = state_names
        self._states = tuple(range(len(self._state_names)))
        if initial_state not in self._states:
            raise ValueError("initial state is not a state id")
        self._initial_state = initial_state

        if len(actions_list) != len(indist_classes_list):
            raise ValueError(
                "actions list and the indist class list are of different lengths"
            )
        self._player_count = len(actions_list)
        self._actions_list = [tuple(set(actions)) for actions in actions_list]
        self._moves = {
            (joint_action, state): (state,)
            for state in self._states
            for joint_action in itertools.product(*actions_list)
        }
        self._indist_graphs = [
            self._indist_graph_from_classes(indist_classes)
            for indist_classes in indist_classes_list
        ]

    def __setitem__(self, key, value):
        """Set a move, mapping a joint action and a state to a set of next states.

        The move map is always total: every pair of joint action and state is mapped to
        a non-empty set of successor states. If a move is not set for some pair of joint
        action and state, the default action becomes a deterministic self loop.

        Args:
            key: A tuple (joint action, state), where the joint action is a tuple or
                list containing in order the action of each player, and the state is the
                state in which the action is performed.
            value: The set of possible successor states resulting from the action. Must
                be a non-empty container of state ids.

        Raises:
            KeyError: Invalid key. One of three things is true. (1) The given state is
                not a valid state id. (2) At least one action in the joint action can't
                be performed by the corresponding player. (3) The joint action is not
                the same length as the number of players.
            ValueError: Invalid value. Value must be a non-empty container of unique
                state ids.

        """
        joint_action, from_state = key
        next_states = value
        self._validate_key(joint_action, from_state)
        self._validate_next_states(next_states)
        self._moves[joint_action, from_state] = tuple(set(next_states))

    def __getitem__(self, key):
        """Get the set of successor states from a joint action and a state.

        The move map is always total: every pair of joint action and state is mapped to
        a non-empty set of successor states. If a move is not set for some pair of joint
        action and state, the default action becomes a deterministic self loop.

        Args:
            key: A tuple (joint action, state), where the joint action is a tuple or
                list containing in order the action of each player, and the state is the
                state in which the action is performed.

        Returns:
            The set of possible successor states given that the player coalition
            collectively perform the given joint action at the given state.

        Raises:
            KeyError: Invalid key. One of three things is true. (1) The given state is
                not a valid state id. (2) At least one action in the joint action can't
                be performed by the corresponding player. (3) The joint action is not
                the same length as the number of players.

        """
        joint_action, from_state = key
        self._validate_key(joint_action, from_state)
        return self._moves[joint_action, from_state]

    @property
    def states(self):
        """Return all the state ids."""
        return self._states

    @property
    def state_names(self):
        """List of all state names."""
        return self._state_names

    @property
    def initial_state(self):
        """Return the initial state."""
        return self._initial_state

    @property
    def players(self):
        """Return all the player ids."""
        return tuple(range(self._player_count))

    @property
    def joint_actions(self):
        """Return a generator of all available joint actions."""
        return (joint_action for joint_action in itertools.product(*self._actions_list))

    def get_actions(self, player):
        """Return all the actions available to a player."""
        return self._actions_list[player]

    def are_distinguishable(self, player, state1, state2):
        """Return whether the player can distinguish the two states."""
        return not self._indist_graphs[player].has_edge(state1, state2)

    def to_pydot(self):
        """Return a pydot graph of the game."""
        graph = pydot.Dot(graph_type="digraph")
        collapsed_moves = defaultdict(list)
        for (action, from_state), to_states in self._moves.items():
            from_name = self._state_names[from_state]
            for to_state in to_states:
                to_name = self._state_names[to_state]
                collapsed_moves[from_name, to_name].append(action)
        out_cnt = defaultdict(int)
        for from_name, _ in collapsed_moves:
            out_cnt[from_name] += 1
        for (from_name, to_name), actions in collapsed_moves.items():
            if out_cnt[from_name] == 1:
                actions_label = "⊥"
            else:
                if self._player_count == 0:
                    action_strs = sorted(action[0] for action in actions)
                else:
                    action_strs = sorted(
                        ["(" + ",".join(action) + ")" for action in actions]
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
            graph.add_edge(pydot.Edge(from_name, to_name, label=actions_label))
        hidden_node = "hidden_initial"
        while hidden_node in self._state_names:
            hidden_node += "_"
        graph.add_node(pydot.Node(hidden_node, shape="none", label=""))
        graph.add_edge(pydot.Edge(hidden_node, self._state_names[self._initial_state]))
        styles = itertools.cycle(("dashed", "dotted", "bold"))
        colors = itertools.cycle(("red", "blue", "darkgreen", "purple4"))
        for indist_graph, style, color in zip(self._indist_graphs, styles, colors):
            for (u, v) in indist_graph.edges:
                if u == v:
                    continue
                u_name = self._state_names[u]
                v_name = self._state_names[v]
                graph.add_edge(
                    pydot.Edge(u_name, v_name, style=style, dir="none", color=color)
                )
        return graph

    def _indist_graph_from_classes(self, indist_classes):
        """Return a graph defining an indistinguishability relation from its classes.

        Note that any state not in any class is implicitly in a singleton class.
        """
        if not _is_partition(indist_classes, self._states):
            raise ValueError(
                "the indistinguishability classes must partition the state ids"
            )
        indist_graph = nx.Graph()
        # add a complete subgraph component for each equivalence class
        for indist_class in indist_classes:
            indist_graph.add_edges_from(itertools.combinations(indist_class, 2))
        indist_graph.add_edges_from((state, state) for state in self._states)
        return indist_graph

    def _validate_key(self, joint_action, state):
        if state not in self._states:
            raise KeyError("invalid state id in key")
        if len(joint_action) != self._player_count:
            raise KeyError("joint action length is not the same as the player count")
        if not all(
            joint_action[i] in self._actions_list[i] for i in range(self._player_count)
        ):
            raise KeyError("some action cant be performed by corresponding player")

    def _validate_next_states(self, next_states):
        if len(next_states) == 0:
            raise ValueError("successor states must be non-empty")
        if not all(state in self._states for state in next_states):
            raise ValueError("some state in value is not a valid state id")
        if len(next_states) != len(set(next_states)):
            raise ValueError("successor states must contain only unique values")


def load_game(filepath):
    """Return a distributed game described by a text file."""
    with open(filepath, "r") as f:
        lines = (line.strip() for line in f)
        actions_table = _read_actions(lines)
        locations = _read_locations(lines)
        initial_location_index = _read_initial_location(lines)
        observations_table = _read_observations(lines)
        transitions = _read_transitions(lines, actions_table)

        game = DistributedGame(
            locations, initial_location_index, actions_table, observations_table
        )
        for key, destination in transitions.items():
            game[key] = tuple(destination)
    return game


def _read_actions(lines):
    """Return the table of actions as described by a sequence of lines."""
    if next(lines, None) is None:
        raise EOFError("Error loading from file. Expected the actions section.")

    actions_table = []
    is_done = False
    while not is_done:
        line = next(lines, None)
        if not line:
            is_done = True
        else:
            actions = [action.strip(whitespace + "'\"") for action in line.split(",")]
            actions_table.append(actions)
    return actions_table


def _read_locations(lines):
    """Return the list of locations as described by a sequence of lines."""
    if next(lines, None) is None:
        raise EOFError("Error loading from file. Expected the locations section.")

    locations = dict()
    is_done = False
    while not is_done:
        line = next(lines, None)
        if not line:
            is_done = True
        else:
            parse = [comp.strip(whitespace + "'\"") for comp in line.split("=")]
            index = int(parse[0])
            name = parse[1]
            locations[index] = name

    for location_index in locations.keys():
        if location_index not in range(len(locations)):
            raise ValueError(
                "Error loading from file. Location indices must range from 0 to n,"
                "where n is the number of locations."
            )
    locations_list = []
    for i in range(len(locations)):
        locations_list.append(locations[i])
    return locations


def _read_initial_location(lines):
    """Return the initial location as described by the next in a sequence of lines."""
    line = next(lines, None)
    if line is None:
        raise EOFError("Error loading from file. Expected the initial location.")
    next(lines, None)

    words = line.split()
    return int(words[len(words) - 1])


def _read_observations(lines):
    """Return the observation partition tables as described by a sequence of lines."""
    if next(lines, None) is None:
        raise EOFError("Error loading from file. Expected the observations section.")

    observations_table = []
    is_done = False
    while not is_done:
        line = next(lines, None)
        if not line:
            is_done = True
        else:
            observations = [
                set(int(l.strip()) for l in part.split(",")) for part in line.split("|")
            ]
            observations_table.append(observations)
    return observations_table


def _read_transitions(lines, actions_table):
    """Return the transitions as described by a sequence of lines."""
    if next(lines, None) is None:
        raise EOFError("Error loading from file. Expected the transitions section.")

    transitions = defaultdict(set)
    is_done = False
    while not is_done:
        line = next(lines, None)
        if not line:
            is_done = True
        else:
            words = [word.strip() for word in line.split()]
            location = int(words[0])
            all_actions = [action for actions in actions_table for action in actions]
            joint_action = tuple(
                all_actions[int(action_index)] for action_index in words[1].split(",")
            )
            destination = int(words[2])
            transitions[joint_action, location].add(destination)
    return transitions


def _is_partition(classes, elements):
    """Return whether the nested container _classes_ partitions _elements_.

    Note that elements may be omitted from the classes. So, eg., this returns True
    for all input where _classes_ is an empty container.
    """
    classed_elements = set()
    for class_ in classes:
        for element in class_:
            if element in classed_elements:
                return False
            classed_elements.add(element)
    elements = set(elements)
    return all(classed_element in elements for classed_element in classed_elements)
