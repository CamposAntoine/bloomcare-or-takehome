"""Evaluator module for the Bloom Care scheduling results."""

from collections import defaultdict
from typing import Any

from .models import Assignment, Caregiver, Visit


def _is_caregiver_available(caregiver: Caregiver, visit: Visit) -> bool:
    """Check if caregiver is available for the given visit."""
    for availability in caregiver.availability:
        if availability.check_availability(visit):
            return True
    return False


def _calculate_caregiver_hours(
    assignments: list[Assignment], visits: list[Visit], caregiver_id: str
) -> float:
    """Calculate total hours worked by a caregiver."""
    total_hours = 0.0

    for assignment in assignments:
        if assignment.caregiver_id == caregiver_id:
            visit = next(v for v in visits if v.id == assignment.visit_id)
            total_hours += (visit.end - visit.start).total_seconds() / 3600.0

    return total_hours


def _calculate_continuity_score(
    assignments: list[Assignment], visits: list[Visit]
) -> float:
    """
    Calculate continuity of care score.

    Minimize different caregivers assigned to the same customer across multiple days.
    """
    if not assignments:
        return 0.0

    # Create lookup for visits
    visit_lookup = {visit.id: visit for visit in visits}

    # Group assignments by customer
    customer_assignments = defaultdict(list)
    for assignment in assignments:
        visit = visit_lookup[assignment.visit_id]
        customer_assignments[visit.customer].append(assignment)

    # Calculate continuity score for each customer
    customer_scores = []
    for customer_assigns in customer_assignments.values():
        total_visits = len(customer_assigns)
        unique_caregivers_set = {assign.caregiver_id for assign in customer_assigns}
        unique_caregivers = len(unique_caregivers_set)

        if total_visits == 1:
            # Single visit gets perfect score
            customer_scores.append(1.0)
        else:
            # Score = 1.0 - (unique_caregivers / total_visits)
            score = 1.0 - (unique_caregivers / total_visits)
            customer_scores.append(score)

    # Return average across all customers
    return sum(customer_scores) / len(customer_scores) if customer_scores else 0.0


def _calculate_travel_efficiency_score(
    assignments: list[Assignment], visits: list[Visit]
) -> float:
    """
    Calculate travel efficiency score.

    Minimize neighborhood switches per caregiver per day.
    """
    if not assignments:
        return 0.0

    # Create lookup for visits
    visit_lookup = {visit.id: visit for visit in visits}

    # Group assignments by caregiver and day
    caregiver_day_assignments = defaultdict(list)
    for assignment in assignments:
        visit = visit_lookup[assignment.visit_id]
        key = (assignment.caregiver_id, visit.start.strftime("%A"))
        caregiver_day_assignments[key].append((visit, assignment))

    # Calculate switches for each caregiver-day combination
    total_switches = 0
    total_caregiver_days = 0

    for day_assigns in caregiver_day_assignments.values():
        total_caregiver_days += 1

        if len(day_assigns) == 1:
            # Single visit gets perfect score (no switches)
            continue

        # Sort by time to get visit order
        day_assigns.sort(key=lambda x: x[0].start)

        # Count neighborhood switches
        switches = 0
        current_neighborhood = day_assigns[0][0].neighborhood

        for visit, _ in day_assigns[1:]:
            if visit.neighborhood != current_neighborhood:
                switches += 1
                current_neighborhood = visit.neighborhood

        total_switches += switches

    if total_caregiver_days == 0:
        return 0.0

    # Calculate average switches per caregiver per day
    avg_switches = total_switches / total_caregiver_days

    # Score = 1.0 - (avg_switches / 2.0), capped at 0.0
    score = max(0.0, 1.0 - (avg_switches / 2.0))
    return score


def _get_unassigned_visits(
    assignments: list[Assignment], visits: list[Visit]
) -> list[str]:
    assigned_visit_ids = {assignment.visit_id for assignment in assignments}
    all_visit_ids = {visit.id for visit in visits}
    return list(all_visit_ids - assigned_visit_ids)


def _get_availability_violations(
    assignments: list[Assignment], visits: list[Visit], caregivers: list[Caregiver]
) -> list[Assignment]:
    visit_lookup = {visit.id: visit for visit in visits}
    caregiver_lookup = {caregiver.id: caregiver for caregiver in caregivers}
    violations = []
    for assignment in assignments:
        visit = visit_lookup[assignment.visit_id]
        caregiver = caregiver_lookup[assignment.caregiver_id]
        if not _is_caregiver_available(caregiver, visit):
            violations.append(assignment)
    return violations


def _get_overlap_violations(
    assignments: list[Assignment], visits: list[Visit]
) -> list[dict[str, Any]]:
    visit_lookup = {visit.id: visit for visit in visits}
    caregiver_assignments = defaultdict(list)
    for assignment in assignments:
        caregiver_assignments[assignment.caregiver_id].append(assignment)
    violations = []
    for caregiver_id, caregiver_assigns in caregiver_assignments.items():
        for i, assignment1 in enumerate(caregiver_assigns):
            visit1 = visit_lookup[assignment1.visit_id]
            for assignment2 in caregiver_assigns[i + 1 :]:
                visit2 = visit_lookup[assignment2.visit_id]
                if visit1.overlaps(visit2):
                    violations.append(
                        {
                            "caregiver_id": caregiver_id,
                            "conflicting_visits": [
                                assignment1.visit_id,
                                assignment2.visit_id,
                            ],
                        }
                    )
    return violations


