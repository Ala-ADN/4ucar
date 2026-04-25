"""Module-to-professor matching engine.

Score = 0.4·specialization_sim + 0.2·h_index + 0.2·capacity + 0.1·feedback + 0.1·same_inst.
"""


def match_module_to_professor(course_specialization, institution_id, semester, required_hours):
    raise NotImplementedError


def ambassador_eligible(domain):
    raise NotImplementedError


def promotion_eligibility(professor_id):
    raise NotImplementedError
