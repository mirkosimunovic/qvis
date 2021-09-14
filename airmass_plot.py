from qplan.util.site import get_site
from qplan.plots import airmass
subaru = get_site('subaru')
from ginga.misc.log import get_logger
from ginga.misc import Bunch
from matplotlib.backends.backend_tkagg import  FigureCanvasTkAgg
import tkinter as tk



def plot_target(root,target,date,obname):
	


	date = date.strftime("%Y-%m-%d %H:%M")
	date = subaru.get_date(date)
	subaru.set_date(date)

	windw = tk.Toplevel(root)
	windw.wm_title(obname)

	target_data = []
	info_list = subaru.get_target_info(target)
	target_data.append(Bunch.Bunch(history=info_list, target=target))	
	    
	logger = get_logger('foo', log_stderr=True)	    
	amp = airmass.AirMassPlot(800, 600, logger=logger)
	canvas = FigureCanvasTkAgg(amp.fig,master=windw)
	amp.plot_altitude(subaru, target_data, subaru.timezone,plot_moon_distance=True)

	canvas.draw()
	canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
	windw.mainloop()


def plot_prog_targs(root,targets,date,program):
	
	date = date.strftime("%Y-%m-%d %H:%M")
	date = subaru.get_date(date)
	subaru.set_date(date)

	windw = tk.Toplevel(root)
	windw.wm_title(program)

	target_data = []
	for tgt in targets:
	    info_list = subaru.get_target_info(tgt)
	    target_data.append(Bunch.Bunch(history=info_list, target=tgt))
	    
	logger = get_logger('foo', log_stderr=True)	    
	amp = airmass.AirMassPlot(800, 600, logger=logger)
	canvas = FigureCanvasTkAgg(amp.fig,master=windw)
	amp.plot_altitude(subaru, target_data, subaru.timezone,plot_moon_distance=True)

	canvas.draw()
	canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
	windw.mainloop()


