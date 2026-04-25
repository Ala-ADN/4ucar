"""Project-to-institution matching engine.

Hard filter on KPI thresholds, then score:
0.35·spec_match + 0.25·kpi + 0.20·past_success + 0.10·capacity + 0.10·geo.
"""


def match_project(project_requirements):
    raise NotImplementedError
