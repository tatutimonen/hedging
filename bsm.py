import math
from dataclasses import dataclass, field
import functools
import warnings
warnings.filterwarnings("ignore")
import numpy as np
from scipy.stats import norm
from pyfinance.options import BSM as BSMAux

#-------------------------------------------------------------------------

@dataclass(frozen=True)
class BSM:
    S: float
    E: float
    r: float
    T: float
    C_obs: float
    sigma: float = 1.0
    d1: float = field(init=False)
    d2: float = field(init=False)

    def __post_init__(self):
        S, E, r, T, C_obs, sigma = self.S, self.E, self.r, self.T, self.C_obs, self.sigma
        sigma = BSMAux(S0=S, K=E, T=T, r=r, sigma=0.5, kind='call').implied_vol(C_obs)
        object.__setattr__(self, "sigma", sigma)
        eps = np.finfo(float).eps
        d1 = (math.log(S / E) + (r + 0.5 * self.sigma**2) * T) / (sigma * math.sqrt(T) + eps)
        object.__setattr__(self, "d1", d1)
        d2 = self.d1 - self.sigma * math.sqrt(T)
        object.__setattr__(self, "d2", d2)

    @staticmethod
    def make_from_dict(d, E):
        return BSM(d["S"], int(E), d["r"], d["T_norm"], d[E])

    @functools.cached_property
    def delta(self):
        return norm.cdf(self.d1)

    @functools.cached_property
    def vega(self):
        return self.S * math.sqrt(self.T) * norm.pdf(self.d1)

#-------------------------------------------------------------------------
