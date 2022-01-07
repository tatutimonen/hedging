## Hedging

We consider the problem of hedging a portfolio of at-the-money call options on S&P 100 index against the Greeks delta and vega on market data from the year 2010. This repository contains an implementation of a CLI tool to compare the performance of delta -and delta-vega hedging of portfolios of different sizes and with different hedging schedules. Python Standard Library module ```concurrent.futures``` is leveraged for parallel execution. Our work is related to a course assignment from the Aalto University course *TU-E2210 - Financial Engineering I*. The data was provided by the course personnel.

----

### Theoretical Background 

The source for this section is *Options futures and other derivatives, ninth edition* by John C. Hull.

The well-known Black-Scholes-Merton model provides a closed-form expression describing the price of a European call option:

<p align="center">
   <img src="https://latex.codecogs.com/svg.image?\begin{align*}C(t,&space;S_t;&space;E,&space;T;&space;\sigma)&space;&=&space;S_t&space;\,&space;\mathcal{N}(d_1)&space;-&space;E&space;e^{-r(T-t)}&space;\mathcal{N}(d_2),\\&space;d_1&space;&=&space;\frac{\ln(S_t/E)&space;&plus;&space;(r&space;&plus;&space;\sigma^2/2)(T-t)}{\sigma&space;\sqrt{T-t}},&space;\\&space;d_2&space;&=&space;d_1&space;-&space;\sigma&space;\sqrt{T-t},&space;\\&space;\mathcal{N}(x)&space;&=&space;\frac{1}{2\pi}\int_{-\infty}^x&space;e^{-u^2/2}&space;\&space;\mathrm{d}u,&space;\end{align*}"/>
</p>

<p>
where <i>t</i> denotes the current time, <i>S<sub>t</sub></i> the price of the underlying at time <i>t</i>, <i>E</i> the strike price, <i>T</i> the time to maturity, <i>σ</i> the volatility, and <i>r</i> the risk-free interest rate. We assume this as the pricing model of call options in this context.
</p>

<p>
The Greeks are a collection of partial derivatives of the function <i>C</i>. We consider the Greeks delta and vega. The delta of a European call option with an underlying that pays no dividends is defined as
</p>

<p align="center">
   <img src="https://latex.codecogs.com/svg.image?\Delta&space;=&space;\frac{\partial&space;C}{\partial&space;S_t}&space;=&space;\mathcal{N}(d_1)."/>
</p>

In essence, the delta of an option quantifies the sensitivity of the price of the option with respect to change in
the underlying. In delta hedging, we compensate for this risk by entering into a short position in the underlying, as we are long in the call(s).

The vega of a European call option with an underlying that pays no dividends is defined as

<p align="center">
   <img src="https://latex.codecogs.com/svg.image?\mathcal{V}&space;=&space;\frac{\partial&space;C}{\partial&space;\sigma}&space;=&space;S_t&space;\sqrt{T-t}&space;\,&space;\mathcal{N}'(d_1)."/>
</p>

The vega of an option captures the price risk related to changes in volatility. In delta-vega hedging, one seeks risk neutrality with respect to both delta and vega. Since the vega of the underlying is zero, taking further option positions is required to achieve vega neutrality.

----

### Running Locally

   1. Install the required libraries with ```pip install -r requirements.txt```
   2. For usage information, do ```python main.py --help```, and proceed as you see fit

----

### Results

One may notice that delta-vega hedging is superior to delta hedging as it provides smaller mean-squared error for the hedging period with smaller hedging costs.

----

### Note

The provided data contains erroneous price action information in some of its sheets (e.g., the option price increasing 1000-fold in a single day). As such, with certain sheets and hedging strategies and parameters the reported mean squeared errors explode to non-sensical levels.

----

### Authors

Miro Kaarela ([mkaarela](https://github.com/mkaarela)), Roope Kausiala ([AdmiralBulldog](https://github.com/AdmiralBulldog)), Tatu Timonen ([timonent](https://github.com/timonent))
