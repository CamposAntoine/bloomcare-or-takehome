from collections import defaultdict

from ortools.sat.python import cp_model

from .models import Caregiver, Visit


def compute_continuity_penalty(
    visits: list[Visit], planning: dict, model: cp_model.CpModel
):
    customer_caregiver_vars = {}
    for v in visits:
        customer = v.customer
        if customer not in customer_caregiver_vars:
            customer_caregiver_vars[customer] = {}
        for c_id, var in planning[v.id].items():
            if c_id not in customer_caregiver_vars[customer]:
                customer_caregiver_vars[customer][c_id] = model.NewBoolVar(
                    f"{customer}_{c_id}"
                )
            model.Add(var <= customer_caregiver_vars[customer][c_id])

    continuity_penalty = sum(
        customer_caregiver_vars[customer][c_id]
        for customer in customer_caregiver_vars
        for c_id in customer_caregiver_vars[customer]
    )
    return continuity_penalty


def compute_travel_penalty(
    visits: list[Visit],
    planning: dict,
    caregivers: list[Caregiver],
    model: cp_model.CpModel,
):
    travel_penalty_vars = []

    for c in caregivers:
        visits_by_day = defaultdict(list)
        for v in visits:
            if c.id in planning[v.id]:
                day = v.start.date()  # We just need the day
                visits_by_day[day].append(v)

        for day_visits in visits_by_day.values():
            # We sort to view only consecutive visits
            day_visits.sort(key=lambda v: v.start)
            for i in range(len(day_visits) - 1):
                v1 = day_visits[i]
                v2 = day_visits[i + 1]

                if v1.neighborhood != v2.neighborhood:
                    switch_var = model.NewBoolVar(f"switch_{c.id}_{v1.id}_{v2.id}")
                    # If switch_var = 1 => both visits are assigned to c
                    model.AddBoolAnd(
                        [planning[v1.id][c.id], planning[v2.id][c.id]]
                    ).OnlyEnforceIf(switch_var)
                    # If switch_var = 0 => it does not chain the two visits
                    model.AddBoolOr(
                        [planning[v1.id][c.id].Not(), planning[v2.id][c.id].Not()]
                    ).OnlyEnforceIf(switch_var.Not())

                    travel_penalty_vars.append(switch_var)

    travel_penalty = sum(travel_penalty_vars)
    return travel_penalty
