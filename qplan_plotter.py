import matplotlib.dates as dt
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.patches as mpatches
from matplotlib.ticker import FuncFormatter
from matplotlib.widgets import Cursor
import pytz
local = pytz.timezone("US/Hawaii")
from datetime import time as timefunc
from datetime import datetime,timedelta
import time as clock
from qplan.common import moon
from qplan.util.site import get_site
from qplan.entity import StaticTarget
import airmass_plot
subaru = get_site('subaru')
import matplotlib
matplotlib.use("TkAgg") # set the backend
import pandas as pd
import numpy as np

minute_delta = 5   # frequency of elevation data in minutes
gridfreq = 5		# frequency in minutes of the date grid for x-axis in plots.
dark_moon_limit = 0.15   # maximum moon illumination fraction for 'dark' time
gray_moon_limit = 0.77   # maximum moon illumination fraction for 'gray' time
morning_cut = timefunc(7,30)        # the visibility plots will ignore times after this hour in the morning 
evening_cut = timefunc(17,30)		 # the visibility plots will ignore times before this hour in the evening



#####################################################################
class night_window:
	def __init__(self,sdate,df,targets,request_windows,queuenightschedule_df):

		self.use_queue_schedule = (queuenightschedule_df is not None)
		start = sdate.strftime("%Y-%m-%d %H:%M")
		self.start = subaru.get_date(start)
		self.end = self.start+timedelta(days=1)
		subaru.set_date(self.start)
		self.sunset = subaru.sunset()
		self.evt12 = subaru.evening_twilight_12()
		self.evt18 = subaru.evening_twilight_18()
		self.mot12 = subaru.morning_twilight_12()
		self.mot18 = subaru.morning_twilight_18()
		self.next_sunrise = subaru.sunrise()
		subaru.set_date(self.start-timedelta(hours=12))	# a fix so that we get the sunrise of the same day, instead of next morning.
		self.sunrise = subaru.sunrise()
		if self.use_queue_schedule:
			self.queue_night_limits = self.get_queue_night_limits(queuenightschedule_df)
		self.targ_dic = {}
		self.targ_observable = []
		for i,target in enumerate(targets):

			observable = False
			visible = False
			SkyOk = False
			if self.use_queue_schedule:
				time = self.queue_night_limits[0]
			else:
				time = self.sunset
			target_min_el = df.telcfg_min_el[i] 
			max_airmass = df.envcfg_airmass[i]
			moon = df.envcfg_moon[i]
			moon_sep = df.envcfg_moon_sep[i]
			this_key = df.program[i]+df.target_name[i]+moon+str(moon_sep)+str(request_windows[i][0])+str(request_windows[i][1])
			if not this_key in self.targ_dic:

				self.targ_dic[this_key] = {}
				self.targ_dic[this_key]['df'] = df.iloc[i,:] 

				while (time<self.end):
					info = subaru.calc(target, subaru.get_date(time.strftime("%Y-%m-%d %H:%M")))						
					if not self.inside_time_window(time,request_windows[i]):
						time = time + timedelta(minutes=minute_delta)	
						continue	
					if not SkyOk:
						if self.sky_ok(info,moon_sep,moon):
							SkyOk = True
					if info.alt_deg>=target_min_el and info.airmass<=max_airmass and SkyOk and not visible:
						self.targ_dic[this_key]['window_start'] = time
						observable = True
						visible = True	
					if info.airmass>max_airmass and visible:
						self.targ_dic[this_key]['window_end'] = time
						break								
					if info.alt_deg<target_min_el and visible:
						self.targ_dic[this_key]['window_end'] = time
						break		
					if time>=self.next_sunrise and visible:
						self.targ_dic[this_key]['window_end'] = time
						break			
					if self.use_queue_schedule and visible:
						if time>=self.queue_night_limits[1]:
							self.targ_dic[this_key]['window_end'] = time
							break										
					if time>=self.next_sunrise and not visible:
						break
					if SkyOk:
						if not self.sky_ok(info,moon_sep,moon):
							self.targ_dic[this_key]['window_end'] = time
							break
					time = time + timedelta(minutes=minute_delta)	
				if not observable:
					self.targ_dic[this_key]['window_start'] = None
					self.targ_dic[this_key]['window_end'] = None
			elif not self.targ_dic[this_key]['window_start'] == None:
				observable = True

			self.targ_observable.append(observable)
			print("  ",self.start.strftime("%m-%d-%Y....."),str(i+1).rjust(4),"OBs done",end='\r')

	def sky_ok(self,info,moon_sep,moon):
		if moon=='dark' and self.dark_time(info,moon_sep):
			return True
		if moon=='gray' and (self.dark_time(info,moon_sep) or self.gray_time(info,moon_sep)):
			return True
		return False

	def dark_time(self,info,moon_sep):
		if info.moon_pct<=dark_moon_limit or info.moon_alt<=-0.5:
			if info.moon_sep>=moon_sep:
				return True
		return False 

	def gray_time(self,info,moon_sep):
		if info.moon_pct<=gray_moon_limit and info.moon_alt>-0.5:
			if info.moon_sep>=moon_sep:
				return True
		return False 		

	def inside_time_window(self,time,request_windows):
		if pd.isnull(request_windows[0]) and pd.isnull(request_windows[1]):
			return True
		elif (not pd.isnull(request_windows[0])) and (not pd.isnull(request_windows[1])):
			mindate,maxdate = request_windows[0].astimezone(local),request_windows[1].astimezone(local)
			if time>=mindate and time<=maxdate:
				return True
			else:
				return False
		elif pd.isnull(request_windows[0]) and (not pd.isnull(request_windows[1])):
			maxdate = request_windows[1].astimezone(local)
			if time<=maxdate:
				return True
		elif (not pd.isnull(request_windows[0])) and pd.isnull(request_windows[1]):
			mindate = request_windows[0].astimezone(local)
			if time>=mindate:
				return True
		return False

	def get_queue_night_limits(self,df):
		df = df.loc[(self.sunset<=df['start_dt']) & (self.next_sunrise>=df['end_dt'])]		
		if len(df)==0:									# No Queue runs tonight...
			return (self.end ,self.end)					# This makes the While Loop end before starting, and on to the next night...
		else:
			return (df.start_dt.min(),df.end_dt.max())  # in case there are more than 1 queue windows in the same night


