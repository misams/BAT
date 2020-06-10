# BAT - Bolt Analysis Tool
> High Duty Bolted Joint Analysis

The bolt analysis tool (BAT) is an input file based Python command line tool for multi-bolt analyses. It is designed primarily for the space industry (ESA), but of course it can be used for all kinds of high duty bolted joint analyses. 

Standards implemented in BAT (current status):
- ESA PSS-03-208 Issue 1 (December 1989)

It supports Python 3.0+ and uses pyQT5.

[![PyPI status](https://img.shields.io/pypi/status/ansicolortags.svg)](https://pypi.python.org/pypi/ansicolortags/)

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
![Example Screenshot BAT v0.4](https://github.com/misams/BAT/BAT/doc/bat_example.png)

## Changelog
### v0.4
>10.06.2020
- pyQT5 GUI initial release
- config file: bat.ini added

### v0.3.1
>18.04.2020
- GUI development started (--gui option added to launch BAT GUI)

### v0.3
>13.04.2020
- BAT input printed to output
- error corrected if *USE_SHIM = no

### v0.2
>08.04.2020
- VDI 2230 thermal method added (takes Young's modulus temperature dependance into account)

### v0.1
>April 2020
- first revision of beta software status

## License

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

- **[GNU General Public License v3.0](https://www.gnu.org/licenses/gpl-3.0.txt)**
- Copyright 2020 © misams
