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
  Experiment design            :active, design, 2019-10-01, 2019-12-9
  

  section Data collection
  Experiment 1        :exp1, after design, 30d
  

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
    
    3. * [ ]   input/output file organization
    
    4. * [ ]   pilot test
    
    
* Data collection


* Data analysis



