# BAT - Bolt Analysis Tool
> Easy to use bolt analysis

The bolt analysis tool (BAT) is an input file based Python command line tool for multi-bolt analyses. It is designed primarily for the space industry (ESA), but of course it can be used for all kinds of high duty bolted joint analyses.

Standards implemented in BAT (current status):
- ESA PSS-03-208 Issue 1 (December 1989)

It supports Python 3.0+ and uses standard libraries only.

[![PyPI status](https://img.shields.io/pypi/status/ansicolortags.svg)](https://pypi.python.org/pypi/ansicolortags/)

## Run BAT
 
- Simply download or clone the repository `https://github.com/misams/BAT.git`
- Run the BAT software with the included test input file `input_test_1.inp`
```shell
$ python bat_main.py -i input_test_1.inp
```
- After sucessfully running `bat_main.py` you get the analysis result directly to your terminal and to the output file `output_test.out` or you redefine the output file name.
```shell
$ python bat_main.py -i input_test_1.inp -o output_test_1.out
```

## License

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

- **[GNU General Public License v3.0](https://www.gnu.org/licenses/gpl-3.0.txt)**
- Copyright 2020 © misams
