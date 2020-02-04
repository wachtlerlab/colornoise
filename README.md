## Project Overview


## Codes
The programming uses Psychopy packages (with Python 3.5, Linux).

| *.py file | Description | Example functions/modules |
| --- | --- | --- |
| rgb2lms_copy | calibrate with a calibration file, transform between rgb and lms | calibration, transformation |
| isolum | measure subject's isoluminance plane | isoslant, fitiso |
| colorpalette | generate colors with hue angle, and subjective isoluminance adjustments if necessary | gensml, genrgb, newcolor, gentheta, showcolorcircle|
| genconfig | write and read experiment parameters/results | writepar, writexpp, writexrl, readpara, readstair
| multinoisecolor | make and excute the color noise experiment | Exp, runexp |
| screensaver | screen-protect program in a colored board patten | None |

 
## Input and Output
### Important folders:
- /config
- /data
### Input
Running experiments requires config files in /config folder:    
    *.par - parameters of stimuli
    
### Output
Running experiments writes config files in /config folder:
    *.xpp - records of each single session
    *.xrl - records of all pairs of parameters and sessions belong to one subject
Results are saved in /data folder:
    *.xlsx - results of each complete session - no results will be saved if userbreak occurs