def _get_max_hours_violations(
    assignments: list[Assignment], visits: list[Visit], caregivers: list[Caregiver]
) -> list[dict[str, Any]]:
    violations = []
    for caregiver in caregivers:
        total_hours = _calculate_caregiver_hours(assignments, visits, caregiver.id)
        if total_hours > caregiver.max_hours:
            violations.append(
                {
                    "caregiver_id": caregiver.id,
                    "assigned_hours": total_hours,
                    "max_hours": caregiver.max_hours,
                }
            )
    return violations


def _check_constraint_violations(
    assignments: list[Assignment], visits: list[Visit], caregivers: list[Caregiver]
) -> dict[str, Any]:
    return {
        "unassigned_visits": _get_unassigned_visits(assignments, visits),
        "availability_violations": _get_availability_violations(
            assignments, visits, caregivers
        ),
        "overlap_violations": _get_overlap_violations(assignments, visits),
        "max_hours_violations": _get_max_hours_violations(
            assignments, visits, caregivers
        ),
    }


def display_caregiver_schedules(
    assignments: list[Assignment], visits: list[Visit], caregivers: list[Caregiver]
) -> None:
    """
    Display detailed schedules for each caregiver.

    Shows each caregiver's assignments organized by day, with multiple visits per day
    properly handled.
    """
    # Create lookups
    visit_lookup = {visit.id: visit for visit in visits}

    # Group assignments by caregiver
    caregiver_assignments = defaultdict(list)
    for assignment in assignments:
        visit = visit_lookup[assignment.visit_id]
        caregiver_assignments[assignment.caregiver_id].append((visit, assignment))

    print("\n" + "=" * 70)
    print("CAREGIVER SCHEDULES")
    print("=" * 70)

    for caregiver in caregivers:
        caregiver_id = caregiver.id
        name = caregiver.name
        max_hours = caregiver.max_hours
        skills = ", ".join(caregiver.skills)

        # Calculate utilization stats
        assigned_hours = _calculate_caregiver_hours(assignments, visits, caregiver.id)
        assigned_visits = len(
            [a for a in assignments if a.caregiver_id == caregiver.id]
        )
        utilization = (
            (assigned_hours / caregiver.max_hours) * 100
            if caregiver.max_hours > 0
            else 0
        )

        # Get this caregiver's assignments
        if caregiver_id not in caregiver_assignments:
            print(f"\n{caregiver_id} - {name} (Max: {max_hours}h, Skills: {skills})")
            print(
                f"   {assigned_hours:.1f}/{max_hours}h ({utilization:.0f}%) - "
                f"{assigned_visits} visits"
            )
            print("   No assignments")
            continue

        assignments_for_caregiver = caregiver_assignments[caregiver_id]

        print(
            f"\n{caregiver_id} - {name} {assigned_hours:.1f}/{max_hours}h "
            f"({utilization:.0f}%) - {assigned_visits} visits"
        )
        print("=" * 70)

        # Group assignments by day
        day_assignments = defaultdict(list)
        for visit, assignment in assignments_for_caregiver:
            day = visit.start.strftime("%A")
            day_assignments[day].append((visit, assignment))

        # Display assignments by day
        for day in [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]:
            if day in day_assignments:
                day_visits = day_assignments[day]
                # Sort visits by start time
                day_visits.sort(key=lambda x: x[0].start)

                print(f"\n{day}:")
                for visit, assignment in day_visits:
                    start_time = visit.start.strftime("%H:%M")
                    end_time = visit.end.strftime("%H:%M")
                    duration = (visit.end - visit.start).total_seconds() / 3600.0
                    print(
                        f"   {start_time}-{end_time} ({duration:.1f}h) "
                        f"{assignment.visit_id} - {visit.customer} "
                        f"({visit.neighborhood}) [{visit.required_skill}]"
                    )

        print("=" * 70)


def evaluate(
    assignments: list[Assignment], visits: list[Visit], caregivers: list[Caregiver]
) -> dict[str, Any]:
    """
    Evaluate the scheduling results.

    Args:
        assignments: List of Assignment objects
        visits: List of all visits
        caregivers: List of all caregivers

    Returns:
        Dictionary containing evaluation results
    """
    evaluation = {
        "constraint_violations": _check_constraint_violations(
            assignments, visits, caregivers
        ),
        "optimization_metrics": {
            "continuity_score": 0.0,
            "travel_efficiency_score": 0.0,
        },
    }

    # Calculate optimization metrics
    evaluation["optimization_metrics"][
        "continuity_score"
    ] = _calculate_continuity_score(assignments, visits)
    evaluation["optimization_metrics"][
        "travel_efficiency_score"
    ] = _calculate_travel_efficiency_score(assignments, visits)

    return evaluation
