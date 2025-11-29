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