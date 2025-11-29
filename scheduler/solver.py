"""Solver module for the Bloom Care scheduling problem."""
from ortools.sat.python import cp_model

from .models import Assignment, Caregiver, Visit
from utils.py import available_for_that_visit

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
    planning = {}
    # Initialisation des variables binaires pour chaque couple, et gestion de la contraine de skill
    for v in visits:
        planning[v.id] = {}
        for c in caregivers:
            # Plutôt que d'initialiser tous les couples V/C possibles, autant n'initialiser que ceux
            # dont les compétences sont ok.
            if v.required_skill in c.skills:
                planning[v.id][c.id] = model.NewBoolVar(f"{v.id}_{c.id}")

    # Gestion de la contrainte de disponibilité
    for v in visits:
        for c_id, var in planning[v.id].items():
            caregiver = next(c for c in caregivers if c.id == c_id)
            available = available_for_that_visit(caregiver, v)
            if not available:
                model.Add(var == 0)

    return []
