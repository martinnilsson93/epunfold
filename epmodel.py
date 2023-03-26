"""Comprises an epistemic model class allowing for epistemic unfolding of a game.

Classes:
    EpistemicModel: A model of each player's knowledge of the history of a game.

"""
from collections import defaultdict
from contextlib import contextmanager
import itertools
import sys

import networkx as nx
from networkx.algorithms.components import connected_components


class EpistemicModel:
    """A model describing each player's knowledge of the history of a distributed game.

    The epistemic model comprises all the possible histories of the game so far and an
    indistinguishability relation for each player. There are multiple possible histories
    since the game allows for imperfect information. The indistinguishability relation
    for each player defines which histories are indistinguishable to that player due to
    imperfect sensing. Naturally, each indistinguishability relation is an equivalence
    relation.

    Attributes:
        history_count: Number of histories comprised by the model.
        player_count: Number of players comprised by the model.

    Methods:
        unfold: Return every successor model.
        next: Return the successor models induced by a joint action function.
        core: Return the homomorphic core of the model.
        is_isomorphic: Return whether this model is isomorphic to another.

    """

    def __init__(self, game):
        """Initialize an epistemic model for a game at its initial state.

        This epistemic model consists of only a single element: the singleton history of
        the initial state. Each player knows exactly that they are in the initial state.

        Args:
            game: The DistributedGame instance with which to initialize the model. The
                game is a multiplayer game of imperfect information.
            indist_classes_list: A list defining the indistinguishable states for each
                player. Each list element is a nested container such that each inner
                container defines the set of indices that are indistinguishable.

        """
        self._game = game
        self._last_states = [game.initial_state]
        self._indist_graphs = [nx.Graph() for _ in game.players]
        for indist_graph in self._indist_graphs:
            indist_graph.add_edge(0, 0)

    @property
    def history_count(self):
        """Return the number of histories that this model comprises."""
        return len(self._last_states)

    @property
    def player_count(self):
        """Return the number of players that this model comprises."""
        return len(self._indist_graphs)

    def print(self):
        """Print the model state."""
        print("MODEL {")
        print("  last state per history")
        print("    ", end="")
        print([self._game.state_names[last_state] for last_state in self._last_states])
        print("  indistinguishability relations per player")
        for indist_graph in self._indist_graphs:
            print("    ", end="")
            print(
                list(
                    (
                        self._game.state_names[self._last_states[u]],
                        self._game.state_names[self._last_states[v]],
                    )
                    for u, v in indist_graph.edges
                    if u != v
                )
            )
        print("}")

    def unfold(self, core=True):
        """Return every epistemic successor model.

        Args:
            core: Whether to quotient the successor models to their homomorphic cores.

        Returns:
            The collection of next epistemic models in the unfolding. These are the
            epistemic successor models induced by all the combinations of joint action
            and possible history of the model. (See the method _next_.)

            Note that only those pairs of joint action and history that are compatible
            with the model are considered. This means that if two histories are
            indistinguishable, then they will each map to the same action. This makes
            sense intuitively in that the player has no way of knowing which of the two
            indistinguishable histories is the real one, and so cannot plan to take
            different action.

        """
        compatible_joint_actions = self._compatible_joint_actions()
        joint_actions_by_result = self._joint_actions_by_result(
            compatible_joint_actions
        )

        return list(
            itertools.chain.from_iterable(
                (
                    (next, joint_actions_list)
                    for next in self.next(joint_actions_list[0], core)
                )
                for joint_actions_list in joint_actions_by_result.values()
            )
        )

    def next(self, joint_actions, core=True):
        """Return the epistemic successor models induced by a joint action function.

        Args:
            joint_actions: A sequence mapping every history id to a joint action. The
                history id is the index in the sequence.
            core: Whether to quotient the successor models to their homomorphic cores.

        Returns:
            The collection of next epistemic models in the unfolding for the given joint
            actions. Intuitively, these are the successor models resulting from the
            player coalition agreeing to perform a specific joint action for every
            possible history in the current model.

        """
        new_last_states, successors_list = self._next_histories(joint_actions)
        indist_union = nx.Graph()
        new_indist_graphs = [nx.Graph() for _ in range(self.player_count)]
        for player in range(self.player_count):
            new_graph = new_indist_graphs[player]
            new_graph.add_edges_from(
                self._new_indist_histories(player, new_last_states, successors_list)
            )
            indist_union.add_edges_from(new_graph.edges)
        component_histories_list = list(connected_components(indist_union))

        if len(component_histories_list) == 1:
            next_models = [self._new_model(new_last_states, new_indist_graphs)]
        else:
            next_models = (
                self._new_submodel(
                    component_histories, new_last_states, new_indist_graphs
                )
                for component_histories in component_histories_list
            )
        if core:
            return [model.core() for model in next_models]
        else:
            return list(next_models)

    def core(self):
        """Return the homomorphic core of the model.

        The core of an epistemic model is the homomorphically equivalent model that is
        minimal with regard to the number of histories it comprises. As with graphs,
        this core is unique up to isomorphism.

        Homomorphism for epistemic models is similar as for graphs but more restrictive.
        A model is homomorphic to another only if there exists a graph homomorphism that
        is a homomorphism for each player's indistinguishability graph to that player's
        corresponding graph in the other model. That is, the model homomorphism is a
        homomoprhism for multiple graphs, as many as there are players. Further, the
        homomorphism must only map between pairs of histories that have the same final
        state.

        Returns:
            A new epistemic model based on this one. The model will be the same if the
            given model is already its own core. Otherwise, the indistinguishability
            graphs of the new returned model will each be a proper subgraph of the
            corresponding graph of this model. More precisely, each returned subgraph
            will be a homomorphic retract of its corresponding graph. Each of these
            retracts are induced by the same retraction, the core retraction of the
            model.

            Note the terminology of retract vs retraction. A retract is a
            homomorphically equivalent graph/model, while a retraction is a node mapping
            that induces a retract.

        """
        retraction_gen = (
            _partition_preserving_maps(_retractions(graph), self._last_states)
            for graph in self._indist_graphs
        )
        retraction_intersection = next(retraction_gen)
        for retraction in retraction_gen:
            retraction_intersection = _intersect_lists(
                retraction_intersection, retraction
            )
        core_retraction = max(
            retraction_intersection, key=lambda retraction: len(retraction)
        )
        if len(core_retraction) == 0:  # already a core
            return self
        new_indist_graphs = [
            _retract(graph, core_retraction) for graph in self._indist_graphs
        ]
        return self._new_submodel(
            new_indist_graphs[0].nodes, self._last_states, new_indist_graphs
        )

    def is_isomorphic(self, other_model):
        """Return whether this model is isomorphic to another.

        Analagous to how model homomorphism is defined, two models are isomorphic only
        if there is a morphism that is an isomorphism between the indistinguishability
        graphs of every player, and that preserves the last state of histories. That is,
        a model isomorphism between two histories k and k' requires that the last state
        of k and k' are the same.
        """
        if len(self._last_states) != len(other_model._last_states):
            return False
        if len(self._indist_graphs) != len(other_model._indist_graphs):
            return False
        if sorted(self._last_states) != sorted(other_model._last_states):
            return False

        isomorphism_gen = (
            _partition_preserving_maps(
                _graph_isomorphisms(this_graph, other_graph), self._last_states
            )
            for this_graph, other_graph in zip(
                self._indist_graphs, other_model._indist_graphs
            )
        )
        isomorphism_intersection = next(isomorphism_gen)
        for isomorphism in isomorphism_gen:
            isomorphism_intersection = _intersect_lists(
                isomorphism_intersection, isomorphism
            )
        return len(isomorphism_intersection) > 0

    def _compatible_joint_actions(self):
        """Generate all combinations of compatible joint actions for every history.

        A combination of joint actions for every history is compatible with the model
        if, for every two histories that is indistinguishable to a player, that player's
        action is identical for both histories.
        """
        compatible_actions = (
            self._compatible_actions(player) for player in range(self.player_count)
        )
        compatible_action_combinations = itertools.product(*compatible_actions)
        for joint_actions in itertools.starmap(zip, compatible_action_combinations):
            yield tuple(joint_actions)

    def _compatible_actions(self, player):
        actions = self._game.get_actions(player)
        indist_classes = list(connected_components(self._indist_graphs[player]))
        for class_actions in itertools.product(actions, repeat=len(indist_classes)):
            compatible_actions = dict()
            for indist_class, class_action in zip(indist_classes, class_actions):
                for history in indist_class:
                    compatible_actions[history] = class_action
            yield tuple(compatible_actions[i] for i in range(len(compatible_actions)))

    def _joint_actions_by_result(self, joint_actions_list):
        """Map joint actions to the successor states they induce for the model.

        The returned dictionary contains as keys all the possible successor state
        arrangements given the list of joint action mappings. The values will each be a
        list of all the joint action mappings that induced that result. Note that each
        joint action mapping induces a unique result, and will therefore occur exactly
        once in the dictionary.
        """
        joint_actions_by_result = defaultdict(list)
        for joint_actions in joint_actions_list:
            res = tuple(
                self._game[joint_action, state]
                for joint_action, state in zip(joint_actions, self._last_states)
            )
            joint_actions_by_result[res].append(joint_actions)
        return joint_actions_by_result

    def _next_histories(self, joint_actions):
        """Return the successor histories given a joint action for each history."""
        new_last_states = []
        history_successors_list = []
        for last_state, joint_action in zip(self._last_states, joint_actions):
            successor_histories = set()
            for successor_state in self._game[joint_action, last_state]:
                new_history_id = len(new_last_states)
                new_last_states.append(successor_state)
                successor_histories.add(new_history_id)
            history_successors_list.append(successor_histories)
        return new_last_states, history_successors_list

    def _new_indist_histories(self, player, new_last_states, successors_list):
        """Generate every pair of indistinguishabile histories for the new model."""
        old_graph = self._indist_graphs[player]
        for old_hist_1, old_hist_2 in old_graph.edges:
            for new_hist_1, new_hist_2 in itertools.product(
                successors_list[old_hist_1], successors_list[old_hist_2]
            ):
                last_state_1 = new_last_states[new_hist_1]
                last_state_2 = new_last_states[new_hist_2]
                if not self._game.are_distinguishable(
                    player, last_state_1, last_state_2
                ):
                    yield new_hist_1, new_hist_2

    def _new_model(self, last_states, indist_graphs):
        """Given a complete model state, return a new model over the same game."""
        model = EpistemicModel(self._game)
        model._last_states = last_states
        model._indist_graphs = indist_graphs
        return model

    def _new_submodel(self, histories, last_states, indist_graphs):
        """Return the submodel induced by a history subset."""
        subgraphs = [graph.subgraph(histories) for graph in indist_graphs]
        subgraphs = [
            nx.convert_node_labels_to_integers(subgraph, label_attribute="old_label")
            for subgraph in subgraphs
        ]
        sub_last_states = [None for _ in range(len(histories))]
        for history in subgraphs[0].nodes:
            sub_last_states[history] = last_states[
                subgraphs[0].nodes[history]["old_label"]
            ]
        return self._new_model(sub_last_states, subgraphs)


