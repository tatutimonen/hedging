from dataclasses import dataclass, field
import math
import pandas as pd
import numpy as np
from bsm import BSM

#-------------------------------------------------------------------------

class Hedger:
    def __new__(cls):
        raise Exception("Non-instantiable class!")

    @dataclass
    class HedgingStats:
        sheet_name: str
        hedge_type: str
        portfolio_size: int
        schedule: int
        cost_basis: float
        strikes: list = field(default_factory=list)
        mse: float = 0.0
        total_cost: float = 0.0
            
        def __repr__(self):
            return (f"[Hedger.{type(self).__name__}]: Using data from sheet {self.sheet_name!r}, performing "
                    f"{self.hedge_type} hedging on a portfolio of {self.portfolio_size} options "
                    f"(strikes of {', '.join('$' + x for x in self.strikes)}) with a schedule of {self.schedule} days,"
                    f" and assuming a cost basis of {self.cost_basis * 100:.2f}%, yielded a mean-squared error "
                    f"of {self.mse:.2f}. The total hedging costs were ${self.total_cost:.2f}.")
    
    @dataclass
    class DeltaState:
        long: float
        short: float
        delta: float
        E_to_delta: dict
            
    @dataclass
    class DeltaVegaState:
        portfolio: float
        underlying: float
        rep_option: float
        alpha: float
        eta: float

    @staticmethod
    def delta_hedge(data, sheet_name="", portfolio_size=2, schedule=2, cost_basis=0.01):
        df = data.get_df(sheet_name=sheet_name)
        
        # We consider at-the-money options.
        day0 = df.iloc[0]
        strikes = day0.dropna().filter(regex=r"\d+").index
        option_value_ser = pd.Series(data=strikes, index=strikes, dtype=int).apply(lambda E: abs(day0.S - E))
        strikes_considered = option_value_ser.iloc[np.argsort(option_value_ser)[:portfolio_size]]
        
        # Compute and save state for the required computations.
        BSMs = {E: BSM(day0.S, int(E), day0.r, day0.T_norm, day0[E]) for E in strikes_considered.index}
        deltas = np.sum(np.nan_to_num([x.delta for x in BSMs.values()]))
        longs = day0[strikes_considered.index].sum()
        state_prev = Hedger.DeltaState(longs, deltas * day0.S, deltas, {E: BSMs[E].delta for E in BSMs.keys()})
        stats = Hedger.HedgingStats(sheet_name, "delta", portfolio_size, schedule, cost_basis, strikes_considered.index)
        stats.total_cost += cost_basis * state_prev.short

        # Simulate trading with the provided data and perform hedging.
        day1_onwards = df.iloc[1:-1].to_dict("index")
        squared_errors = []

        for t, row in day1_onwards.items():
            BSMs = {E: BSM.make_from_dict(row, E) for E in strikes_considered.index}
            longs = sum(x.C_obs for x in BSMs.values())
            delta_handler = lambda x: x.delta if not math.isnan(x.delta) else state_prev.E_to_delta[str(x.E)]
            state = Hedger.DeltaState(
                longs, state_prev.delta * row["S"], state_prev.delta, {E: delta_handler(BSMs[E]) for E in BSMs.keys()})
            dlong = state.long - state_prev.long
            dshort = state.short - state_prev.short
            squared_errors.append((dlong - dshort)**2)
            # Rehedge?
            if t % schedule == 0:
                deltas = sum(state.E_to_delta.values())
                state.short = deltas * row["S"]
                state.delta = deltas
                stats.total_cost += abs(cost_basis * (state_prev.delta - state.delta) * row["S"])
            state_prev = state
                
        stats.mse = np.mean(squared_errors)
        return stats
        
    @staticmethod
    def delta_vega_hedge(data, sheet_name="", portfolio_size=2, schedule=2, cost_basis=0.01):
        if not sheet_name:
            sheet_name = data.get_sheet_names()[0]
            print("[Hedger] Warning: sheet name not specified; proceeding with {sheet_name!r}")

        df = data.get_df(sheet_name=sheet_name)
        # Options for hedging vega.
        next_sheet = data.get_next_sheet_name(sheet_name)
        df_hedge = data.get_df(sheet_name=next_sheet)

        # Take the date at which the second sheet starts.
        for index, row in df.iterrows():
            if row["date"] == df_hedge.iloc[0]["date"]:
                break
        start_index = index

        # We consider at-the-money options.
        day0 = df.iloc[start_index]
        strikes = day0.dropna().filter(regex=r"\d+").index
        option_value_ser = pd.Series(data=strikes, index=strikes, dtype=int).apply(lambda E: abs(day0.S - E))
        day0_hedge = df_hedge.iloc[0]
        strikes_hedge = day0_hedge.dropna().filter(regex=r"\d+").index
        option_value_ser_hedge = pd.Series(data=strikes_hedge, index=strikes_hedge, dtype=int).apply(lambda E: abs(day0_hedge.S - E))

        portfolio_strikes = option_value_ser.iloc[np.argsort(option_value_ser)[:portfolio_size]]
        rep_option_strike = option_value_ser_hedge.iloc[np.argsort(option_value_ser_hedge)[:1]]

        # Compute and save state for the required computations.
        portfolio_BSMs = {E: BSM(day0.S, int(E), day0.r, day0.T_norm, day0[E]) for E in portfolio_strikes.index}
        E_rep = rep_option_strike.index[0]
        rep_option_BSM = BSM(day0_hedge.S, int(E_rep), day0_hedge.r, day0_hedge.T_norm, day0_hedge[E_rep])
        portfolio_delta = sum(x.delta for x in portfolio_BSMs.values())
        portfolio_vega = sum(x.vega for x in portfolio_BSMs.values())
        rep_option_delta = rep_option_BSM.delta
        rep_option_vega = rep_option_BSM.vega
        portfolio = day0[portfolio_strikes.index].sum() 
        alpha = -portfolio_delta + portfolio_vega / rep_option_vega * rep_option_delta
        eta = -portfolio_vega / rep_option_vega
        # Don't hedge at day 0 if some delta or vega is nan (= implied vol is nan).
        if math.isnan(alpha + eta):
            alpha, eta = 0, 0

        state_prev = Hedger.DeltaVegaState(portfolio, alpha * day0.S, eta * day0_hedge[E_rep], alpha, eta)
        stats = Hedger.HedgingStats(sheet_name, "delta-vega", portfolio_size, schedule, cost_basis, portfolio_strikes.index)
        stats.total_cost += cost_basis * state_prev.alpha * day0.S + cost_basis * state_prev.eta * day0_hedge[E_rep]
        
        # Simulate trading with the provided data and perform hedging.
        day1_onwards = df.iloc[start_index+1:-1].reset_index(drop=True).to_dict("index")
        day1_onwards_hedge = df_hedge.iloc[1:-1].reset_index(drop=True).to_dict("index")
        squared_errors = []

        for t, row in day1_onwards.items():
            row_hedge = day1_onwards_hedge[t]
            portfolio_BSMs = {E: BSM.make_from_dict(row, E) for E in portfolio_strikes.index}
            rep_option_BSM = BSM.make_from_dict(row_hedge, E_rep)
            portfolio = sum(x.C_obs for x in portfolio_BSMs.values())
            state = Hedger.DeltaVegaState(
                portfolio, state_prev.alpha * row["S"], state_prev.eta * row_hedge[E_rep], state_prev.alpha, state_prev.eta)
            diff = (state.portfolio + state.underlying + state.rep_option) \
                   - (state_prev.portfolio + state_prev.underlying + state_prev.rep_option)
            squared_errors.append(diff**2)
            # Rehedge?
            if t % schedule == 0:
                portfolio_delta = sum(x.delta for x in portfolio_BSMs.values())
                portfolio_vega = sum(x.vega for x in portfolio_BSMs.values())
                rep_option_delta = rep_option_BSM.delta
                rep_option_vega = rep_option_BSM.vega
                
                eps = np.finfo(float).eps
                alpha = -portfolio_delta + portfolio_vega / (rep_option_vega + eps) * rep_option_delta
                eta = -portfolio_vega / (rep_option_vega + eps)
                if not math.isnan(alpha + eta):
                    state.alpha, state.eta = alpha, eta
                
                state.underlying = state.alpha * row["S"]
                state.rep_option = state.eta * row_hedge[E_rep]
                stats.total_cost += abs(
                    cost_basis * (state_prev.alpha - state.alpha) * row["S"] \
                    + cost_basis * (state_prev.eta - state.eta) * row_hedge[E_rep])

            state_prev = state
                
        stats.mse = np.mean(squared_errors)
        return stats

#-------------------------------------------------------------------------
