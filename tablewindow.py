import tkinter as tk
import tkinter.ttk as ttk
from pandastable import Table, TableModel

default_columns = ['id','program','grade','name','target_name','target_ra','target_dec','inscfg_filter',
                  'inscfg_dither','inscfg_exp_time','envcfg_seeing','envcfg_airmass','envcfg_transparency',
                  'envcfg_moon_sep','envcfg_moon','total_time','completion_rate']

class Window(tk.Toplevel):
        def __init__(self, df,root,tablecount):
            super().__init__()
            self.geometry('1000x350+400+900')
            self.title('Table '+str(tablecount))
            self.df = df 
            self.column_dict = {}
            for key in self.df.columns.values:
            	self.column_dict[key] = tk.IntVar()
            	if key in default_columns:
            		self.column_dict[key].set(1)
            	else:
            		self.column_dict[key].set(0)
          		

            s = ttk.Style()
            s.configure('my.TButton',background = 'deep sky blue')
            col_but = ttk.Button(self,text='Edit Columns', style='my.TButton', command=self.edit_columns).pack(side=tk.TOP, anchor=tk.NE)
            f = tk.Frame(self)
            f.pack(fill=tk.BOTH,expand=1)
            self.table = pt = Table(f, dataframe=self.df[default_columns],
                                    showtoolbar=True, showstatusbar=True)
            pt.show()
            

        def edit_columns(self):
        	self.newwindow = tk.Toplevel(self)
        	self.newwindow.geometry('330x475+1400+900')
        	self.newwindow.title('Edit Columns')
        	self.newwindow.configure(background='white')
        	self.column_dict_edited = self.column_dict.copy()
        	keys = list(self.df.columns.values)
        	numrows = int(len(keys)/2) + len(keys)%int(len(keys)/2)
        	for ix,key in enumerate(keys):
        		col = int(ix>=numrows)
        		var = tk.IntVar()
        		var.set(self.column_dict[key].get())
        		ttk.Checkbutton(self.newwindow,text=key,variable=var).grid(sticky='news',row=ix%numrows,column=max(0,col),padx=5)
        		self.column_dict_edited[key] = var
        	ttk.Button(self.newwindow,text='(Un)Select All',command=self.select_all).grid(sticky='w',row=100,column=0,padx=10,pady=5)	
        	s = ttk.Style()
        	s.configure('my.TButton',background = 'deep sky blue')
        	ttk.Button(self.newwindow, text='Update', style='my.TButton',command=self.update).grid(sticky='e',row=100,column=1,padx=30,pady=5)
        	self.newwindow.mainloop()

        def update(self):
        	self.column_dict = self.column_dict_edited
        	self.new_cols = [col for col in self.column_dict if self.column_dict[col].get()==1]        	
        	self.table.model.df = self.df[self.new_cols]
        	self.table.redraw()
        	self.newwindow.destroy() 

        def select_all(self):
            all_on = True
            for key in self.column_dict_edited:
            	butt = self.column_dict_edited[key]
            	if not butt.get():
            		all_on=False
            		butt.set(1)
            if all_on:
            	for key in self.column_dict_edited:
            		butt = self.column_dict_edited[key]
            		butt.set(0)        	


def opentable(df,root,tablecount):

	app = Window(df,root,tablecount)
	# Run a while loop and exception to avoid crash during scroll wheel event
	while True:
	    try:
	        app.mainloop()
	        break
	    except UnicodeDecodeError:
	        pass

