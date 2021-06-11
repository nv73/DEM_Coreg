# -*- coding: utf-8 -*-
"""
Created on Wed Mar 24 12:47:22 2021

author: nick.viner
"""

"""
This application is an implementation of the DEM co-registration algorithm written by Amaury Dehecq, 2015
based on the methods presented by Nuth & Kaab 2011

The following libraries were used:
    
    Numpy 1.20.3 + mkl
    GDAL 3.3.0
    PyQt 5.12.3
    SciPy 1.6.3
    MatPlotLib 3.4.2
    

"""

from PyQt5 import QtWidgets, uic, QtCore
import sys
import dem_coregistration
import geoutil_coreg_ui
import os

class coRegForm(QtWidgets.QDialog, geoutil_coreg_ui.Ui_GeoUtilsCoReg):
    def __init__(self, parent=None):
        super().__init__()
        
        #Initiate the GUI
        self.setupUi(self)
        
        #Connect signals to functions
        self.actionLoadPrimary.clicked.connect(self.loadPrimary)
        self.actionLoadSecondary.clicked.connect(self.loadSecondary)
        self.actionRun.clicked.connect(self.coregister)
        self.actionLoadMask.clicked.connect(self.loadMask)
        self.actionLoadShapefile.clicked.connect(self.loadShapeFile)
        self.textIterations.valueChanged.connect(self.changeIterations)
        self.textMinimumPointCount.textChanged.connect(self.changeMinimumPointCount)
        self.textMinimumHeightFilter.textChanged.connect(self.changeMinimumHeightFilter)
        self.textMaximumHeightFilter.textChanged.connect(self.changeMaximumHeightFilder)
        self.textMaximumResidualAllowance.textChanged.connect(self.changeMaximumResidual)
        self.textNoDataValue.textChanged.connect(self.changeNoDataValue)
        self.comboVerticalShift.currentIndexChanged.connect(self.doVerticalShift)
        self.actionAbout.clicked.connect(self.displayAbout)
        
        #Variables
        self.primaryDEM = None
        self.secondaryDEM = None
        self.iterations = int(self.textIterations.value())
        self.mask = 'none'
        self.shapefilemask = 'none'
        self.noDataValue = self.textNoDataValue.text()
        self.minPointCount = int(self.textMinimumPointCount.text())
        self.maxheight = self.textMaximumHeightFilter.text()
        self.minheight = self.textMinimumHeightFilter.text()
        self.maxRes = self.textMaximumResidualAllowance.text()
        self.degree = int(self.textPolynomialDegree.text())
        self.grid = self.comboExtractionGrid.currentText()
        self.stats = self.comboSaveStats.currentText()
        self.icesat = self.comboICESATDEM.currentText()
        self.plot = False
        self.ramp = True
        self.progress = 0
        
        #Thread handling
        self.threadPool = QtCore.QThreadPool()
        
        #The original function uses master / slave terminology. I prefer to use primary / secondary
        if self.grid == "Primary":
            self.grid = 'master'
        else:
            self.grid = 'slave'
    
    #Display a window which gives credit to the parties behind this script
    def displayAbout(self):
        
        about = QtWidgets.QMessageBox()
        about.setIcon(QtWidgets.QMessageBox.Information)
        about.setText("GeoUtils Coregistration GUI: Nick Viner, Hakai Institute, 2021")
        about.setInformativeText("See details for references.")
        about.setDetailedText("DEM_Coregistration Algorithm: Amaury Dehecq\n\nBased on methods presented by Nuth & Kaab 2011")
        about.setWindowTitle("About")
        about.setStandardButtons(QtWidgets.QMessageBox.Ok)
        about.exec_()
    
    #Get a string representing the file path to the primary DEM (*.tif)
    def loadPrimary(self):
        
        self.primaryDEM, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Select DEM file...', '', ".tif(*.tif)")
        
        self.lineEdit.setText(self.primaryDEM)
        
        self.updateLog("Primary loaded: %s" % self.primaryDEM)
    
    #Get a string representing the file path to the secondary DEM (*.tif)
    def loadSecondary(self):
        
        self.secondaryDEM, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Select DEM file...', '', ".tif(*.tif)")
        
        self.lineEdit_2.setText(self.secondaryDEM)
        
        self.updateLog("Secondary loaded: %s" % self.secondaryDEM)
    
    #Get a string representing the file path to a mask (*.tif)
    #The mask should be a georeferenced file with values of 0 and 1. Anywhere with a value of 1 or greater will be masked out.
    def loadMask(self):
        
        self.mask, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Select Mask file...', '', ".tif(*.tif)")
        
        self.textMask.setText(self.mask)
    
    #Get a string representing the file path to a shape file (*.shp)
    #The shape file us used to define the boundries in which to perform the coregistration
    def loadShapeFile(self):
        
        self.shapefilemask, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Select shape file...', '', ".shp(*.shp)")
        
        self.textShapefileMask.setText(self.shapefilemask)
    
    #Set a custom NoData value if needed
    def changeNoDataValue(self):
        
        self.noDataValue = int(self.textNoDataValue.text())
        
        self.updateLog("No data value set to: %s" % self.textNoDataValue.text())
    
    #Change how many iterations of fitting to run through
    def changeIterations(self):
        
        self.iterations = int(self.textIterations.value())
        
        self.updateLog("Iterations set to %s" % self.textIterations.value())
    
    #Change the minimum number of points in aspect bins for it to be considered valid
    def changeMinimumPointCount(self):
        
        self.minPointCount = int(self.textMinimumPointCount.text())
        
        self.updateLog("Minimum point count set to %s" % self.textMinimumPointCount.text())
    
    #Set a lower boundary for points used when co-registering (points lower than this value will be masked)
    def changeMinimumHeightFilter(self):
        
        self.minheight = self.textMinimumHeightFilter.text()
      
    #Set an upper boundary for points used when co-registering (points higher than this will be masked)
    def changeMaximumHeightFilder(self):
        
        self.maxheight = self.textMaximumHeightFilter.text()
    
    #Change the maximum allowed value of residuals. 
    def changeMaximumResidual(self):
        
        self.maxRes = self.textMaximumResidualAllowance.text()
    
    #Decide whether or not to apply a vertical shift to the data
    def doVerticalShift(self):
        
        if self.comboVerticalShift.currentText() == 'False':
            
            self.ramp = False
            
            self.updateLog("Vertical shift disabled.")
            
        else:
            
            self.ramp = True
            
            self.updateLog("Vertical shift enabled.")
    
    #Signal slot for updating the GUI update messages
    @QtCore.pyqtSlot(str)
    def updateLog(self, msg):
        
        self.log.setText(str(msg))
    
    #Signal slot for updating the GUI progress bar
    #It's a very simplistic / hacky method for a loading bar, but it's a  QoL tool
    #which provides the user a bit of confidence that the function is working. 
    @QtCore.pyqtSlot(int)
    def progressBarUpdate(self, val):
        
        self.progress += val
        self.progressBar.setValue(self.progress)
    
    #Signal slot for resetting the GUI buttons and progress bar when processing has finished
    @QtCore.pyqtSlot(int)
    def progressBarFinished(self, val):
        
        self.progressBar.setValue(0)
        self.progress = 0
        self.actionRun.setEnabled(True)
        self.actionLoadPrimary.setEnabled(True)
        self.actionLoadSecondary.setEnabled(True)
        self.actionLoadMask.setEnabled(True)
        self.actionLoadShapefile.setEnabled(True)
        
    #Create a new thread and run the co-registration function on that thread.
    def coregister(self):
        
        #Disable all the buttons on the GUI to prevent them being used while the thread is running
        self.actionRun.setEnabled(False)
        self.actionLoadPrimary.setEnabled(False)
        self.actionLoadSecondary.setEnabled(False)
        self.actionLoadMask.setEnabled(False)
        self.actionLoadShapefile.setEnabled(False)
        
        #Get a string which represents the name for the output file
        saveFile, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Save coregistered DEM...', '', ".tif(*.tif)")
        
        #Create the object which will run the co-registration function
        cr = dem_coregistration.coregistration(master_dem_fp=self.primaryDEM, slave_dem_fp=self.secondaryDEM, outfile=saveFile, niter=self.iterations,
                           plot = self.plot, maskfile=self.mask, shp=self.shapefilemask, buffer=0, nodata1=self.noDataValue,
                           nodata2=self.noDataValue, min_count=self.minPointCount, zmax=self.maxheight, zmin=self.minheight,
                           resmax=self.maxRes, degree=self.degree, grid=self.grid, save=True, IS=self.icesat, doRamp=self.ramp)
        
        #Setup the signals connections which will be needed to provide updates during processing
        cr.signal.updateSignal.connect(self.updateLog)
        cr.signal.progressSignal.connect(self.progressBarUpdate)
        cr.signal.finishedSignal.connect(self.progressBarFinished)
        
        #Set the progress bar configuration
        self.progressBar.setValue(0)
        self.progressBar.maximum = 13 + self.iterations
        
        #Open and run the co-registration object.
        self.threadPool.start(cr)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    form = coRegForm()
    form.show()

    app.exec_()
    