def _retract(graph, retraction):
    """Return the retract defined by applying the retraction to the graph."""
    return nx.relabel_nodes(graph, retraction, copy=True)


def _partition_preserving_maps(maps, partition):
    """Return a sublist of only the maps that preserve the partition.

    A map _f_ preserves _partition_ if _partition[x] == partition[f[x]]_ for all _f[x]_.
    """
    return [
        f for f in maps if all(partition[x] == partition[fx] for x, fx in f.items())
    ]


def _retractions(graph):
    """Return the retractions of a graph."""
    # path hack to fix importing from subfolder: otherwise transitive imports break...
    with _add_path("./homsearch"):
        try:
            import homsearch.homsearch
        except ImportError:
            print('ERROR: could not import the homsearch extension. it is likely that the extension was not built properly', file=sys.stderr)
            raise
    return [
        {k: v for (k, v) in retraction.items() if k != v}
        for retraction in homsearch.homsearch.find_retracts(graph)
    ]


def _graph_isomorphisms(graph1, graph2):
    """Return the isomorphisms between two graphs."""
    graphMatcher = nx.algorithms.isomorphism.GraphMatcher(graph1, graph2)
    return (
        {k: v for (k, v) in isomorphism.items() if k != v}
        for isomorphism in graphMatcher.isomorphisms_iter()
    )


def _intersect_lists(list1, list2):
    """Return the intersection of two lists."""
    return [e for e in list1 if e in list2]


def _is_partition(classes, elements):
    """Return whether the nested container _classes_ partitions _elements_."""
    classed_elements = set()
    for class_ in classes:
        for element in class_:
            if element in classed_elements:
                return False
            classed_elements.add(element)
    elements = set(elements)
    return all(classed_element in elements for classed_element in classed_elements)

@contextmanager
def _add_path(dir):
    sys.path.append(dir)
    try:
        yield
    finally:
        try:
            sys.path.remove(dir)
        except ValueError:
            pass
