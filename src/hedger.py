from dataclasses import dataclass
import pandas as pd
import numpy as np
from bsm import BSM

#----------------------------------------------------------------------------

class Hedger:
    @dataclass
    class HedgingStats:
        cost_basis: float
        mse: float = 0.0
        total_cost: float = 0.0
            
        def __repr__(self):
            return (f"[Hedger.{type(self).__name__}]: "
                    f"Assuming a cost basis of {self.cost_basis*100:.2f}%, mean-squared error "
                    f"of hedging was {self.mse:.2f}, and the total costs were ${self.total_cost:.2f}.")
    
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

    def delta_hedge(self, data, sheet_name="", portfolio_size=2, schedule=2, cost_basis=0.01):
        df = data.get_df(sheet_name=sheet_name)
        
        # We consider at-the-money options.
        day0 = df.iloc[0]
        strikes = day0.dropna().filter(regex=r"\d+").index
        option_value_ser = pd.Series(data=strikes, index=strikes, dtype=int).apply(lambda E: abs(day0.S - E))
        strikes_considered = option_value_ser.iloc[np.argsort(option_value_ser)[:portfolio_size]]
        print((f"[{type(self).__name__}] Info: "
               "Considering a position in call(s) with strike price(s) of "
               f"{', '.join(map(lambda x: '$' + x, strikes_considered.index))}"))
        
        # Compute and save state for the required computations.
        BSMs = {E: BSM(day0.S, int(E), day0.r, day0.T_norm, day0[E]) for E in strikes_considered.index}
        deltas = np.sum(np.nan_to_num(list(map(lambda x: x.delta, BSMs.values()))))
        longs = day0[strikes_considered.index].sum()
        state_prev = Hedger.DeltaState(
            longs, deltas * day0.S, deltas, {E: BSMs[E].delta for E in BSMs.keys()}
        )
        stats = Hedger.HedgingStats(cost_basis=cost_basis)
        stats.total_cost += cost_basis * state_prev.short
        
        # Simulate trading with the provided data and perform hedging.
        day1_onwards = df.iloc[1:-1].to_dict("index")
        squared_errors = []
        for t, row in day1_onwards.items():
            BSMs = {E: BSM.make_from_dict(row, E) for E in strikes_considered.index}
            longs = sum(map(lambda x: x.C_obs, BSMs.values()))
            delta_handler = lambda x: x.delta if not math.isnan(x.delta) else state_prev.E_to_delta[str(x.E)]
            state = Hedger.DeltaState(
                longs, state_prev.delta * row["S"], state_prev.delta, {E: delta_handler(BSMs[E]) for E in BSMs.keys()}
            )
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
        
    def delta_vega_hedge(self, data, sheet_name="", portfolio_size=2, schedule=2, cost_basis=0.01):
        if not sheet_name:
            sheet_name = data.get_sheet_names()[0]
            print(f"[{type(self).__name__}] Warning: sheet name not specified; proceeding with {sheet_name!r}")
            
        df = data.get_df(sheet_name=sheet_name)
        next_sheet = data.get_next_sheet_name(sheet_name)
        df2 = data.get_df(sheet_name=next_sheet)
        
        # Take the date at which the second sheet starts.
        for index, row in df.iterrows():
            if row["date"] == df2.iloc[0]["date"]:
                break
        start_index = index
        
        # We consider at-the-money options.
        day0 = df.iloc[start_index]
        strikes = day0.dropna().filter(regex=r"\d+").index
        option_value_ser = pd.Series(data=strikes, index=strikes, dtype=int).apply(lambda E: abs(day0.S - E))
        day0_2 = df2.iloc[0]
        strikes2 = day0_2.dropna().filter(regex=r"\d+").index
        option_value_ser_2 = pd.Series(data=strikes2, index=strikes2, dtype=int).apply(lambda E: abs(day0_2.S - E))
        
        portfolio_strikes = option_value_ser.iloc[np.argsort(option_value_ser)[:portfolio_size]]
        rep_option_strike = option_value_ser_2.iloc[np.argsort(option_value_ser_2)[:1]]
        print((f"[{type(self).__name__}] Info: "
               "Considering a position in call(s) with strike price(s) of "
               f"{', '.join(map(lambda x: '$' + x, portfolio_strikes.index))}"))
        
        # Compute and save state for the required computations.
        portfolio_BSMs = {E: BSM(day0.S, int(E), day0.r, day0.T_norm, day0[E]) for E in portfolio_strikes.index}
        rep_E = rep_option_strike.index[0]
        rep_option_BSM = BSM(day0_2.S, int(rep_E), day0_2.r, day0_2.T_norm, day0_2[rep_E])
        portfolio_delta = sum(map(lambda x: x.delta, portfolio_BSMs.values()))
        portfolio_vega = sum(map(lambda x: x.vega, portfolio_BSMs.values()))
        rep_option_delta = rep_option_BSM.delta
        rep_option_vega = rep_option_BSM.vega
        portfolio = day0[portfolio_strikes.index].sum() 
        alpha = -portfolio_delta + portfolio_vega / rep_option_vega * rep_option_delta
        eta = -portfolio_vega / rep_option_vega
        # Don't hedge at day 0 if some delta or vega is nan (= implied vol is nan).
        if math.isnan(alpha + eta):
            alpha, eta = 0, 0
        state_prev = Hedger.DeltaVegaState(portfolio, alpha * day0.S, eta * day0_2[rep_E], alpha, eta)
        stats = Hedger.HedgingStats(cost_basis=cost_basis)
        stats.total_cost += cost_basis * state_prev.alpha * day0.S + cost_basis * state_prev.eta * day0_2[rep_E]
        
        # Simulate trading with the provided data and perform hedging.
        day1_onwards = df.iloc[start_index+1:-1].reset_index(drop=True).to_dict("index")
        day1_onwards_2 = df2.iloc[1:-1].reset_index(drop=True).to_dict("index")
        squared_errors = []
        for t, row in day1_onwards.items():
            row2 = day1_onwards_2[t]
            portfolio_BSMs = {E: BSM.make_from_dict(row, E) for E in portfolio_strikes.index}
            rep_option_BSM = BSM.make_from_dict(row2, rep_E)
            portfolio = sum(map(lambda x: x.C_obs, portfolio_BSMs.values()))
            state = Hedger.DeltaVegaState(
                portfolio, state_prev.alpha * row["S"], state_prev.eta * row2[rep_E], state_prev.alpha, state_prev.eta
            )
            diff = (state.portfolio + state.underlying + state.rep_option) \
                   - (state_prev.portfolio + state_prev.underlying + state_prev.rep_option)
            squared_errors.append(diff**2)
            # Rehedge?
            if t % schedule == 0:
                portfolio_delta = sum(map(lambda x: x.delta, portfolio_BSMs.values()))
                portfolio_vega = sum(map(lambda x: x.vega, portfolio_BSMs.values()))
                rep_option_delta = rep_option_BSM.delta
                rep_option_vega = rep_option_BSM.vega
                eps = np.finfo(float).eps
                alpha = -portfolio_delta + portfolio_vega / (rep_option_vega + eps) * rep_option_delta
                eta = -portfolio_vega / (rep_option_vega + eps)
                if not math.isnan(alpha + eta):
                    state.alpha, state.eta = alpha, eta
                state.underlying = state.alpha * row["S"]
                state.rep_option = state.eta * row2[rep_E]
                stats.total_cost += abs(
                    cost_basis * (state_prev.alpha - state.alpha) * row["S"] \
                    + cost_basis * (state_prev.eta - state.eta) * row2[rep_E]
                )
            state_prev = state
                
        stats.mse = np.mean(squared_errors)
        return stats

#----------------------------------------------------------------------------
