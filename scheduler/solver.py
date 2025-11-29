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


    # Gestion de la contrainte de non-chevauchement
    for c in caregivers:
        # Récupérer toutes les visites possibles pour ce soignant sous forme de liste d'objets Visit
        caregiver_visits = [v for v in visits if c.id in planning[v.id]]
        
        # Pour toutes les paires de visites
        for i in range(len(caregiver_visits)):
            for j in range(i + 1, len(caregiver_visits)):
                v1 = caregiver_visits[i]
                v2 = caregiver_visits[j]
                if visits_overlap(v1, v2):
                    # Si chevauchement on ajoute la contrainte
                    model.Add(planning[v1.id][c.id] + planning[v2.id][c.id] <= 1)


    # Gestion de la contraine max_hours
    for c in caregivers:
        caregiver_visits = [v for v in visits if c.id in planning[v.id]]
        if not caregiver_visits:
            continue

        vars_list = []
        durations = []

        for v in caregiver_visits:
            duration_hours = (v.end - v.start).seconds // 3600  
            durations.append(duration_hours)
            vars_list.append(planning[v.id][c.id])

        model.Add(sum(d * var for d, var in zip(durations, vars_list)) <= c.max_hours)



    # Note à moi-même, je devrai faire attention à l'inverse à la fin : que une visite ne puisse pas être faites par deux soignants

    return []
