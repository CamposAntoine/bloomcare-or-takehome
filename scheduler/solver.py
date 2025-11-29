"""Solver module for the Bloom Care scheduling problem."""
from ortools.sat.python import cp_model

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
    x = {}
    for v in visits:
        x[v.id] = {}
        for c in caregivers:
            # Plutôt que d'initialiser tous les couples V/C possibles, autant n'initialiser que ceux
            # dont les compétences sont ok.
            if v.required_skill in c.skills:
                x[v.id][c.id] = model.NewBoolVar(f"{v.id}_{c.id}")


    return []
