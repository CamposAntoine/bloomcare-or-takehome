"""Solver module for the Bloom Care scheduling problem."""
from ortools.sat.python import cp_model
from collections import defaultdict


from .models import Assignment, Caregiver, Visit
from scheduler.utils import available_for_that_visit
from scheduler.utils import visits_overlap

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


    # Il n'y a que un caregiver par visite :
    for v in visits:
        model.Add(
            sum(var for var in planning[v.id].values()) <= 1
        )

    # Objectif bonus : pénaliser un haut nombre de caregivers différents par patiens
    customer_caregiver_vars = {}
    for v in visits:
        customer = v.customer
        if customer not in customer_caregiver_vars:
            customer_caregiver_vars[customer] = {}
        for c_id, var in planning[v.id].items():
            if c_id not in customer_caregiver_vars[customer]:
                customer_caregiver_vars[customer][c_id] = model.NewBoolVar(f"{customer}_{c_id}")
            model.Add(var <= customer_caregiver_vars[customer][c_id])

    # somme que je vais essayer de minimiser pendant le solving
    continuity_penalty = sum(
        customer_caregiver_vars[customer][c_id]
        for customer in customer_caregiver_vars
        for c_id in customer_caregiver_vars[customer]
    )


    # Objectif bonus : pénaliser le fait que un caregiver fasse deux visites d'affilées dans deux quartiers différents
    travel_penalty_vars = []

    for c in caregivers:
        visits_by_day = defaultdict(list)
        for v in visits:
            if c.id in planning[v.id]:
                day = v.start.date()  # juste besoin du jour
                visits_by_day[day].append(v)

        for day_visits in visits_by_day.values():
            # On trie pour ne regarder que les visites consécutives
            day_visits.sort(key=lambda v: v.start)
            for i in range(len(day_visits) - 1):
                v1 = day_visits[i]
                v2 = day_visits[i + 1]

                # On regarde que les paires dans des quartiers différents
                if v1.neighborhood != v2.neighborhood:
                    switch_var = model.NewBoolVar(f"switch_{c.id}_{v1.id}_{v2.id}")
                    # Si switch_var = 1 => les deux visites sont assignées à c
                    model.AddBoolAnd([planning[v1.id][c.id], planning[v2.id][c.id]]).OnlyEnforceIf(switch_var)
                    # Si switch_var = 0 => il enchaine pas les deux visites
                    model.AddBoolOr([planning[v1.id][c.id].Not(), planning[v2.id][c.id].Not()]).OnlyEnforceIf(switch_var.Not())
                    
                    travel_penalty_vars.append(switch_var)

    travel_penalty = sum(travel_penalty_vars)

    # Objectif du modèle : maximiser le nombres de visites effectuées :
    # (et maintenant minimiser le trajet, et les caregivers différents par patients)
    model.Maximize(
        sum(var for v in visits for var in planning[v.id].values())
        - 0.5*continuity_penalty
        - 0.2*travel_penalty
    ) # Sans coeffictient j'ai une violation de visites non assignées
      # je choisis 0.5 arbitrairement et ça fonctionne : chaque patient ne voit que un soignant et 0 violation

    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    assignments = []

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        for v in visits:
            for c_id, var in planning[v.id].items():
                if solver.BooleanValue(var):
                    assignments.append(Assignment(visit_id=v.id, caregiver_id=c_id))
    else:
        print("⚠️ Aucune solution trouvée !")

    return assignments

