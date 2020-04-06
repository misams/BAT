# Bolt Analysis Tool (BAT)

The bolt analysis tool (BAT) is an input file based Python command line tool for multi-bolt analyses. It is designed primarily for the space industry (ESA), but of course it can be used for all kinds of high duty bolted joint analyses.

Standards implemented in BAT (current status):
- ESA PSS-03-208 Issue 1 (December 1989)

It supports Python 3.0+ and uses standard libraries only.

## Readme to be filled in...

### Preload loss due to thermal expansion (CTE mismatch) and change in Young's Modulus (bolt and clamped parts)

![\Delta F_{Vth} = F_{VRT} \left(  1 - \frac{\delta_S + \delta_P}{\delta_S \frac{E_{SRT}}{E_{ST}} +  \delta_P \frac{E_{PRT}}{E_{PT}}} \right) + \frac{l_K (\alpha_S - \alpha_P) \Delta T}{\delta_S \frac{E_{SRT}}{E_{ST}} + \delta_P \frac{E_{PRT}}{E_{PT}}}](https://render.githubusercontent.com/render/math?math=%5CDelta%20F_%7BVth%7D%20%3D%20F_%7BVRT%7D%20%5Cleft(%20%201%20-%20%5Cfrac%7B%5Cdelta_S%20%2B%20%5Cdelta_P%7D%7B%5Cdelta_S%20%5Cfrac%7BE_%7BSRT%7D%7D%7BE_%7BST%7D%7D%20%2B%20%20%5Cdelta_P%20%5Cfrac%7BE_%7BPRT%7D%7D%7BE_%7BPT%7D%7D%7D%20%5Cright)%20%2B%20%5Cfrac%7Bl_K%20(%5Calpha_S%20-%20%5Calpha_P)%20%5CDelta%20T%7D%7B%5Cdelta_S%20%5Cfrac%7BE_%7BSRT%7D%7D%7BE_%7BST%7D%7D%20%2B%20%5Cdelta_P%20%5Cfrac%7BE_%7BPRT%7D%7D%7BE_%7BPT%7D%7D%7D)
