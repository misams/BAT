# BAT - Bolt Analysis Tool
> High Duty Bolted Joint Analysis

The bolt analysis tool (BAT) is an input file based Python command line tool for multi-bolt analyses. It is designed primarily for the space industry (ESA), but of course it can be used for all kinds of high duty bolted joint analyses. 

Standards implemented in BAT (current status includes concentric axially loaded joints only):
- ESA PSS-03-208 Issue 1 (December 1989)
- [ECSS-E-HB-32-23A 16 April 2010](https://ecss.nl/hbstms/ecss-e-hb-32-23a-threaded-fasteners-handbook/)

The user manual can be found here: [BAT User-Manual](https://github.com/misams/BAT/blob/master/BAT/doc/BAT_doc/LaTex/BAT_UserManual.pdf)

It supports Python 3.0+ and uses pyQT5, matplotlib and numpy.

[![PyPI status](https://img.shields.io/pypi/status/ansicolortags.svg)](https://pypi.python.org/pypi/ansicolortags/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.0+](https://img.shields.io/badge/Python-3.0%2B-success)](https://www.python.org)
[![required](https://img.shields.io/badge/required-pyQt5%2C%20matplotlib%2C%20numpy-success)]()

## Run BAT without GUI
 
- Download or clone the repository `https://github.com/misams/BAT.git`.
- Run the BAT software with the included test input file `input_test_1.inp`.
```shell
$ python bat_main.py -i input_test_1.inp
```
- After sucessfully running `bat_main.py` you get the analysis result directly to your terminal and to the output file `output_test.out` or you redefine the output file name.
```shell
$ python bat_main.py -i input_test_1.inp -o output_test_1.out
```
- To show all available command line options - type the following.
```shell
$ python bat_main.py --help
```

## Run BAT with GUI (pyQT5)

- Download or clone the repository `https://github.com/misams/BAT.git`.
- Run the BAT software with the GUI-option.
```shell
$ python bat_main.py --gui
```
![Example Screenshot BAT v0.7.5](https://github.com/misams/BAT/blob/master/BAT/doc/bat_example.png)

## Changelog

Release | Date | Info
--- | --- | ---
v0.7.5 | 16.05.2021 | - circular Flange-GUI<br>- tightening torque tolerance drop-down included<br>- MOS correction if gapping occurs
v0.7.4 | 04.04.2021 | - bolt and material info button and windows added to GUI<br>- Tools/Bolted Flange disabled (under development)
v0.7.3 | 30.01.2021 | - MIN / MAX prevailing torque M_p added
v0.7.2 | 02.01.2021 | - ECSS / ESA-PSS some bugs corrected (Mp implementation)<br>- ECSS: 5% embedding added<br>- fitting factor added (applied to loads)<br>- Flange-GUI-window added (dummy status)<br>- tests.py added (ECSS worked example 7.14 added)<br>- BAT User-Manual (LaTex) created
v0.7.1 | 13.09.2020 | - Torque table generator added
v0.7 | 08.09.2020 | - Base-Class for analysis methods<br>- ESA-PSS converted to base-class<br>- ECSS-E-HB-32-23A method included (GUI updated)
v0.6 | 01.09.2020 | - Save-methods finished
v0.5 | 26.07.2020 | - FQ bug corrected<br>- Save-as method implemented
v0.4 | 10.06.2020 | - pyQT5 GUI initial release<br>- config file: bat.ini added
v0.3.1 | 18.04.2020 | - GUI development started (--gui option added to launch BAT GUI)
v0.3 | 13.04.2020 | - BAT input printed to output<br>- error corrected if *USE_SHIM = no
v0.2 | 08.04.2020 | - VDI 2230 thermal method added (takes Young's modulus temperature dependance into account)
v0.1 | April 2020 | - first revision of beta software status

## License

- **[GNU General Public License v3.0](https://www.gnu.org/licenses/gpl-3.0.txt)**
- Copyright 2020 © misams
