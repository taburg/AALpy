from .Vpa import VpaAlphabet
import random
from collections import defaultdict

from aalpy.base import Automaton, AutomatonState


class VcaState(AutomatonState):
    """
    Single state of a VCA.
    """

    def __init__(self, state_id, is_accepting=False):
        super().__init__(state_id)
        self.transitions = defaultdict(list)
        self.is_accepting = is_accepting


class VcaTransition:
    """
    Represents a transition in a VCA.

    Attributes:
        start (VcaState): The starting state of the transition.
        target (VcaState): The target state of the transition.
        symbol: The symbol associated with the transition.
        action: The action performed during the transition (push | pop | None).
    """

    def __init__(self, start: VcaState, target: VcaState, symbol, action):
        self.start = start
        self.target_state = target
        self.letter = symbol
        self.action = action

    def __str__(self):
        return f"{self.letter}: {self.start.state_id} --> {self.target_state.state_id} | {self.action}: {self.stack_guard}"


class Vca(Automaton):
    """
    Visibly Counter Automaton with threshold m.
    """
    error_state = VcaState("ErrorSinkState", False)

    def __init__(self, initial_state: VcaState, states, threshold=0):
        assert threshold == 0, "Only 0-VCA are currently supported!"
        super().__init__(initial_state, states)
        self.initial_state = initial_state
        self.states = states
        self.input_alphabet = self.get_input_alphabet()
        self.current_state = None
        self.counter = 0
        self.m = threshold

        # alphabet sets for faster inclusion checks (as in VpaAlphabet we have lists, for reproducibility)
        self.internal_set = set(self.input_alphabet.internal_alphabet)
        self.call_set = set(self.input_alphabet.call_alphabet)
        self.return_set = set(self.input_alphabet.return_alphabet)

    def reset_to_initial(self):
        self.current_state = self.initial_state
        self.counter = 0

    def step(self, letter):
        """
        Perform a single step on the VCA by transitioning with the given input letter.

        Args:
            letter: A single input that is looked up in the transition table of the VcaState.

        Returns:
            bool: True if the reached state is an accepting state and the counter is zero, False otherwise.
        """
        if self.current_state == Vca.error_state:
            return False

        if letter is None:
            return self.current_state.is_accepting and self.counter == 0

        transitions = self.current_state.transitions[letter]

        taken_transition = None

        # TODO consider updating this to support m-VCAs?
        taken_transition = transitions[0]

        if taken_transition is None:
            self.current_state = Vca.error_state
            return False

        self.current_state = taken_transition.target_state
        if taken_transition.action == 'push':
            self.counter += 1
        elif taken_transition.action == 'pop':
            # zero counter does not allow pop
            if self.counter <= 0:
                self.current_state = Vca.error_state
                return False
            self.counter -= 1

        return self.current_state.is_accepting and self.stack == []

    def to_state_setup(self):
        state_setup_dict = {}

        # ensure prefixes are computed
        # self.compute_prefixes()

        sorted_states = sorted(self.states, key=lambda x: len(x.prefix) if x.prefix is not None else len(self.states))
        for s in sorted_states:
            state_setup_dict[s.state_id] = (
                s.is_accepting, {k: (v.target_state.state_id, v.action) for k, v in s.transitions.items()})

        return state_setup_dict

    def get_input_alphabet(self) -> VpaAlphabet:
        int_alphabet, ret_alphabet, call_alphabet = [], [], []
        for state in self.states:
            for transition_list in state.transitions.values():
                for transition in transition_list:
                    if transition.action == 'pop':
                        if transition.letter not in ret_alphabet:
                            ret_alphabet.append(transition.letter)
                    elif transition.action == 'push':
                        if transition.letter not in call_alphabet:
                            call_alphabet.append(transition.letter)
                    elif transition.letter not in int_alphabet:
                        int_alphabet.append(transition.letter)

        return VpaAlphabet(int_alphabet, call_alphabet, ret_alphabet)

    def is_input_complete(self) -> bool:
        """
        Check whether all states have defined transition for all inputs
        :return: true if automaton is input complete

        Returns:

            True if input complete, False otherwise

        """
        alphabet = set(self.get_input_alphabet().get_merged_alphabet())
        for state in self.states:
            if set(state.transitions.keys()) != alphabet:
                return False
        return True

    # TODO implement this for VCA!
    @staticmethod
    def from_state_setup(state_setup: dict, **kwargs):
        pass
    #     """
    #     Create a VPA from a state setup.

    #     Example state setup:
    #         state_setup = {
    #             "q0": (False, {"(": [("q1", 'push', "(")],
    #                            "[": [("q1", 'push', "[")],  # exclude empty seq
    #                            }),
    #             "q1": (False, {"(": [("q1", 'push', "(")],
    #                            "[": [("q1", 'push', "[")],
    #                            ")": [("q2", 'pop', "(")],
    #                            "]": [("q2", 'pop', "[")]}),
    #             "q2": (True, {
    #                 ")": [("q2", 'pop', "(")],
    #                 "]": [("q2", 'pop', "[")]
    #             }),

    #         Args:
    #             state_setup (dict): A dictionary mapping from state IDs to tuples containing
    #                 (is_accepting: bool, transitions_dict: dict), where transitions_dict maps input symbols to
    #                 lists of tuples (target_state_id, action, stack_guard).
    #             init_state_id (str): The state ID for the initial state of the VPA.
    #             input_alphabet (VpaAlphabet): The alphabet for the VPA.

    #         Returns:
    #             Vpa: The constructed Variable Pushdown Automaton.
    #         """
    #     # state_setup should map from state_id to tuple(is_accepting and transitions_dict)

    #     init_state_id = kwargs['init_state_id']

    #     # build states with state_id and output
    #     states = {key: VpaState(key, val[0]) for key, val in state_setup.items()}
    #     states[Vpa.error_state.state_id] = Vpa.error_state  # PdaState(Pda.error_state,False)
    #     # add transitions to states
    #     for state_id, state in states.items():
    #         if state_id == Vpa.error_state.state_id:
    #             continue
    #         for _input, trans_spec in state_setup[state_id][1].items():
    #             for (target_state_id, action, stack_guard) in trans_spec:
    #                 trans = VpaTransition(start=state, target=states[target_state_id], symbol=_input, action=action,
    #                                       stack_guard=stack_guard)
    #                 state.transitions[_input].append(trans)

    #     init_state = states[init_state_id]
    #     # states to list
    #     states = [state for state in states.values()]

    #     vpa = Vpa(init_state, states)
    #     return vpa

    def is_balanced(self, seq):
        from aalpy.utils import is_balanced
        return is_balanced(seq, self.input_alphabet)

    def generate_random_accepting_word(self, min_steps=4, max_steps=20):
        """
        Generate a random valid sequence for a given VCA.

        Args:

            min_steps : Minimum number of steps
            max_steps : Maximum number of steps before the process terminates

        Returns:
            list: A list of input symbols (the generated sequence) leading to an accepting state.
        """

        sequence = []
        self.reset_to_initial()

        for step_count in range(max_steps):
            current_state = self.current_state

            # If we have met the min_steps requirement and are in an accepting state with counter zero, stop
            if step_count >= min_steps and current_state.is_accepting and self.counter == 0:
                return sequence

            # Get all possible transitions from the current state
            possible_transitions = []
            for letter, transitions in current_state.transitions.items():
                for t in transitions:
                    if t.action == 'pop' and self.counter > 0:
                        possible_transitions.append(t)
                    elif t.action == 'push' or t.action is None:
                        possible_transitions.append(t)

            # If no valid transitions exist, return an incomplete sequence or error
            if not possible_transitions:
                break

            # Randomly choose a valid transition
            chosen_transition = random.choice(possible_transitions)

            # Perform the transition
            self.step(chosen_transition.letter)

            # Add the chosen letter to the sequence
            sequence.append(chosen_transition.letter)

        # None indicates that a sequance was not successfully generated
        return None


