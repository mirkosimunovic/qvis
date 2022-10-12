# Options
current_semester = "S22B"
programfilepath = "/Users/msimunovic/Dropbox/HSC/QVis/assets/programs.xlsx"
schedulefilepath = "/Users/msimunovic/Dropbox/HSC/QVis/assets/schedule.xlsx"
maxobquery = 100     # Maximum number of OBs queried per Program
qdbfile = "qdb.yml"		# File name for the QDB access file. Must be located inside the qvis working directory. 


# Define all the lists of observing conditions in HSC Queue programs
grades = ['Grade A','Grade B','Grade C','Grade F']
seeing = ['0.8','1.0','1.3','1.6','100.0']
transp = ['0.7','0.4','0.1','0.0']
airmass = ['2.0','2.5','3.0','any']
bbfilters = ['HSC-g','HSC-r2','HSC-i2','HSC-z','HSC-Y']
nbfilters =[
'NB387',				
'NB391',				
'NB395',	
'NB400',				
'NB430',				
'NB468',				
'NB497',
'NB506',				
'NB515',				
'NB527',				
'NB656',				
'NB718',				
'NB816',				
'NB921',				
'NB926',				
'IB945',				
'NB973',				
'NB1010']	

label_dic = { 
"program":"program",
"filter":"inscfg_filter", 
"grade":"grade",
"completion":"completion_rate",
"seeing":"envcfg_seeing",
"airmass":"envcfg_airmass",
"transp":"envcfg_transparency",
"moon":"envcfg_moon",
"moon_sep":"envcfg_moon_sep",
"target":"target_name"
}
