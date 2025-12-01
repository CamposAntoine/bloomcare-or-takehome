# Bloom Care OR Take-home Test

## Antoine Campos

I want to improve the daily lives of homecare professionals and the people they support.

I was tasked with building a **staff scheduler** to help our clients optimise their schedules. The agency needs to assign caregivers to visits throughout a week, considering a few constraints.

**My goal**: Assign workers to visits while satisfying constraints and optionally optimizing for some extra criteria.

### **Given**:

- A list of **caregivers**, each with:
  - A weekly **availability** (e.g Monday 8h-12h, Tuesday 8h-18h, …)
  - A **maximum weekly working time** (e.g. 35h)
  - Skills (e.g. "cooking", "hygiene", "cleaning")
- A list of **visits**, each defined by:
  - A start and end time
  - Required **skill**
  - A neighborhood

### Core Requirements

- Staff as many visits as possible (ideally **all visits is staffed**)
- Each caregiver is only assigned to visits they are **available** for
- No caregiver is assigned to **overlapping visits**
- No caregiver works **more than their max hours per week**

### 🚀 Bonus Objectives (stretch)

Once the basics work, if you still have some time, you can try optimizing further. Pick one or more of these:

- **Continuity of care**: minimize the number of different caregivers assigned to the same customer across multiple days (clients prefer familiar faces!)
- **Travel efficiency**: minimize how often caregivers switch **neighborhoods** during a single day (less travel time = better quality of life for caregivers)

## ✅ Time

I spent around 3-4 hours on this assignement
### Expected output

My solver will return a list of assignments (see `Assignment` class in `models.py`). Run `poetry run python -m scheduler` to evaluate your output (see [CONTRIBUTING.md](CONTRIBUTING.md))


### What I will be evaluated on

- [ ] You followed the instructions
- [ ] Your architecture and design choices are clearly documented
- [ ] Correctness: Are all constraints respected?
- [ ] Clarity: Is the code readable and well-explained?
- [ ] Modeling: Did you structure the problem thoughtfully?
- [ ] Tests are included and runnable


### My stack

I chose to use `CP-SAT` from `OR-Tools`.

### 💪 **Thanks for your time!**

---

## Documentation

- **[CONTRIBUTING.md](CONTRIBUTING.md)**: Development help and code quality standards
- **[SCORING.md](SCORING.md)**: Detailed explanation of how my solution is evaluated and scored
