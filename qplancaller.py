from qplan import q_db,q_query
from ginga.misc.log import get_logger
import os
import pandas as pd
import time


class Call:
	def __init__(self,dict_val,semesters,filepath_text,progpathmode,maxOBquery,timewindow_obs):

		self.dict_val = dict_val
		self.grade = [key for key in self.dict_val['grade']['dict'] if self.dict_val['grade']['dict'][key].get()==1]
		self.seeing = [key for key in self.dict_val['seeing']['dict'] if self.dict_val['seeing']['dict'][key].get()==1]
		self.transp = [key for key in self.dict_val['transp']['dict'] if self.dict_val['transp']['dict'][key].get()==1]
		self.airmass = [key for key in self.dict_val['airmass']['dict'] if self.dict_val['airmass']['dict'][key].get()==1]
		self.bbfilters = [key for key in self.dict_val['bbfilters']['dict'] if self.dict_val['bbfilters']['dict'][key].get()==1]
		self.nbfilters = [key for key in self.dict_val['nbfilters']['dict'] if self.dict_val['nbfilters']['dict'][key].get()==1]
		self.semesters = semesters.split(",")
		self.filepath_text = filepath_text
		self.progpathmode = progpathmode
		self.maxOBquery = int(maxOBquery)
		self.timewindow_obs = timewindow_obs
		self.pgms = []
		self.obs = []
		self.df = []
		self.df_pgm = []
		self.skipped_pgm = []

	def connect(self):

		# create null logger
		logger = get_logger("example1", log_stderr=False)
		# config file for queue db access
		q_conf_file = os.path.join(os.path.abspath('.'), "mirkosm.yml")

		# create handle to queue database (be sure it is running at the chosen address)
		self.qdb = q_db.QueueDatabase(logger)
		self.qdb.read_config(q_conf_file)
		self.qdb.connect()

		# make query object
		self.qa = q_db.QueueAdapter(self.qdb)
		self.qq = q_query.QueueQuery(self.qa)

	def get_programs(self):

		# get programs by program spreadsheet file
		if self.progpathmode==1:
			try:
				df = pd.read_excel(self.filepath_text,engine='openpyxl')
				active_pgms = list(df.proposal)
				self.pgms = [self.qq.get_program(prog) for prog in active_pgms]
			except:
				return None

		# get programs by semester
		elif self.progpathmode==2:
			try:
				self.pgms = list(self.qq.get_program_by_semester(self.semesters))
			except:
				return None

		# Filter by Grade
		newpgms = []
		for pgm in self.pgms:
			if 'Grade '+pgm.grade in self.grade:
				newpgms.append(pgm)
		self.pgms = newpgms

		# Add the Completion rates
		executedOBs = self.get_exec_OBs()
		for pgm in self.pgms:
			key = pgm.proposal
			if key not in executedOBs:
				pgm.completion_rate = 0.0
				pgm.used_time = 0.0
			else:	
				tot_exec_time = sum([executedOBs[key][ob]['total_time'] for ob in executedOBs[key]])
				tot_used_time = (tot_exec_time+tot_exec_time/8.8*1.2) # Add the queue operation overhead time
				pgm.completion_rate = tot_used_time/pgm.total_time*100.
				pgm.used_time = tot_used_time

		return self.pgms

	def get_exec_OBs(self):

			executedOBs = list(self.qq.get_do_not_execute_ob_keys())
			pposals = [pgm.proposal for pgm in self.pgms]
			executedOBs = [OB for OB in executedOBs if OB[0] in pposals]
			if len(executedOBs)>0: 
				executedOBs = list(self.qq._ob_keys_to_obs(executedOBs))
			else:
				return []
			d = dict()
			for rec in executedOBs:
				dd = d.setdefault(rec['program'], dict())
				dd[rec['name']] = dict(total_time=rec['total_time'])
			executedOBs = d
			return executedOBs		

	def get_obs(self):

		# Get all OBs in all programs
		obs_all = []
		for pgm in self.pgms:
			prop = pgm.proposal
			pgm.obs = []
			obs = list(self.qq.get_obs_by_proposal(prop))
			for ob in obs:
				if self.is_ob_ok(ob):
					ob.grade = pgm.grade		# add the grade key to the OB object.
					ob.completion_rate = pgm.completion_rate		# add the grade key to the OB object.
					obs_all.append(ob)
					pgm.obs.append(ob)

		self.obs = obs_all
		self.update_pgms()		# Use the qualifying OBs to update the Program list.
		return self.obs

	def update_pgms(self):		# Remove Programs from Program list that do not have any qualifying OBs.

		newpgms = [ob.program.proposal for ob in self.obs]	
		self.pgms = [pgm for pgm in self.pgms if pgm.proposal in newpgms]	

	def get_observable_obs(self):

		# get OBs that can be observed 
		keys = list(self.qq.get_schedulable_ob_keys())
		keys_names = [key[1] for key in keys]
		obs_all = []
		pgm_count = {}
		for ob in self.obs:
			this_name = ob.name
			num = pgm_count.setdefault(ob.program.proposal,[])
			if len(num)>self.maxOBquery: 		# skip an OB if it exceeds the Max OBs per program
				if ob.program.proposal not in self.skipped_pgm: self.skipped_pgm.append(ob.program.proposal)
				continue
			if this_name in keys_names:
				num += [1,]
				obs_all.append(ob)
		self.obs = obs_all
		return self.obs

	def is_ob_ok(self,ob):

		seeing =   '%.1f' % ob.envcfg.seeing
		airmass =  '%.1f' % ob.envcfg.airmass
		transp =   '%.1f' % ob.envcfg.transparency
		mindate = ob.envcfg.lower_time_limit
		maxdate = ob.envcfg.upper_time_limit
		if self.timewindow_obs and (mindate==None and maxdate==None):	# Reject OB if not time critical 
			return False

		if ob.inscfg.filter.startswith('nb'):
			filters =  'NB'+ob.inscfg.filter.split('nb')[1]
		else:
			filters =  'HSC-'+ob.inscfg.filter
		if seeing in self.seeing:
			if airmass in self.airmass:
				if transp in self.transp:
					if (filters in self.bbfilters or filters in self.nbfilters):
						return True

		return False

	def build_df(self):

		df = {}
		for ob in self.obs:
			dictionary = ob.to_rec()
			for key in dictionary:
				if key.startswith('calib'):		# ignore the 'calib_*' entries.
					continue
				if type(dictionary[key]) is dict:
					for key2 in dictionary[key]:
						if key+'_'+key2 in df:	# check if key already in DataFrame dictionary
							df[key+'_'+key2] += [dictionary[key][key2],]  # add new element to list
						else:
							df[key+'_'+key2] = [dictionary[key][key2]]	# create the columns and add elements
				else:
					if key in df:				# check if key already in DataFrame dictionary
						df[key] += [dictionary[key],]		# add new element to list
					else:
						df[key] = [dictionary[key]]			# create the columns and add elements

		df = pd.DataFrame(df)
		grades = df['grade']				# Retrieve the grade column and move it to the front
		df.drop('grade',axis=1,inplace=True)
		df.insert(2,'grade',grades)
		self.df = df

		df2 = {}
		for pgm in self.pgms:
			dictionary2 = pgm.to_rec()
			for key in dictionary2:
				mylist = df2.setdefault(key,[])
				mylist.append(dictionary2[key])
		self.df_pgm = pd.DataFrame(df2)
		self.df_pgm.sort_values(by=['grade','proposal'],ascending=True,inplace=True)

		return self.df,self.df_pgm