###################################################################################
class Plot:
	def __init__(self,df,df_pgm,root,tablecount,start_date,end_date):

		self.df = df 
		self.df_pgm = df_pgm
		self.root = root
		self.queuenightschedule_df = self.root.queuenightschedule_df
		self.targ_observable = []
		self.nightvis_info = {}
		self.figcount = tablecount
		self.sdate = datetime(start_date.year,start_date.month,start_date.day)-timedelta(hours=12)
		self.edate = datetime(end_date.year,end_date.month,end_date.day)+timedelta(hours=36)
		self.date_grid = self.create_date_grid()
		self.nights_list = self.get_nights_list()
		self.root.pb['maximum'] = (self.edate - self.sdate).days+1   # add extra day to make progress bar end after the final night
		self.targets = [ StaticTarget(name=name, ra=ra, dec=dec) for name,ra,dec in zip(self.df.target_name,self.df.target_ra,self.df.target_dec)]
		self.request_windows = [(mindate,maxdate) for mindate,maxdate in zip(self.df.envcfg_lower_time_limit,self.df.envcfg_upper_time_limit)]

	def create_date_grid(self):
		sdate = self.sdate
		edate = self.edate
		daterange_plot = pd.date_range(sdate,edate,freq=str(gridfreq)+'min',tz=None)
		date_ls = [date for date in daterange_plot if (date.time()<=morning_cut or date.time()>=evening_cut)]
		if self.queuenightschedule_df is not None:	# case when only queue nights are used in plot
			obs_nights = [ (date.date() if date.time()>=evening_cut else (date.date()-timedelta(days=1) if date.time()<=morning_cut else None) ) for date in date_ls]
			# keep timestamp only if corresponds to an observing night from queue schedule
			date_ls = [date for date,obs_night in zip(date_ls,obs_nights) if obs_night in self.queuenightschedule_df['obs_night'].dt.date.values ]	
		date_grid = pd.Index(date_ls)
		return date_grid

	def get_nights_list(self):
		nights = pd.date_range(self.sdate.date(),self.edate.date(),freq='1D',tz=None)
		if self.queuenightschedule_df is not None:	# case when using only queue nights
			nights = [night for night in nights if night in self.queuenightschedule_df['obs_night'].dt.date.values]
		return nights

	def create_plot(self):	
		plt.ion()
		plt.style.use('seaborn-ticks')
		self.fig, self.ax = plt.subplots(figsize=(17, 10))	
		self.fig.canvas.manager.set_window_title('HSC Queue Visualization Figure '+str(self.figcount))
		self.fig.canvas.manager.window.wm_geometry("+320+00") # move the window
		self.cid = self.fig.canvas.mpl_connect('button_press_event', self.onclick)	

	def onclick(self,event):
		if event.dblclick:
			ix, iy = event.xdata, event.ydata
			ylabels = self.ax.get_yticklabels()
			label = ylabels[int(round(iy))].get_text()
			date = self.date_grid[int(ix)] - timedelta(days=1)   # subtract one day so that it plots the correct night

			if self.plottype=='OB':
				targs = self.targets[np.where(self.df.name==label)[0][0]]
				airmass_plot.plot_target(self.root,targs,date,label)
			if self.plottype=='prog':
				ind = np.where(self.df.program==label)[0]
				targs = [self.targets[i] for i in ind]
				airmass_plot.plot_prog_targs(self.root,targs,date,label)

	def calculate_windows(self):
		time = self.sdate
		while time <= self.edate:
			nw = night_window(time,self.df,self.targets,self.request_windows,self.queuenightschedule_df)
			self.nightvis_info[time.strftime("%y-%m-%d")] = nw
			self.targ_observable.append(nw.targ_observable)
			time = time + timedelta(days=1)
			self.update_progbar(time)

	def update_progbar(self,time):

		self.root.pb['value'] = (time - self.sdate).days
		self.root.update()

	def time2grid(self,time):
		if time is None:
			return 0
		newtime = time.replace(tzinfo=None)		
		ind = self.date_grid.get_loc(newtime, method='nearest')
		if self.date_grid[ind]>=newtime:
			diff = (self.date_grid[ind]-newtime).seconds
			eff_ind = ind-(diff/(gridfreq*60.)) if diff<(gridfreq*60.) else ind
		else:
			diff = (newtime-self.date_grid[ind]).seconds
			eff_ind = ind+(diff/(gridfreq*60.)) if diff<(gridfreq*60.) else ind
		return eff_ind

	def date_ax(self,fig, ax, dates, fmt='%b %d %H:%M'): 
		N = len(dates)
		def format_date(index, pos):
			index = np.clip(int(index + 0.5), 0, N - 1)
			return dates[index].strftime(fmt)
		ax.xaxis.set_major_formatter(FuncFormatter(format_date))

