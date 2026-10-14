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
        # TODO unify this with the dot +1/-1 representation
        return f"{self.letter}: {self.start.state_id} --> {self.target_state.state_id} | {self.action}"


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

        return self.current_state.is_accepting and self.counter == 0

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
        # FIXME should this be VPA state, not VCA state?
        vpa_state = VcaState(state_id=vca_state.state_id, is_accepting=vca_state.is_accepting)
        vpa_states[dfa_state.state_id] = vpa_state

    for vca_state in vca_repr.states:
        for input_symbol, reached_vca_state in vca_state.transitions.items():
            origin_state = vpa_states[vca_state.state_id]
            # FIXME see complement_vca: this should not work!
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


def complement_vca(vca: Vca) -> Vca:
    """
    Forms the complement of a VCA.
    Importantly, the effect of the stack is not inversed, only the states of the automaton are.
    The original VCA remains intact.
    """

    assert vca.m == 0, "Only 0-VCA are currently supported!"

    # deep copy
    complement_states = {state.state_id: VcaState(state_id=state.state_id, is_accepting=not state.is_accepting) for state in vca.states}
    for state in vca.states:
        for input_symbol, transitions in state.transitions.items():
            origin_state = complement_states[state.state_id]
            reached_state = complement_states[transitions[0].target_state.state_id]

            # TODO this could be a long and ugly one-liner
            if input_symbol in vca.input_alphabet.call_alphabet:
                transition = VcaTransition(origin_state, reached_state, input_symbol, 'push')
            if input_symbol in vca.input_alphabet.return_alphabet:
                transition = VcaTransition(origin_state, reached_state, input_symbol, 'pop')
            if input_symbol in vca.input_alphabet.internal_alphabet:
                transition = VcaTransition(origin_state, reached_state, input_symbol, None)

            origin_state.transitions[input_symbol].append(transition)

    initial_state = complement_states[vca.initial_state.state_id]
    complement = Vca(initial_state, list(complement_states.values()))

    return complement


# TODO overload * operator?
def product_vca(vca1: Vca, vca2: Vca):
    """
    Forms the product of two VCAs.
    A state in the product automaton is accepting if and only if both its original automata states are accepting.
    """

    assert vca1.m == 0, "Only 0-VCA are currently supported!"
    assert vca2.m == 0, "Only 0-VCA are currently supported!"
    assert vca1.call_set == vca2.call_set and vca1.return_set == vca2.return_set and vca1.internal_set == vca2.internal_set, "Both VCAs must have the same alphabet!"

    product_states = {(s1.state_id, s2.state_id): VcaState(state_id=(s1.state_id + "/" + s2.state_id), is_accepting=(s1.is_accepting and s2.is_accepting)) for s1 in vca1.states for s2 in vca2.states}

    for s1 in vca1.states:
        for s2 in vca2.states:
            origin_state = product_states[(s1.state_id, s2.state_id)]
            for input_symbol in s1.transitions:
                if input_symbol not in s2.transitions:
                    continue
                # Assume determinism and avoid adding each transition twice
                if input_symbol in origin_state.transitions:
                    continue
                reached_state = product_states[(s1.transitions[input_symbol][0].target_state.state_id, s2.transitions[input_symbol][0].target_state.state_id)]

                # TODO this could be a long and ugly one-liner
                if input_symbol in vca1.input_alphabet.call_alphabet:
                    transition = VcaTransition(origin_state, reached_state, input_symbol, 'push')
                if input_symbol in vca1.input_alphabet.return_alphabet:
                    transition = VcaTransition(origin_state, reached_state, input_symbol, 'pop')
                if input_symbol in vca1.input_alphabet.internal_alphabet:
                    transition = VcaTransition(origin_state, reached_state, input_symbol, None)

                origin_state.transitions[input_symbol].append(transition)

    # TODO remove non-reachable states?
    initial_state = product_states[(vca1.initial_state.state_id, vca2.initial_state.state_id)]
    product = Vca(initial_state, list(product_states.values()))

    return product


