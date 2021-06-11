# -*- coding: utf-8 -*-
"""
Created on Wed Mar 24 12:47:22 2021

author: nick.viner
"""

from PyQt5 import QtWidgets, uic, QtCore
import sys
import dem_coregistration
import geoutil_coreg_ui
import os

#os.environ['PROJ_LIB'] = ".\\deps\\proj"
#os.environ['GDAL_DATA'] = ".\\deps"
bundle_dir = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
UI_PATH = os.path.abspath(os.path.join(bundle_dir, 'geoutil_coreg.ui'))

class coRegForm(QtWidgets.QDialog, geoutil_coreg_ui.Ui_GeoUtilsCoReg):
    def __init__(self, parent=None):
        super().__init__()
        #uic.loadUi(UI_PATH, self)
        
        self.setupUi(self)
        
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
        self.threadPool = QtCore.QThreadPool()
        
        if self.grid == "Primary":
            self.grid = 'master'
        else:
            self.grid = 'slave'
            
    def displayAbout(self):
        
        about = QtWidgets.QMessageBox()
        about.setIcon(QtWidgets.QMessageBox.Information)
        about.setText("GeoUtils Coregistration GUI: Nick Viner, Hakai Institute, 2021")
        about.setInformativeText("See details for references.")
        about.setDetailedText("DEM_Coregistration Algorithm: Amaury Dehecq\n\nBased on methods presented by Nuth & Kaab 2011")
        about.setWindowTitle("About")
        about.setStandardButtons(QtWidgets.QMessageBox.Ok)
        about.exec_()
        
    def loadPrimary(self):
        
        self.primaryDEM, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Select DEM file...', '', ".tif(*.tif)")
        
        self.lineEdit.setText(self.primaryDEM)
        
        self.updateLog("Primary loaded: %s" % self.primaryDEM)
    
    def loadSecondary(self):
        
        self.secondaryDEM, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Select DEM file...', '', ".tif(*.tif)")
        
        self.lineEdit_2.setText(self.secondaryDEM)
        
        self.updateLog("Secondary loaded: %s" % self.secondaryDEM)
        
    def loadMask(self):
        
        self.mask, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Select Mask file...', '', ".tif(*.tif)")
        
        self.textMask.setText(self.mask)
    
    def loadShapeFile(self):
        
        self.shapefilemask, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Select shape file...', '', ".shp(*.shp)")
        
        self.textShapefileMask.setText(self.shapefilemask)
        
    def changeNoDataValue(self):
        
        self.noDataValue = int(self.textNoDataValue.text())
        
        self.updateLog("No data value set to: %s" % self.textNoDataValue.text())
        
    def changeIterations(self):
        
        self.iterations = int(self.textIterations.value())
        
        self.updateLog("Iterations set to %s" % self.textIterations.value())
        
    def changeMinimumPointCount(self):
        
        self.minPointCount = int(self.textMinimumPointCount.text())
        
        self.updateLog("Minimum point count set to %s" % self.textMinimumPointCount.text())
        
    def changeMinimumHeightFilter(self):
        
        self.minheight = self.textMinimumHeightFilter.text()
        
    def changeMaximumHeightFilder(self):
        
        self.maxheight = self.textMaximumHeightFilter.text()
        
    def changeMaximumResidual(self):
        
        self.maxRes = self.textMaximumResidualAllowance.text()
        
    def doVerticalShift(self):
        
        if self.comboVerticalShift.currentText() == 'False':
            
            self.ramp = False
            
            self.updateLog("Vertical shift disabled.")
            
        else:
            
            self.ramp = True
            
            self.updateLog("Vertical shift enabled.")
    
    @QtCore.pyqtSlot(str)
    def updateLog(self, msg):
        
        self.log.setText(str(msg))
    
    @QtCore.pyqtSlot(int)
    def progressBarUpdate(self, val):
        
        self.progress += val
        self.progressBar.setValue(self.progress)
    
    @QtCore.pyqtSlot(int)
    def progressBarFinished(self, val):
        
        self.progressBar.setValue(0)
        self.progress = 0
        self.actionRun.setEnabled(True)
        self.actionLoadPrimary.setEnabled(True)
        self.actionLoadSecondary.setEnabled(True)
        self.actionLoadMask.setEnabled(True)
        self.actionLoadShapefile.setEnabled(True)
        
        
    def coregister(self):
        self.actionRun.setEnabled(False)
        self.actionLoadPrimary.setEnabled(False)
        self.actionLoadSecondary.setEnabled(False)
        self.actionLoadMask.setEnabled(False)
        self.actionLoadShapefile.setEnabled(False)
        
        saveFile, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Save coregistered DEM...', '', ".tif(*.tif)")
        
        cr = dem_coregistration.coregistration(master_dem_fp=self.primaryDEM, slave_dem_fp=self.secondaryDEM, outfile=saveFile, niter=self.iterations,
                           plot = self.plot, maskfile=self.mask, shp=self.shapefilemask, buffer=0, nodata1=self.noDataValue,
                           nodata2=self.noDataValue, min_count=self.minPointCount, zmax=self.maxheight, zmin=self.minheight,
                           resmax=self.maxRes, degree=self.degree, grid=self.grid, save=True, IS=self.icesat, doRamp=self.ramp)
        
        cr.signal.updateSignal.connect(self.updateLog)
        cr.signal.progressSignal.connect(self.progressBarUpdate)
        cr.signal.finishedSignal.connect(self.progressBarFinished)
        
        self.progressBar.setValue(0)
        self.progressBar.maximum = 13 + self.iterations
        self.threadPool.start(cr)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    form = coRegForm()
    form.show()

    app.exec_()
    