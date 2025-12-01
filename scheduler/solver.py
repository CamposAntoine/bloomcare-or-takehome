"""Solver module for the Bloom Care scheduling problem."""
from ortools.sat.python import cp_model

from .bonus_objectives import compute_continuity_penalty, compute_travel_penalty
from .constraints import (
    add_availibility,
    add_max_hours,
    add_non_overlapping,
    variables_init,
)
from .models import Assignment, Caregiver, Visit


def solve(visits: list[Visit], caregivers: list[Caregiver]) -> list[Assignment]:
    """
    Solve the scheduling problem.

    Args:
        visits: List of visits to be assigned
        caregivers: List of available caregivers

    Returns:
        List of Assignment objects representing which caregiver
          is assigned to which visit
    """
    model = cp_model.CpModel()
    planning: dict[str, dict[str, bool]] = {}

    # Initialisation of binary variables for each pair => skill constraint
    planning = variables_init(visits, planning, caregivers, model)

    # Managing availability constraints
    planning = add_availibility(visits, planning, caregivers, model)

    # Management of non-overlap constraints
    planning = add_non_overlapping(visits, planning, caregivers, model)

    # Managing the max_hours constraint
    planning = add_max_hours(visits, planning, caregivers, model)

    # There is only one caregiver per visit:
    for v in visits:
        model.Add(sum(var for var in planning[v.id].values()) <= 1)

    # Bonus objective: penalise a high number of different caregivers per patient
    continuity_penalty = compute_continuity_penalty(visits, planning, model)

    # Bonus objective: penalise two consecutive visits in two different neighbourhoods.
    travel_penalty = compute_travel_penalty(visits, planning, caregivers, model)

    # Model objective: maximise the number of visits made:
    # (and minimise travel and the number of different caregivers per patient)
    model.Maximize(
        sum(var for v in visits for var in planning[v.id].values())
        - 0.5 * continuity_penalty
        - 0.2 * travel_penalty
    )
    # Without any coefficient, I'd have a violation of unassigned visits.
    # I arbitrarily choose 0.5 and => no violations
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    assignments = []

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        for v in visits:
            for c_id, var in planning[v.id].items():
                if solver.BooleanValue(var):
                    assignments.append(Assignment(visit_id=v.id, caregiver_id=c_id))
    else:
        print("⚠️ No solution found!")

    return assignments