# TODO implement this for VPA, too - it's the same algorithm
def is_language_empty(vca: Vca) -> bool:
    """
    Computes whether the language the VCA accepts is the empty language.

    Algorithm from: Finkel et al. "A Direct Symbolic Approach to Model Checking Pushdown Systems" (Fig. 1)
    Simplified to only compute epsilon transitions, since only they are needed for emptiness (as opposed to general reachability).
    Emptiness is the case when no final state is reachable from the initial state via an epsilon-stack transition.
    """

    states = {q.state_id: q for q in vca.states}
    stack = [(q, q) for q in states]
    hash = set()

    # c_direct = {(q1, q2): [] for q1 in states for q2 in states}
    # c_trans = {(q1, q2): [] for q1 in states for q2 in states}

    # for q1 in states.values():
    #     for t_plus in q1.transitions.values():
    #         t_plus = t_plus[0]  # unpack list
    #         if t_plus.action != 'push':
    #             continue
    #         for q2 in states.values():
    #             for t_minus in q2.transitions.values():
    #                 t_minus = t_minus[0]  # unpack list
    #                 if t_minus.action != 'pop':
    #                     continue
    #                 c_direct[(t_plus.target_state.state_id, t_minus.start.state_id)].append((t_plus.start.state_id, t_minus.target_state.state_id))

    # for q1 in states:
    #     for q2 in states:
    #         if q1 == q2:
    #             continue
    #         for t in states:
    #             c_trans[(q1, q2)].append(((q2, t), (q1, t)))
    #             c_trans[(q1, q2)].append(((t, q1), (t, q2)))

    while stack:
        alpha = stack.pop()
        hash.add(alpha)
        # stack.extend(c_direct[alpha])
        # c_direct[alpha] = []  # c_direct contents are transferred to stack
        # Compute c_direct on the fly
        for q1 in states.values():
            for t_plus in q1.transitions.values():
                t_plus = t_plus[0]  # unpack list
                if t_plus.action != 'push' or t_plus.target_state.state_id != alpha[0]:
                    continue
                for q2 in states.values():
                    for t_minus in q2.transitions.values():
                        t_minus = t_minus[0]  # unpack list
                        if t_minus.action != 'pop' or t_minus.start.state_id != alpha[1]:
                            continue
                        c_direct_transition = (t_plus.start.state_id, t_minus.target_state.state_id)
                        if c_direct_transition not in hash and c_direct_transition not in stack:
                            stack.append(c_direct_transition)
        # Compute c_trans pending transitions in c_direct on the fly
        # TODO merge with below?
        for former_alpha in hash:
            if former_alpha == alpha:
                continue
            for t in states:
                gamma, beta = (former_alpha[1], t), (former_alpha[0], t)
                if gamma in hash and beta not in hash and beta not in stack:
                    stack.append(beta)
                gamma, beta = (t, former_alpha[0]), (t, former_alpha[1])
                if gamma in hash and beta not in hash and beta not in stack:
                    stack.append(beta)
            
        # Compute c_trans[alpha] on the fly
        for t in states:
            gamma, beta = (alpha[1], t), (alpha[0], t)
            gamma, beta = (t, alpha[0]), (t, alpha[1])
            if gamma in hash and beta not in hash and beta not in stack:
                stack.append(beta)

    # Check for emptiness
    epsilon_stack_transitions = list(hash)
    accepting_transitions = [t for t in epsilon_stack_transitions if t[0] == vca.initial_state.state_id and states[t[1]].is_accepting]
    return len(accepting_transitions) == 0


# TODO overload == operator in __eq__?
def is_equal(vca1: Vca, vca2: Vca) -> bool:
    # Use this order to minimize the number of large (product) automata in use at the same time
    vca2_compl = complement_vca(vca2)
    vca1_x_vca2compl = product_vca(vca1, vca2_compl)
    vca1_subseteq_vca2 = is_language_empty(vca1_x_vca2compl)

    # Unbind names to decrease reference count in hope of collection before next huge product automaton comes...
    del vca1_x_vca2compl
    del vca2_compl

    vca1_compl = complement_vca(vca1)
    vca2_x_vca1compl = product_vca(vca1_compl, vca2)
    vca2_subseteq_vca1 = is_language_empty(vca2_x_vca1compl)

    return vca1_subseteq_vca2 and vca2_subseteq_vca1
