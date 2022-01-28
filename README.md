# qvis
## GUI tool for visualization of Subaru Telescope HSC Queue programs

The tool will open a Tkinter GUI and let you choose among different selection criteria 
to define the set of OBs that will be visualized.

The display options will allow you to:
- Display the visibility of individual OBs for a period observing nights
- Display the visibility of entire Programs (based on their contained OBs) 
- Display the number of OBs that can be observed (i.e. that satisfy Moon, time window, elevation limits, etc) 
- Display the total combined time of all qualifying OBs and group them by e.g. program, filter, grade, seeing, etc.
- Display the completion rates (used/allocated time) of individual programs.

The required python packages are:
- qplan   (see https://github.com/naojsoft/qplan)
- ginga
- tkcalendar
- pandas
- pandastable
- numpy
- matplotlib

## How to Use

You need to have a QDB access file. Request one to OCS group at Subaru. 
Place your "qdb.yml" file in the qvis main working directory and update the file name
on hscqueueconfig.py if needed.

You need to have downloaded the queue spreadsheet files for the semester.
The files are located in nextcloud /subaru-support-queue-shared/HSC-S2**/ob/  
- programs.xlsx
- schedule.xlsx 
- [all individual spreadsheet files of each program in the semester]


Run the tool from command line

$ python qvis.py

Created by Mirko Simunovic. Email me at mirkosm@naoj.org. 