def vca_from_dfa_representation(dfa_repr, vpa_alphabet):
    vca_states = dict()
    for dfa_state in dfa_repr.states:
        vca_state = VcaState(state_id=dfa_state.state_id, is_accepting=dfa_state.is_accepting)
        vca_states[dfa_state.state_id] = vca_state

    for dfa_state in dfa_repr.states:
        for input_symbol, reached_dfa_state in dfa_state.transitions.items():
            origin_state = vca_states[dfa_state.state_id]
            reached_state = vca_states[reached_dfa_state.state_id]

            # TODO this could be a long and ugly one-liner
            if input_symbol in vpa_alphabet.call_alphabet:
                transition = VcaTransition(origin_state, reached_state, input_symbol, 'push')
            if input_symbol in vpa_alphabet.return_alphabet:
                transition = VcaTransition(origin_state, reached_state, input_symbol, 'pop')
            if input_symbol in vpa_alphabet.internal_alphabet:
                transition = VcaTransition(origin_state, reached_state, input_symbol, None)

            origin_state.transitions[input_symbol].append(transition)

    initial_state = vca_states[dfa_repr.initial_state.state_id]
    learned_model = Vca(initial_state, list(vca_states.values()))

    return learned_model


def vpa_from_vca_representation(vca_repr, stack_symbol='$'):
    assert vca_repr.m == 0, "Only 0-VCA are currently supported!"

    vpa_states = dict()
    for vca_state in vca_repr.states:
        vpa_state = VcaState(state_id=vca_state.state_id, is_accepting=vca_state.is_accepting)
        vpa_states[dfa_state.state_id] = vpa_state

    for vca_state in vca_repr.states:
        for input_symbol, reached_vca_state in vca_state.transitions.items():
            origin_state = vpa_states[vca_state.state_id]
            reached_state = vpa_states[reached_vca_state.state_id]

            # TODO this could be a long and ugly one-liner
            if input_symbol in vca_repr.input_alphabet.call_alphabet:
                transition = VpaTransition(origin_state, reached_state, input_symbol, 'push', stack_symbol)
            if input_symbol in vca_repr.input_alphabet.return_alphabet:
                transition = VpaTransition(origin_state, reached_state, input_symbol, 'pop', stack_symbol)
            if input_symbol in vca_repr.input_alphabet.internal_alphabet:
                transition = VpaTransition(origin_state, reached_state, input_symbol, None)

            origin_state.transitions[input_symbol].append(transition)

    initial_state = vpa_states[vca_repr.initial_state.state_id]
    learned_model = Vpa(initial_state, list(vca_states.values()))

    return learned_model
