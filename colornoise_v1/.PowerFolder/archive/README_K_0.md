## Project Overview


## Codes
The programming uses Psychopy (v2020.1) with Python 3.7 (Ubuntu 18.04.3 LTS).
The experiment can be implemented by 8-bit or 10-bit color depths.  

| *.py file | Description | Example functions/modules |
| --- | --- | --- |
| rgb2lms_plus | calibrate with a calibration file, transform between rgb and lms | calibration, transformation |
| isolum | measure subject's isoluminance plane | isoslant, fitiso |
| colorpalette_plus | generates sml and RGB values with hue angles on an iso-luminance plane, and vice versa | ColorPicker|
| genconfig | write and read experiment config files | ParWriter, ParReader, XppWriter, XppReader, XrlWriter, XrlReader |
| multinoisecolor | excute the color noise experiment in 8-bit color depths | Exp, run_exp |
| multinoisecolor10bit | excute the color noise experiment in 10-bit color depths| Exp, run_exp |
| screensaver | screen-protect program in a colored board patten | run_scrsaver |

 
## Input and Output
### Important folders:
- /config
- /data
### Input
Running experiments requires config files in /config folder:    
    *.par - parameters of stimuli
    
### Output
- Running experiments writes config files in /config folder:    
    *.xpp - records of each single session    
    *.xrl - records of all pairs of parameters and sessions belong to one subject    
- Results are saved in /data folder:    
    *.xlsx - results of each complete session - no results will be saved if userbreak occurs    

