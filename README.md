
## Project Overview

---

## Codes
The programming uses Psychopy (v2020.1) with Python 3.7 (Ubuntu 18.04.3 LTS).
The experiment stimuli can be implemented by 8-bit or 10-bit color depths.  

| *.py file | Description | Example functions/modules |
| --- | --- | --- |
| rgb2lms_plus | calibrate with a calibration file, transform between rgb and lms | calibration, transformation |
| isolum | (abandoned!) measure subject's isoluminance plane | isoslant, fitiso |
| colorpalette_plus | generates sml and RGB values with hue angles on an iso-luminance plane, and vice versa | ColorPicker|
| genconfig | (abandoned!) write and read experiment config files | ParWriter, ParReader, XppWriter, XppReader, XrlWriter, XrlReader |
| config_tools | write and read experiment config files | write_cfg, write_par, WriteXpp, write_xrl, read_yml |
| multinoisecolor10bit | excute the color noise experiment in 10-bit color depths| Exp, run_exp |
| screensaver | screen-protect program in a colored board patten | run_scrsaver |

## Data structure
```
experiment directory  
│
└───config
|   |   expconfig.yaml    # experiment config YAML
│   │   parameter.yaml    # parameter YAML
│   └───colorlist         
│       └───subject       # lists of all achievable colors for this subject
│ 
└───isolum  
│   └───subject           # isoluminance measurement output for this subject
|
└───data
│   └───subject
|       |  subject_20200000T0000.yaml  # single session log YAML
|       |  subject.xrl                 # subject log file, records of all pairs of parameters and sessions belong to one subject 
|       |  subject20200000T0000.xlsx   # data from a compeleted session
|
```
