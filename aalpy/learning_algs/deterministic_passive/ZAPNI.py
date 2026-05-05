from aalpy.utils import is_balanced
from aalpy.automata.Vca import vca_from_dfa_representation

def run_ZAPNI(data, vpa_alphabet, algorithm='edsm', print_info=True):
    """
    Run ZAPNI, a deterministic passive model learning algorithm for deterministic visibly counter automata.
    The resulting model conforms to the provided data, and is minimal if the characteristic set was present.

    Args:

        data: sequence of input sequences and corresponding label. Eg. [[(i1,i2,i3, ...), label], ...]
        vpa_alphabet:  grouping of alphabet elements to call symbols, return symbols, and internal symbols. Call symbols
        increment the counter, return symbols decrement it, and internal symbols do not affect the counter.
        algorithm: either 'classic' or 'gsm' for classic RPNI or 'edsm' for evidence driven state merging
        print_info: print learning progress and runtime information

    Returns:

        VCA conforming to the data, or None if data is non-deterministic.
    """
    from aalpy.learning_algs import run_EDSM, run_RPNI
    assert algorithm in {'gsm', 'classic', 'edsm'}

    # preprocess input sequences to keep track of counter
    zapni_data = [word for word in data if is_balanced(word[0], vpa_alphabet)]

    # instantiate and run ZAPNI as base RPNI on filtered data
    if algorithm != 'edsm':
        learned_model = run_RPNI(zapni_data, automaton_type='dfa', algorithm=algorithm, print_info=print_info)
    else:
        learned_model = run_EDSM(zapni_data, automaton_type='dfa', print_info=print_info)

    # convert intermediate DFA representation to VPA
    learned_model = vca_from_dfa_representation(learned_model, vpa_alphabet)

    return learned_model