#####################################################################   Plot Display Options ########################################################################################
#####################################################################################################################################################################################
	def fill_plot(self,group_by):

		groups = np.sort(self.df[group_by].unique()) if group_by=="completion_rate" else self.df[group_by].unique()
		colors = cm.rainbow(np.linspace(0, 1, len(groups)))
		colors_ = colors[[np.where(groups==g)[0][0] for g in self.df[group_by]]]

		self.fig.clf()
		self.ax = self.fig.add_subplot(111)		
		self.plottype = "OB"

		def this_key(i,program,this_df):
			return program+this_df.target_name[i]+this_df.envcfg_moon[i]+str(this_df.envcfg_moon_sep[i])+str(self.request_windows[i][0])+str(self.request_windows[i][1])

		time = self.sdate
		while time <= self.edate:
			nw = self.nightvis_info[time.strftime("%y-%m-%d")]
			if time.date() in self.nights_list:		# Only draw visibility windows if night is within the queried period (case of schedule only)
				self.ax.hlines(self.df.name,
					[self.time2grid(nw.targ_dic[this_key(i,program,self.df)]['window_start']) for i,program in enumerate(self.df.program)],
					[self.time2grid(nw.targ_dic[this_key(i,program,self.df)]['window_end']) for i,program in enumerate(self.df.program)],				
					linewidth=6,alpha=0.6,color=colors_)
			self.ax.fill_betweenx(y=(-5,len(self.df.name)+5),x1=self.time2grid(nw.sunrise),x2=self.time2grid(nw.sunset),facecolor='gray',alpha=0.2)
			self.ax.fill_betweenx(y=(-5,len(self.df.name)+5),x1=self.time2grid(nw.sunset),x2=self.time2grid(nw.evt12),facecolor='mediumslateblue',alpha=0.3)
			self.ax.fill_betweenx(y=(-5,len(self.df.name)+5),x1=self.time2grid(nw.evt12),x2=self.time2grid(nw.evt18),facecolor='royalblue',alpha=0.7)
			self.ax.fill_betweenx(y=(-5,len(self.df.name)+5),x1=self.time2grid(nw.mot18),x2=self.time2grid(nw.mot12),facecolor='royalblue',alpha=0.7)
			self.ax.fill_betweenx(y=(-5,len(self.df.name)+5),x1=self.time2grid(nw.mot12),x2=self.time2grid(nw.next_sunrise),facecolor='mediumslateblue',alpha=0.3)
			time = time + timedelta(days=1)

		patches = [mpatches.Patch(color=color, label=key, alpha=0.8) for (key, color) in zip(groups,colors)]
		if len(patches)>20: plt.legend(handles=patches, bbox_to_anchor=(1, 1), loc='upper left',title=group_by,ncol=2)	
		else: plt.legend(handles=patches, bbox_to_anchor=(1, 1), loc='upper left',title=group_by)
		self.date_ax(self.fig,self.ax,self.date_grid)
		ind00hr = np.where((self.date_grid.hour==0) & (self.date_grid.minute==0))[0]
		self.ax.xaxis.set_ticks(ind00hr)
		plt.xlim(self.time2grid(self.sdate+timedelta(hours=24)),self.time2grid(self.edate))
		plt.xticks(rotation=45)
		plt.xlabel("Time (HST)")
		plt.tight_layout()
		plt.ylim(-1,len(self.ax.get_yticklabels()))
		self.ax.xaxis.grid(True)
		self.ax.tick_params(top=False,right=False)
		plt.show()
		
	def fill_plot_prog(self,group_by):

		self.fig.clf()
		self.ax = self.fig.add_subplot(111)			
		self.plottype = "prog"

		def this_key(i,program,this_df,request_windows_):
			return program+this_df.target_name[i]+this_df.envcfg_moon[i]+str(this_df.envcfg_moon_sep[i])+str(request_windows_[i][0])+str(request_windows_[i][1])

		programs = self.df.program.unique()	
		groups = np.sort(self.df[group_by].unique()) if group_by=="completion_rate" else self.df[group_by].unique()
		colors = cm.rainbow(np.linspace(0, 1, len(groups)))	
		prgm_obs = {}
		for pgm in programs:	
			dfpgm = self.df.loc[self.df.program==pgm].reset_index(drop=True)
			request_windows_ = np.array(self.request_windows)[self.df.program==pgm]
			colors_ = colors[[np.where(groups==g)[0][0] for g in dfpgm[group_by]]]
			time = self.sdate
			while time <= self.edate:
				nw = self.nightvis_info[time.strftime("%y-%m-%d")]

				# Draw the shades and lines only once per night.
				if pgm==programs[0]:
					self.ax.fill_betweenx(y=(-5,len(programs)+5),x1=self.time2grid(nw.sunrise),x2=self.time2grid(nw.sunset),facecolor='gray',alpha=0.2)
					self.ax.fill_betweenx(y=(-5,len(programs)+5),x1=self.time2grid(nw.sunset),x2=self.time2grid(nw.evt12),facecolor='mediumslateblue',alpha=0.3)
					self.ax.fill_betweenx(y=(-5,len(programs)+5),x1=self.time2grid(nw.evt12),x2=self.time2grid(nw.evt18),facecolor='royalblue',alpha=0.7)
					self.ax.fill_betweenx(y=(-5,len(programs)+5),x1=self.time2grid(nw.mot18),x2=self.time2grid(nw.mot12),facecolor='royalblue',alpha=0.7)
					self.ax.fill_betweenx(y=(-5,len(programs)+5),x1=self.time2grid(nw.mot12),x2=self.time2grid(nw.next_sunrise),facecolor='mediumslateblue',alpha=0.3)


				ind = [i for i,program in enumerate(dfpgm.program) if nw.targ_dic[this_key(i,program,dfpgm,request_windows_)]['window_start'] is not None]
				if len(ind)==0:
					time = time + timedelta(days=1)
					continue
				else:
					prgm_obs.setdefault(pgm,1)
				dfpgm = dfpgm.loc[ind].reset_index(drop=True)	
				request_windows_ = request_windows_[ind]
				if time.date() in self.nights_list:		# Only draw visibility windows if night is within the queried period (case of schedule only)
					self.ax.hlines(dfpgm.program,
						[self.time2grid(nw.targ_dic[this_key(i,program,dfpgm,request_windows_)]['window_start']) for i,program in enumerate(dfpgm.program)],
						[self.time2grid(nw.targ_dic[this_key(i,program,dfpgm,request_windows_)]['window_end']) for i,program in enumerate(dfpgm.program)],					
						linewidth=20,alpha=0.4,color=colors_)
				time = time + timedelta(days=1)

		patches = [mpatches.Patch(color=color, label=key) for (key, color) in zip(groups,colors)]
		if len(patches)>20: plt.legend(handles=patches, bbox_to_anchor=(1, 1), loc='upper left',title=group_by,ncol=2)	
		else: plt.legend(handles=patches, bbox_to_anchor=(1, 1), loc='upper left',title=group_by)
		self.date_ax(self.fig,self.ax,self.date_grid)
		ind00hr = np.where((self.date_grid.hour==0) & (self.date_grid.minute==0))[0]
		self.ax.xaxis.set_ticks(ind00hr)		
		plt.xlim(self.time2grid(self.sdate+timedelta(hours=24)),self.time2grid(self.edate))
		plt.xticks(rotation=45)
		plt.xlabel("Time (HST)")
		plt.tight_layout()
		plt.ylim(-1,len(prgm_obs.keys()))
		self.ax.xaxis.grid(True)
		self.ax.tick_params(top=False,right=False)
		plt.show()


	def fill_plot_num(self,group_by):

		groups = np.sort(self.df[group_by].unique()) if group_by=="completion_rate" else self.df[group_by].unique()
		colors = cm.rainbow(np.linspace(0, 1, len(groups)))

		self.fig.clf()
		self.ax = self.fig.add_subplot(111)			
		self.plottype = "number"
		sdate = self.sdate.date()    # We need the time at 00:00.
		edate = self.edate.date()

		number_obs_OB_gg = []
		for k,group in enumerate(groups):
			time = sdate
			number_obs_OB = []
			date = []
			while time <= edate:
				if time not in self.nights_list: time = time + timedelta(days=1); continue
				nw = self.nightvis_info[time.strftime("%y-%m-%d")]
				number_obs_OB.append(sum([bool_ for bool_,g in zip(nw.targ_observable,self.df[group_by]) if g==group]))
				date.append(time)
				time = time + timedelta(days=1)

			number_obs_OB_gg.append(number_obs_OB)
		data_dict = {}
		for group,number_OB_arr in zip(groups,number_obs_OB_gg):
			data_dict[group] = number_OB_arr
		pd.DataFrame(data_dict,index=date)[groups].plot(kind='bar',stacked=True,ax=self.ax)

		plt.legend(bbox_to_anchor=(1, 1), loc='upper left',title=group_by)
		self.date_ax(self.fig,self.ax,date,fmt='%b %d')
		self.ax.xaxis.set_ticks(np.arange(0,len(date)))		
		plt.xticks(rotation=70)
		plt.xlabel("Time (HST)")
		plt.ylabel("Number of Observable OBs")
		plt.tight_layout()
		self.ax.xaxis.grid(True)
		self.ax.yaxis.grid(True)
		self.ax.tick_params(top=False,right=False)
		self.ax.yaxis.get_major_locator().set_params(integer=True)		
		plt.show()

	def fill_plot_TotTime(self,group_by):
		
		self.fig.clf()
		gs = self.fig.add_gridspec(3,1)
		self.ax1,self.ax1 = self.fig.add_subplot(gs[0:1,0]),self.fig.add_subplot(gs[2,0])	

		#####  Top Axis #############################################
		self.ax1 = plt.subplot2grid((3, 1), (0, 0), rowspan=2)
		df = self.df.copy(deep=True)
		df.sort_values(by=['grade','program'],ascending=True,inplace=True)
		if group_by=='inscfg_filter':		
			grade_arr = df.grade.unique()
			df.groupby([group_by,'grade'])['total_time'].sum().div(3600).unstack('grade')[list(grade_arr)].plot(
			kind='bar',stacked=True,ax=self.ax1)	
			plt.legend(bbox_to_anchor=(1, 1), loc='upper left',title='grade')	
			plt.ylabel('Combined OB Total Time (hrs)')
			self.ax1.annotate("(queue operation overhead not included)",xy=(0.01,0.96),xycoords='axes fraction',color='gray')
			plt.xticks(rotation=30)
			plt.tight_layout()
			self.ax1.yaxis.grid(True)
		elif group_by=='program':
			filter_arr = df.inscfg_filter.unique()
			sorted_arr = df.program.unique()				# The df DataFrame has already been sorted by (grade,program).
			df.groupby([group_by,'inscfg_filter'])['total_time'].sum().div(3600).unstack('inscfg_filter')[list(filter_arr)].loc[list(sorted_arr)].plot(
				kind='bar',stacked=True,ax=self.ax1)	
			plt.legend(bbox_to_anchor=(1, 1), loc='upper left',title='inscfg_filter')	
			plt.ylabel('Combined OB Total Time (hrs)')
			self.ax1.annotate("(queue operation overhead not included)",xy=(0.01,0.96),xycoords='axes fraction',color='gray')			
			self.ax1.yaxis.grid(True)
			self.ax1.tick_params(top=False,right=False)			
			plt.xticks(rotation=30)
			plt.tight_layout()
		else:
			filter_arr = df.inscfg_filter.unique()
			df.groupby([group_by,'inscfg_filter'])['total_time'].sum().div(3600).unstack('inscfg_filter')[list(filter_arr)].plot(
				kind='bar',stacked=True,ax=self.ax1)	
			plt.legend(bbox_to_anchor=(1, 1), loc='upper left',title='inscfg_filter')	
			plt.ylabel('Combined OB Total Time (hrs)')
			self.ax1.annotate("(queue operation overhead not included)",xy=(0.01,0.96),xycoords='axes fraction',color='gray')			
			self.ax1.yaxis.grid(True)
			self.ax1.tick_params(top=False,right=False)			
			plt.xticks(rotation=30)
			plt.tight_layout()


		#####  Bottom Axis #############################################
		self.ax2 = plt.subplot2grid((3, 1), (2, 0), rowspan=1)
		grades = self.df_pgm.grade.unique()	
		colors = cm.tab10(np.arange(len(grades)))			
		colors_ = colors[[np.where(grades==g)[0][0] for g in self.df_pgm.grade]]

		df = self.df_pgm.set_index('proposal')
		df[['used_time','total_time']].div(3600).plot(kind='bar',y='total_time',ax=self.ax2,edgecolor=colors_,fill=False)
		for ix,p in enumerate(self.ax2.patches):
			perc = '%.1f' % (df.iloc[ix]['completion_rate'])
			self.ax2.annotate(perc+'%', (p.get_x() + 0.1, p.get_height() + 0.6),weight='bold',size='large',color=colors_[ix])		
		df[['used_time','total_time']].div(3600).plot(kind='bar',y='used_time',ax=self.ax2,color=colors_)
		patches = [mpatches.Patch(color=color, label=key) for (key, color) in zip(grades,colors)]
		plt.legend(handles=patches,bbox_to_anchor=(1, 1), loc='upper left',title='grade')	
		plt.ylabel('Used/Allocated Time (hrs)')
		self.ax2.annotate("(all overheads included)",xy=(0.01,0.92),xycoords='axes fraction',color='gray')					
		self.ax2.yaxis.grid(True)
		self.ax2.tick_params(top=False,right=False)	
		plt.xticks(rotation=30)
		plt.tight_layout()
		plt.xlabel('program')
		plt.ylim(0,df[['total_time']].div(3600).total_time.max()+10)
		plt.show()


