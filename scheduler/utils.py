def available_for_that_visit(caregiver, visit) -> bool:
    """
    Vérifie si le caregiver peut effectuer la visite en terme de dispo.
    
 
    Renvoie: True si le caregiver peut effectuer la visite, False sinon
    """
    # On va chercher le jour de la semaine en majuscule, comme dans caregivers.json
    visit_day = visit.start.strftime("%A").upper()
    for avail in caregiver.availability:
        if (avail.day == visit_day and
            avail.start <= visit.start.time() and
            visit.end.time() <= avail.end):
            return True  
    return False 


def visits_overlap(v1: Visit, v2: Visit) -> bool:
    """
    Vérifie si deux visites se chevauchent dans le temps.

    Renvoie True si chevauchement, False sinon
    """
    latest_start = max(v1.start, v2.start)
    earliest_end = min(v1.end, v2.end)
    return latest_start < earliest_end
