"""Layer 3: deterministic, auditable cleaning schedule with OR-Tools CP-SAT (free, open source)."""
import numpy as np
from ortools.sat.python import cp_model
from .model import daily_deposition, rain_flags, trajectory, PSH

TAIL_DAYS = 3   # value residual soiling for a few days beyond the horizon
SCALE = 10      # integer scaling for CP-SAT


def _coef(mw, price):  # AED per 1% loss for one day
    return mw * PSH * price / 100.0


def evaluate(sites, forecasts, initial, cleans, mw, price, clean_cost):
    """Score any schedule. cleans[site] = bool array over days."""
    res = {"traj": {}, "loss_cost": 0.0, "clean_cost": 0.0, "mwh_lost": 0.0, "n_cleans": 0}
    for s in sites:
        df = forecasts[s]
        dep, rain = daily_deposition(df), rain_flags(df)
        tr = trajectory(initial[s], dep, rain, cleans[s])
        res["traj"][s] = tr
        pct_days = tr.sum() + TAIL_DAYS * tr[-1]
        res["mwh_lost"] += pct_days / 100 * mw * PSH
        res["loss_cost"] += pct_days * _coef(mw, price)
        n = int(np.sum(cleans[s]))
        res["n_cleans"] += n
        res["clean_cost"] += n * clean_cost
    res["total_cost"] = res["loss_cost"] + res["clean_cost"]
    return res


def optimize(sites, forecasts, initial, mw, price, clean_cost, crews, time_limit=5.0):
    D = len(next(iter(forecasts.values())))
    m = cp_model.CpModel()
    x, loss = {}, {}
    BIG = 100_000
    obj = []
    for s in sites:
        df = forecasts[s]
        dep = np.round(daily_deposition(df) * 100).astype(int)   # hundredths of %
        rain = rain_flags(df)
        c = int(round(_coef(mw, price) / 100 * SCALE))           # cost per hundredth-% per day, scaled
        for d in range(D):
            x[s, d] = m.NewBoolVar(f"x_{s}_{d}")
            loss[s, d] = m.NewIntVar(0, BIG, f"l_{s}_{d}")
            prev = int(round(initial[s] * 100)) if d == 0 else loss[s, d - 1]
            m.Add(loss[s, d] >= int(dep[d]))
            if not rain[d]:
                m.Add(loss[s, d] >= prev + int(dep[d]) - BIG * x[s, d])
            else:
                m.Add(x[s, d] == 0)   # never pay for a clean on a rain day
            w = c * (1 + (TAIL_DAYS if d == D - 1 else 0))
            obj.append(w * loss[s, d])
            obj.append(int(clean_cost * SCALE) * x[s, d])
    for d in range(D):
        m.Add(sum(x[s, d] for s in sites) <= crews)
    m.Minimize(sum(obj))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_workers = 4
    status = solver.Solve(m)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None
    return {s: np.array([bool(solver.Value(x[s, d])) for d in range(D)]) for s in sites}


def fixed_cycle(sites, D, interval):
    """Calendar baseline: every site cleaned every `interval` days, staggered."""
    return {s: np.array([(d - i) % interval == 0 for d in range(D)]) for i, s in enumerate(sites)}
