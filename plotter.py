"""
plotter.py
Author: Alex Walter
Date: Dec 10, 2019

This is a simple pyqtgraph plot that you can run in the background of your code.
Send data to it and it will plot it in real time

"""
import matplotlib
matplotlib.use("Qt5Agg")
import matplotlib.pyplot as plt
import numpy as np
import time
import pickle

class plotter():
    def __init__(self, xData=np.asarray([]), yData=np.asarray([]), yerr=None, xerr=None):
        self.xData = xData
        self.yData = yData
        self.yerr=yerr
        self.xerr=xerr

    def makePlot(self, title='', xlabel='', ylabel=''):
        plt.ion()
        self.fig = plt.figure()
        self.ax = self.fig.gca()
        #self.line, = self.ax.plot(self.xData, self.yData, '.-')
        #self.pltObject = self.ax.errorbar(self.xData, self.yData, self.yerr, self.xerr, fmt='.-')
        self.ax.set_title(title)
        self.ax.set_xlabel(xlabel)
        self.ax.set_ylabel(ylabel)
        #plt.ion()

    def update(self, x, y, yerr=None, xerr=None):
        #print("Updating plot")
        if x is not None and y is not None:
            self.xData = np.append(self.xData, x)
            self.yData = np.append(self.yData, y)
            if yerr is not None:
                if self.yerr is None: self.yerr = np.asarray([])
                self.yerr = np.append(self.yerr, yerr)
            if xerr is not None:
                if self.xerr is None: self.xerr = np.asarray([])
                self.xerr = np.append(self.xerr, xerr)
        #self.ax.plot(self.xData,self.yData)
        #self.line.set_data(self.xData, self.yData)
        if len(self.xData)==1:
            self.pltObject = self.ax.errorbar(self.xData, self.yData, self.yerr, self.xerr, fmt='.-', capsize=2)
        else:
            update_errorbar(self.pltObject, self.xData, self.yData, self.yerr, self.xerr)
        self.ax.relim()  # Recalculate limits
        self.ax.autoscale_view(True, True, True)  # Autoscale
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def block(self):
        plt.ioff()
        plt.show()  # python thread blocks until user closes plot window
        plt.close()

    def save(self, fn):
        pickle.dump(self,fn)
    def load(self, fn):
        old=pickle.load(fn)
        self.xData=old.xData
        self.yData=old.yData
        self.yerr=old.yerr
        self.xerr=old.xerr
        try:
            self.ax=old.ax
            self.fig=old.fig
            self.pltObject=old.pltObject
            plt.block()
        except:
            pass

    def ylog(self):
        self.ax.set_yscale('log')

    def xlog(self):
        self.ax.set_xscale('log')

def update_errorbar(errobj, x, y, yerr=None, xerr=None):
    ln, caps, bars = errobj


    if len(bars) == 2:
        assert xerr is not None and yerr is not None, "Your errorbar object has 2 dimension of error bars defined. You must provide xerr and yerr."
        barsx, barsy = bars  # bars always exist (?)
        try:  # caps are optional
            errx_top, errx_bot, erry_top, erry_bot = caps
        except ValueError:  # in case there is no caps
            pass

    elif len(bars) == 1:
        assert (xerr is     None and yerr is not None) or\
               (xerr is not None and yerr is     None),  \
               "Your errorbar object has 1 dimension of error bars defined. You must provide xerr or yerr."

        if xerr is not None:
            barsx, = bars  # bars always exist (?)
            try:
                errx_top, errx_bot = caps
            except ValueError:  # in case there is no caps
                pass
        else:
            barsy, = bars  # bars always exist (?)
            try:
                erry_top, erry_bot = caps
            except ValueError:  # in case there is no caps
                pass

    ln.set_data(x,y)

    try:
        errx_top.set_xdata(x + xerr)
        errx_bot.set_xdata(x - xerr)
        errx_top.set_ydata(y)
        errx_bot.set_ydata(y)
    except NameError:
        pass
    try:
        barsx.set_segments([np.array([[xt, y], [xb, y]]) for xt, xb, y in zip(x + xerr, x - xerr, y)])
    except NameError:
        pass

    try:
        erry_top.set_xdata(x)
        erry_bot.set_xdata(x)
        erry_top.set_ydata(y + yerr)
        erry_bot.set_ydata(y - yerr)
    except NameError:
        pass
    try:
        barsy.set_segments([np.array([[x, yt], [x, yb]]) for x, yt, yb in zip(x, y + yerr, y - yerr)])
    except NameError:
        pass


if __name__ == '__main__':
    pax = plotter()
    pax.makePlot()
    for i in range(10):
        pax.update(i, i)
        time.sleep(.2)














