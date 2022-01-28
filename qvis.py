import tkinter as tk
import tkinter.messagebox as msgbox
import tkinter.ttk as ttk
import os
import matplotlib.pyplot as plt
from hscqueueconfig import *
import hscqueueconfig
import qplancaller
import tablewindow
import qplan_plotter
from tkcalendar import DateEntry
import datetime
from datetime import timedelta
import time 
import pytz
local = pytz.timezone("US/Hawaii")
import importlib
from idlelib.tooltip import Hovertip
import traceback
import pandas as pd

class Panel(tk.Tk):

	def __init__(self):
		super().__init__()
		self.title("qvis")
		self.geometry("291x748+0+50")
		self.resizable(0,0)
		style = ttk.Style(self)
		style.theme_use('default')   # aqua, alt, default, clam, classic
		self.dict_all = {}
		self.semester_text=tk.StringVar()
		self.filepath_text=tk.StringVar()
		self.schedpath_text=tk.StringVar()
		self.maxOBdisp_text = tk.StringVar()
		self.tablecount = 0


		# Create the Header Label
		self.label = tk.Label(self,text="HSC Queue Vis Tool",fg='royal blue',font=('Open Sans',25))
		self.label.grid(sticky=tk.N,columnspan=2)

		n = ttk.Notebook(self)
		tab_1 = ttk.Frame(n)
		tab_2 = ttk.Frame(n)
		tab_3 = ttk.Frame(n)
		n.add(tab_1,text=" OB Conditions")
		n.add(tab_2,text=" Filters")
		n.add(tab_3,text=" Options")
		n.grid(sticky=tk.NSEW,columnspan=2)

		# TAB 1  Observing Conditions
		# Make Program Grade Frame
		self.grade_vars,self.grade_all = self.make_newFrame(tab_1,grades,"Program Grade",0,0)
		self.dict_all['grade'] = {'all':self.grade_all,'dict':self.grade_vars}
		# Make seeing Frame
		self.seeing_vars,self.seeing_all = self.make_newFrame(tab_1,seeing,"Seeing",0,1)
		self.dict_all['seeing'] = {'all':self.seeing_all,'dict':self.seeing_vars}
		# Make transp Frame
		self.transp_vars,self.transp_all = self.make_newFrame(tab_1,transp,"Transparency",1,0)
		self.dict_all['transp'] = {'all':self.transp_all,'dict':self.transp_vars}
		# Make transp Frame
		self.airmass_vars,self.airmass_all = self.make_newFrame(tab_1,airmass,"Airmass",1,1)
		self.dict_all['airmass'] = {'all':self.airmass_all,'dict':self.airmass_vars}

		# Show only observable OBs checkbox
		self.unobserved_obs = tk.IntVar()
		self.unobserved_obs.set(1)
		ttk.Checkbutton(tab_1,text="Only Unobserved OBs",variable=self.unobserved_obs).grid(sticky=tk.W,padx=13,pady=5,columnspan=2)

		# Show only Time Constraint OBs checkbox
		self.timewindow_obs = tk.IntVar()
		self.timewindow_obs.set(0)
		ttk.Checkbutton(tab_1,text="Only OBs with Time Windows",variable=self.timewindow_obs).grid(sticky=tk.W,padx=13,pady=5,columnspan=2)

		# TAB 2 HSC Filters
		# Make BB Filter Frame
		self.bbfilt_vars,self.bbfilt_all = self.make_newFrame(tab_2,bbfilters,"Broad Band",0,0)
		self.dict_all['bbfilters'] = {'all':self.bbfilt_all,'dict':self.bbfilt_vars}
		# Make BB Filter Frame
		self.nbfilt_vars,self.nbfilt_all = self.make_newFrame(tab_2,nbfilters,"Narrow Band",0,1)
		self.dict_all['nbfilters'] = {'all':self.nbfilt_all,'dict':self.nbfilt_vars}

		# TAB 3 Options
		pathframe = ttk.LabelFrame(tab_3,text="Select Programs",labelanchor='n',borderwidth=2)
		pathframe.grid(sticky='news',columnspan=3,padx=5,pady=5)
		# Radio button
		self.progpathmode = tk.IntVar()
		self.progpathmode.set(1)
		ttk.Radiobutton(pathframe, text="", variable=self.progpathmode, value=1).grid(row=0,column=0,padx=(5,3),pady=15)
		# Create the 'Load Programs Path' button.
		loadpath_frame = ttk.Frame(pathframe)
		loadpath_frame.grid(row=0,column=1,sticky='news')
		loadfilebutton = ttk.Button(loadpath_frame, text='From File', command=self.load_file_path)
		loadfilebutton.grid(sticky='w', padx=2,pady=15)
		Hovertip(loadfilebutton, "Select path to the 'programs.xlsx' spreadsheet file\n\nThe individual program spreadsheet files for the\n"+
			                      "semester should be in same directory.",hover_delay=500)
		self.filepath_entry = ttk.Entry(pathframe,textvariable=self.filepath_text,background='white',foreground='black',width=15)
		self.filepath_entry.grid(row=0,column=2,sticky='news',pady=15,padx=3)
		self.filepath_entry.insert(0,hscqueueconfig.programfilepath)
		Hovertip(self.filepath_entry, "Select path to the 'programs.xlsx' spreadsheet file\n\nThe individual program spreadsheet files for the\n"+
			                          "semester should be in same directory.",hover_delay=500)
		# Filter by Semesters Entry
		ttk.Radiobutton(pathframe, text="", variable=self.progpathmode, value=2).grid(row=1,column=0,padx=(5,3),pady=15)
		ttk.Label(pathframe,text="Filter by Sem:").grid(row=1,column=1,sticky='w',padx=4,pady=(10,1))
		semester_entry = ttk.Entry(pathframe,textvariable=self.semester_text,background='white',foreground='black',width=15)
		semester_entry.grid(row=1,column=2,sticky='news',pady=(15,10),padx=3)
		semester_entry.insert(0,hscqueueconfig.current_semester)
		ttk.Label(pathframe,text="(use commas for list)",font=('Sans',9)).grid(row=2,column=2,sticky='w',padx=10,pady=0)
		# Load Schedule file button
		schedulefilepath = ttk.Button(tab_3, text='Schedule File path:', command=self.load_schedfile_path)
		schedulefilepath.grid(row=2, sticky='w', padx=5,pady=15)
		Hovertip(schedulefilepath, "Select path to the 'schedule.xlsx'\nspreadsheet file",hover_delay=500)
		self.schedpath_entry = ttk.Entry(tab_3,textvariable=self.schedpath_text,background='white',foreground='black',width=15)
		self.schedpath_entry.grid(row=2,column=2,sticky='news',pady=15,padx=3)
		self.schedpath_entry.insert(0,hscqueueconfig.schedulefilepath)
		Hovertip(self.schedpath_entry, "Select path to the 'schedule.xlsx'\nspreadsheet file",hover_delay=500)
		# Maximum OBs displayed per Program
		ttk.Label(tab_3,text="Max OBs number:").grid(row=3,column=0,sticky='w',padx=6,pady=(10,1))
		maxOBdisplay_entry = ttk.Entry(tab_3,textvariable=self.maxOBdisp_text,background='white',foreground='black',width=7)
		maxOBdisplay_entry.grid(row=3,column=1,sticky='w',pady=(15,6),padx=5,columnspan=2)		
		maxOBdisplay_entry.insert(0,hscqueueconfig.maxobquery)
		Hovertip(maxOBdisplay_entry, "Maximum number of OBs\nper Program in Query.\nThe remaining qualifying OBs\nwill be IGNORED.",hover_delay=500)

		ttk.Button(tab_3, text='Set as Default', command=self.set_as_default).grid(sticky='e', padx=8,pady=15,column=2)

		#################################### Create the Plot Section. Frame and LabelFrame and buttons  ###########################################
		PlotFrame = ttk.Frame(self)
		PlotFrame.grid(sticky='news',columnspan=2)

		PlotFrame = ttk.LabelFrame(PlotFrame,text="Plot",labelanchor='n',borderwidth=3)
		PlotFrame.grid(sticky='news',padx=10,pady=2)

		self.display = tk.StringVar()
		menuframe = ttk.Frame(PlotFrame)
		menuframe.grid(row=0,column=0,columnspan=2,sticky='news',pady=5)
		ttk.Label(menuframe,text="Y Axis:").grid(row=0,column=0,sticky='w',padx=2)
		dispmenu = ttk.OptionMenu(menuframe, self.display,"OBs", "OBs", "program", "number", "time sum")
		dispmenu.grid(row=0,column=1,padx=1,sticky='w')
		dispmenu.config(width=6)
		Hovertip(dispmenu, "--OBs: Display all OBs based on selection criteria\n--program: Group all OBs into their programs\n"\
			               "--number: Display number of observable OBs per night\n--time sum: Combined total time of all qualifying OBs",hover_delay=500)

		self.groupby = tk.StringVar()
		menuframe = ttk.Frame(PlotFrame)
		menuframe.grid(row=1,column=0,columnspan=2,sticky='news')
		ttk.Label(menuframe,text="Group by:").grid(row=0,column=0,sticky='w',padx=2)
		groupmenu = ttk.OptionMenu(menuframe, self.groupby,"program", *label_dic)
		groupmenu.grid(row=0,column=1,padx=1,sticky='w')
		groupmenu.config(width=7)
		s2 = ttk.Style()
		s2.configure('my2.TButton',foreground = 'blue',font=('Sans',12,'bold'))			
		updatebut = ttk.Button(menuframe, style='my2.TButton' , text='Update', command=self.call_plot_function)
		updatebut.grid(row=0,column=2,padx=(6,3),pady=0,sticky='w')
		updatebut.config(width=6)


		startdateframe = ttk.Frame(PlotFrame)
		startdateframe.grid(row=2,column=0,sticky='news')
		ttk.Label(startdateframe,text='From').grid()
		self.startdate = DateEntry(startdateframe, width=9, borderwidth=2)
		self.startdate.grid(padx=(10,1))
		self.startdate._top_cal.overrideredirect(False)

		enddateframe = ttk.Frame(PlotFrame)
		enddateframe.grid(row=2,column=1,sticky='news')
		ttk.Label(enddateframe,text='Until').grid()
		self.enddate = DateEntry(enddateframe, width=9, borderwidth=2)
		self.enddate.set_date(self.startdate.get_date()+timedelta(days=13))
		self.enddate.grid(padx=(1,10))
		self.enddate._top_cal.overrideredirect(False)

		# Create the 'show' button.
		showframe = ttk.Frame(PlotFrame)
		showframe.grid(row=3,column=0,columnspan=2,sticky='news')
		s = ttk.Style()
		s.configure('my.TButton',background = 'deep sky blue')		
		show_button = ttk.Button(showframe, style='my.TButton', text='                     Show OBs                     ', command=self.show_programs)
		show_button.grid(padx=10,pady=5,sticky='ew')


		# Show only "Queue nights" checkbox
		self.plot_queue_nights_only = tk.IntVar()
		self.plot_queue_nights_only.set(1)
		queue_only_button = ttk.Checkbutton(PlotFrame,text="Only Scheduled Queue Nights",variable=self.plot_queue_nights_only)
		queue_only_button.grid(row=4,column=0,sticky=tk.W,padx=13,pady=5,columnspan=2)	
		Hovertip(queue_only_button, "This will make the Figure show visibility only\nduring the Queue night runs according to the schedule.",hover_delay=500)
		###########################################  Select All and Quit Buttons  ################################################

		# Create the 'Select All' button.
		selectall_frame = ttk.Frame(self)
		selectall_frame.grid(row=5,column=0,sticky='news')
		selectall_button = ttk.Button(selectall_frame, text='(Un)Select All', command=self.select_all_all)
		selectall_button.grid(sticky='w', padx=20,pady=20)

		# Create the 'Quit' button.
		quit_frame = ttk.Frame(self)
		quit_frame.grid(row=5,column=1,sticky='news')
		quit_button = ttk.Button(quit_frame, text='Quit', command=self.destroy_)
		quit_button.grid(column=1,sticky='e', padx=2,pady=20)

		###########################################   Progress Bar ###############################################################

		bar_frame = ttk.Frame(self)
		bar_frame.grid(row=6,column=0,sticky='news',columnspan=2)
		self.pb = ttk.Progressbar(
		    bar_frame,
		    orient='horizontal',
		    mode='determinate',
		    length=270
		)	
		self.pb.grid(sticky='news',padx=10,pady=(0,5),columnspan=2)
		self.pb['value'] = 0

		##########################################################################################################################

		# Make All selected by default
		self.select_all_all()
		# Make Grade AB show by default
		self.dict_all['grade']['dict']['Grade C'].set(0)
		self.dict_all['grade']['dict']['Grade F'].set(0) 

	def make_newFrame(self,tab,option_list,labelname,gridx,gridy):

		newFrame = ttk.LabelFrame(tab,text=labelname)
		newFrame.grid(row=gridx,column=gridy,padx=10,pady=10,sticky=tk.NW)
		# create checkbuttons
		var_dict = {}
		for option in option_list:
			var = tk.IntVar()
			ttk.Checkbutton(newFrame,text=option,variable=var).grid(sticky=tk.W)
			var_dict[option] = var
		sall = tk.IntVar()
		ttk.Checkbutton(newFrame,text="(Un)Select All",command=self.select_all,var=sall).grid()
	
		return var_dict,sall

	def select_all(self):

		for key in self.dict_all:
			all_box = self.dict_all[key]['all']
			if all_box.get()==True:
				var_dict = self.dict_all[key]['dict']
				all_on = True
				for butt in var_dict:
					butt = var_dict[butt]
					if not butt.get():
						all_on = False
						butt.set(1)
				if all_on:
					for butt in var_dict:
						butt = var_dict[butt]
						butt.set(0)
			all_box.set(0)    # return the "select all" box to unchecked. 			

	def select_all_all(self):

		all_on = True
		for key in self.dict_all:
			var_dict = self.dict_all[key]['dict']
			for butt in var_dict:
				butt = var_dict[butt]
				if not butt.get():
					all_on=False
					butt.set(1)
		if all_on:
			for key in self.dict_all:
				var_dict = self.dict_all[key]['dict']
				for butt in var_dict:
					butt = var_dict[butt]
					butt.set(0)

	def load_file_path(self):

		self.filepath = tk.filedialog.askopenfilename(title='Select path to Programs file',initialdir='./')
		self.filepath_entry.delete(0,tk.END)
		self.filepath_entry.insert(0,self.filepath)

	def load_schedfile_path(self):

		self.filepath = tk.filedialog.askopenfilename(title='Select path to Schedule file',initialdir='./')
		self.schedpath_entry.delete(0,tk.END)
		self.schedpath_entry.insert(0,self.filepath)

	def get_schedule_df(self):
		df = pd.read_excel(self.schedpath_text.get(),engine='openpyxl') 
		df["start_dt"] = pd.to_datetime(df['date'].astype(str)+' '+df['start time'].astype(str))
		df["end_dt"] = pd.to_datetime(df['date'].astype(str)+' '+df['end time'].astype(str))
		df['start_dt'] = df['start_dt'].dt.tz_localize(local)
		df['end_dt'] = df['end_dt'].dt.tz_localize(local)				
		df = df.sort_values(by='start_dt',ascending=True,ignore_index=True)
		df['end_dt'] = df.apply(lambda x: x['end_dt']+timedelta(days=1) if x['end_dt']<x['start_dt'] else x['end_dt'] ,axis=1)
		df['obs_night'] = pd.to_datetime(df.apply(lambda x: x['start_dt'].date()-timedelta(days=1) if x['start_dt'].time()<datetime.time(8,0) else x['start_dt'].date(), axis=1))
		return df		

	def set_as_default(self):

		if not self.maxOBdisp_text.get().isdecimal(): 
			tk.messagebox.showerror("Error", "    Max OB number has to be numeric")
			return
		with open('hscqueueconfig.py','r') as configfile:
			filedata = configfile.read()
		filedata = filedata.replace('current_semester = "'+hscqueueconfig.current_semester+'"','current_semester = "'+self.semester_text.get()+'"')
		filedata = filedata.replace('programfilepath = "'+hscqueueconfig.programfilepath+'"','programfilepath = "'+self.filepath_text.get()+'"')
		filedata = filedata.replace('schedulefilepath = "'+hscqueueconfig.schedulefilepath+'"','schedulefilepath = "'+self.schedpath_text.get()+'"')		
		filedata = filedata.replace('maxobquery = '+str(int(hscqueueconfig.maxobquery)),'maxobquery = '+self.maxOBdisp_text.get())
		with open('hscqueueconfig.py','w') as configfile:
			filedata = configfile.write(filedata)
		importlib.reload(hscqueueconfig)	



	def show_programs(self):
		
		# Check Dates
		if self.enddate.get_date() < self.startdate.get_date():
			tk.messagebox.showerror("Dates Error", "Error: 'Until' Date must be later or equal to 'From' Date.")
			return None		# Exit function 

		# Get the Queue night schedule from Schedule File
		if self.plot_queue_nights_only.get()==True:
			try:
				self.queuenightschedule_df = self.get_schedule_df()
			except Exception:
				tk.messagebox.showerror("Error", "Error: Cannot load the schedule spreadsheet file.")
				traceback.print_exc()				
				return None     # Exit function
			# check if period has queue nights	
			if not any([(obs_night>=self.startdate.get_date() and obs_night<=self.enddate.get_date()) for obs_night in self.queuenightschedule_df['obs_night']]):
				tk.messagebox.showerror("Dates Error", "Error: The selected date period does not contain any scheduled Queue nights.")
				return None		# Exit function 
		else:
			self.queuenightschedule_df = None

		print("")
		print("== Searching Programs in QDB...")		
		# Get the OBs from database
		self.call = qplancaller.Call(
			self.dict_all,self.semester_text.get(),self.filepath_text.get(),
			self.progpathmode.get(),self.maxOBdisp_text.get(),self.timewindow_obs.get()
			)
		notfound = self.call.connect()
		if notfound:
			tk.messagebox.showerror("Error", "Error: The QDB access file was not found.\n\nPlease check the file name on 'hscqueueconfig.py'\nand restart qvis if needed.")
			return None		# Exit function if cannot connect to database

		pgms = self.call.get_programs()
		if pgms==None: 
			tk.messagebox.showerror("Error", "Error: No Programs found.\n\n\t\tPlease check your network\n\t\tor Programs File.")
			return None		# Exit function if cannot connect to database

		# Get Programs spreadsheet files if available
		nofiles = []
		for pgm in pgms:
			try:
				xls = pd.ExcelFile(self.filepath_text.get().split('programs.xlsx')[0]+'/'+pgm.proposal+'.xlsx',engine='openpyxl')
				df1 = pd.read_excel(xls, 'ob')
				df1 = df1.loc[df1.Code.notna()]
				pgm.spsheet_obs = df1.Code.values
			except Exception:
				traceback.print_exc()
				nofiles.append(pgm.proposal)
				pgm.spsheet_obs = None
		if len(nofiles)>0:	
			tk.messagebox.showinfo("Warning", "Warning: Could not open spreadsheet files for following Programs:\n\n\t\t"+"\n\t\t".join(nofiles)+
				                   "\n\nOBs will be obtained from DB, and may include OBs from older semesters.")
			self.update()


		# Get all OBs 
		t0 = time.time()
		obs = self.call.get_obs()		
		if self.unobserved_obs.get(): 
			obs = self.call.get_observable_obs()	# Filter by observable obs
		if len(obs)==0:
			tk.messagebox.showerror("Error", "Error: No OBs found.\n\n\t\tPlease check your conditions.")
			return None		# Exit function if cannot get any OBs
		print("")
		print("== QDB == : %i OBs found [Query: %.1f millisec/OB]" % (len(obs),1000*(time.time()-t0)/int(len(obs))))
		print("")

		# Open Message Box Info
		if len(self.call.skipped_pgm)>0:
			list_text = ''
			for pgm in self.call.skipped_pgm:
				list_text += pgm+'\n'
			tk.messagebox.showinfo("Message","The Max OB number was reached\nfor the following Programs:\n\n"+list_text+"\n(remaining qualifying OBs were IGNORED)")
			self.update()

		# Create the DataFrames
		self.tablecount += 1
		df,df_pgm =  self.call.build_df()

		# Initialize the plot object
		self.plot = qplan_plotter.Plot(df,df_pgm,self,self.tablecount,self.startdate.get_date(),self.enddate.get_date())
		# Calculate the visibility windows
		print("== Calculating the visibility...")
		print("")
		self.plot.calculate_windows()

		# Create the Figure object
		self.plot.create_plot()

		print("\n")
		print("== Loading the figure...")
		print("")
		# Call the plot functions
		self.call_plot_function()

		# Open the PandasTable object
		tablewindow.opentable(df,self,self.tablecount)

	def call_plot_function(self):

		time.sleep(0.2)
		try:
			if self.display.get()=="OBs":
				self.plot.fill_plot(label_dic[self.groupby.get()])
			elif self.display.get()=="program":
				self.plot.fill_plot_prog(label_dic[self.groupby.get()])
			elif self.display.get()=="number":
				self.plot.fill_plot_num(label_dic[self.groupby.get()])							
			elif self.display.get()=="time sum":
				self.plot.fill_plot_TotTime(label_dic[self.groupby.get()])
		except AttributeError:
			tk.messagebox.showerror("Error", "Error: There are no open plots.")							
		except Exception:
			 traceback.print_exc()
		
	def destroy_(self):
		plt.close('all')
		print("")
		print("  Good Bye")
		print("")
		self.destroy()


if __name__ == '__main__':
	panel = Panel()
	panel.mainloop()