---
output:
  pdf_document: default
  html_document: default
---


## Progress


```mermaid
gantt
  dateFormat YYYY-MM-DD
  title Progress of the project
  
  section Preparations
  Experiment set up                   :set-up, 2019-09-01, 2019-10-01
  Experiment design and pilot         :active, design, 2019-10-01, 2020-01-15
  

  section Data collection
  Experiment 1        :exp1, after exp1, 30d
  

  section Analysis
  Analysis of Exp.1            :ana1, after exp1, 30d


  section Manuscript
  Method section                :man1, after ana1, 70d
  Introduction                  :man3, after man1, 60d
  Discussion                    :man4, after man3, 30d
  Results                       :man2, after man3, 20d
  
```

# To-do Task

* Preparations

    1. * [x]   set up with Python 3 and PsychoPy

    2. * [x]   color-generation codes 

* Experimental design

    1. * [x]   background study

    2. * [x]   paradiam design
    
    3. * [x]   input/output file organization
    
    4. * [x]   pilot test and preliminary data analysis 
    
    5. * [ ]   set up 10-bit monitor (high color-depth is required)
    
    
* Data collection


* Data analysis



