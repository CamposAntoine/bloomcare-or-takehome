from ortools.sat.python import cp_model

from scheduler.utils import available_for_that_visit, visits_overlap

from .models import Caregiver, Visit


def variables_init(
    visits: list[Visit],
    planning: dict,
    caregivers: list[Caregiver],
    model: cp_model.CpModel,
) -> dict:
    for v in visits:
        planning[v.id] = {}
        for c in caregivers:
            # Rather than initialising all possible V/C pairs,
            # it is better to initialise only those, whose skills are acceptable.
            if v.required_skill in c.skills:
                planning[v.id][c.id] = model.NewBoolVar(f"{v.id}_{c.id}")
    return planning


def add_availibility(
    visits: list[Visit],
    planning: dict,
    caregivers: list[Caregiver],
    model: cp_model.CpModel,
) -> dict:
    for v in visits:
        for c_id, var in planning[v.id].items():
            caregiver = next(c for c in caregivers if c.id == c_id)
            available = available_for_that_visit(caregiver, v)
            if not available:
                model.Add(var == 0)
    return planning


def add_non_overlapping(
    visits: list[Visit],
    planning: dict,
    caregivers: list[Caregiver],
    model: cp_model.CpModel,
) -> dict:
    for c in caregivers:
        # Retrieve all possible visits for this caregiver
        caregiver_visits = [v for v in visits if c.id in planning[v.id]]

        # For all pairs of visits
        for i in range(len(caregiver_visits)):
            for j in range(i + 1, len(caregiver_visits)):
                v1 = caregiver_visits[i]
                v2 = caregiver_visits[j]
                if visits_overlap(v1, v2):
                    # Si chevauchement on ajoute la contrainte
                    model.Add(planning[v1.id][c.id] + planning[v2.id][c.id] <= 1)
    return planning


def add_max_hours(
    visits: list[Visit],
    planning: dict,
    caregivers: list[Caregiver],
    model: cp_model.CpModel,
) -> dict:
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

        model.Add(
            sum(d * var for d, var in zip(durations, vars_list, strict=False))
            <= c.max_hours
        )
    return planning
