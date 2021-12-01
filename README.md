# hedging

Hedging assignment for course TU-E2210 - Financial Engineering I.

The well-known Black-Scholes-Merton model provides a closed-form expression describing the price of a European call option:

<p align="center">
    <img src="https://latex.codecogs.com/svg.latex?\begin{aligned}&space;C(t,&space;S_t,&space;E,&space;T,&space;\sigma)&space;&=&space;S_t&space;F_\Phi(d_1)&space;-&space;E&space;e^{-r(T-t)}&space;F_\Phi(d_2),&space;\\&space;d_1&space;&=&space;\frac{\ln(S_t/E)&space;&plus;&space;(r&space;&plus;&space;\sigma^2/2)(T-t)}{\sigma&space;\sqrt{T-t}},&space;\\&space;d_2&space;&=&space;d_1&space;-&space;\sigma&space;\sqrt{T-t},&space;\\&space;F_\Phi(x)&space;&=&space;\frac{1}{2\pi}\int_{-\infty}^x&space;e^{-t^2/2}&space;\&space;\mathrm{d}t&space;\end{aligned}" title="\begin{aligned} C(t, S_t, E, T, \sigma) &= S_t F_\Phi(d_1) - E e^{-r(T-t)} F_\Phi(d_2), \\ d_1 &= \frac{\ln(S_t/E) + (r + \sigma^2/2)(T-t)}{\sigma \sqrt{T-t}}, \\ d_2 &= d_1 - \sigma \sqrt{T-t}, \\ F_\Phi(x) &= \frac{1}{2\pi}\int_{-\infty}^x e^{-t^2/2} \ \mathrm{d}t \end{aligned}">
</p>
