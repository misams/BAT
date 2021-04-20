import sys
import os
import logging
from pathlib import Path
from collections import Counter, OrderedDict
from src.functions.InputFileParser import InputFileParser
from src.EsaPss import EsaPss
from src.Ecss import Ecss
from src.gui.GuiInputHandler import GuiInputHandler
from PyQt5 import QtWidgets, uic, QtCore, QtGui
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QMenu
from PyQt5.Qt import Qt, QApplication, QClipboard
from src.gui.FlangeGuiWindow import FlangeWindow # currently dummy-only
from src.gui.BoltInfoWindow import BoltInfoWindow
from src.gui.MatInfoWindow import MatInfoWindow

# inherit correct QMainWindow class as defined in UI file (designer)
class Ui(QtWidgets.QMainWindow):
    def __init__(self, ui_dir, materials=None, bolts=None, inp_dir=None, bat_version="-"):
        super(Ui, self).__init__()
        # load *.ui file
        self.ui_dir = ui_dir
        uic.loadUi(self.ui_dir+"/bat_gui.ui", self)
        #
        # INIT variables
        self.materials = materials # materials DB
        self.bolts = bolts # bolts DB
        self.openedInputFile = None # opened BAT input file
        self.gih = None # GUI input handler
        self.inp_dir = inp_dir # default directory of input-files
        self.bat_version = bat_version # BAT software version
        #
        # set window title
        #
        self.setWindowTitle("Bolt Analysis Tool - BAT (v{0:^})".format(self.bat_version))
        #
        # set widgets pointers and connections
        #
        # status bar
        self.statusbar = self.findChild(QtWidgets.QStatusBar, "statusbar")
        self.statusbar.showMessage("BAT initialized and ready.")
        # menu bar
        self.actionNew.triggered.connect(self.menuNew)
        self.actionOpen.triggered.connect(self.menuOpenInput)
        self.actionSave.triggered.connect(self.menuSave)
        self.actionSave_as.triggered.connect(self.menuSaveAs)
        self.actionQuit.triggered.connect(self.close)
        self.actionBolted_Flange.triggered.connect(self.menuBoltedFlange)
        self.w_bolted_flange = None # bolted flange window
        self.actionAbout_BAT.triggered.connect(self.menuAboutBat)
        # base options
        self.radioEsaPss = self.findChild(QtWidgets.QRadioButton, "radioEsaPss")
        self.radioEsaPss.toggled.connect(self.methodRadioClicked)
        self.radioEcss = self.findChild(QtWidgets.QRadioButton, "radioEcss")
        self.radioEcss.toggled.connect(self.methodRadioClicked)
        self.radioVdi = self.findChild(QtWidgets.QRadioButton, "radioVdi")
        self.radioVdi.toggled.connect(self.methodRadioClicked)
        self.projectName = self.findChild(QtWidgets.QLineEdit, "projectName")
        self.tabWidget = self.findChild(QtWidgets.QTabWidget, "tabWidget")
        # Bolt tab
        self.radioTBJ = self.findChild(QtWidgets.QRadioButton, "radioTBJ")
        self.radioTTJ = self.findChild(QtWidgets.QRadioButton, "radioTTJ")
        self.comboBolt = self.findChild(QtWidgets.QComboBox, "comboBolt")
        self.comboBoltMaterial = self.findChild(QtWidgets.QComboBox, "comboBoltMaterial")
        self.comboBoltMaterialT = self.findChild(QtWidgets.QComboBox, "comboBoltMaterialT")
        self.toolButton_bolt_info = self.findChild(QtWidgets.QToolButton, "toolButton_bolt_info")
        self.toolButton_bolt_info.clicked.connect(self.boltInfoPressed)
        self.toolButton_mat_info = self.findChild(QtWidgets.QToolButton, "toolButton_mat_info")
        self.toolButton_mat_info.clicked.connect(self.matInfoPressed)
        self.cofBoltHeadMin = self.findChild(QtWidgets.QLineEdit, "cofBoltHeadMin")
        self.cofBoltHeadMax = self.findChild(QtWidgets.QLineEdit, "cofBoltHeadMax")
        self.cofThreadMin = self.findChild(QtWidgets.QLineEdit, "cofThreadMin")
        self.cofThreadMax = self.findChild(QtWidgets.QLineEdit, "cofThreadMax")
        self.tightTorque = self.findChild(QtWidgets.QLineEdit, "tightTorque")
        self.tightTorqueTol = self.findChild(QtWidgets.QLineEdit, "tightTorqueTol")
        self.radioLockYes = self.findChild(QtWidgets.QRadioButton, "radioLockYes")
        self.radioLockYes.toggled.connect(self.lockRadioClicked)
        self.radioLockNo = self.findChild(QtWidgets.QRadioButton, "radioLockNo")
        self.radioLockNo.toggled.connect(self.lockRadioClicked)
        self.Mp_min = self.findChild(QtWidgets.QLineEdit, "Mp_min")
        self.Mp_max = self.findChild(QtWidgets.QLineEdit, "Mp_max")
        self.loadingPlaneFactor = self.findChild(QtWidgets.QLineEdit, "loadingPlaneFactor")
        self.w_bolt_info = None # bolt info window
        self.w_mat_info = None # material info window
        # Clamped Parts tab
        self.cofClampedParts = self.findChild(QtWidgets.QLineEdit, "cofClampedParts")
        self.numberOfShearPlanes = self.findChild(QtWidgets.QSpinBox, "numberOfShearPlanes")
        self.throughHoleDiameter = self.findChild(QtWidgets.QLineEdit, "throughHoleDiameter")
        self.substDA = self.findChild(QtWidgets.QLineEdit, "substDA")
        self.comboRz = self.findChild(QtWidgets.QComboBox, "comboRz")
        self.clampedPartsTable = self.findChild(QtWidgets.QTableWidget, "clampedPartsTable")
        self.addCpButton = self.findChild(QtWidgets.QPushButton, "addCpButton")
        self.addCpButton.clicked.connect(self.addCpPressed)
        self.deleteCpButton = self.findChild(QtWidgets.QPushButton, "deleteCpButton")
        self.deleteCpButton.clicked.connect(self.deleteCpPressed)
        self.useShimCheck = self.findChild(QtWidgets.QCheckBox, "useShimCheck")
        self.useShimCheck.stateChanged.connect(self.useShimChecked)
        self.combo_shim = QtWidgets.QComboBox()
        self.combo_shim_mat = QtWidgets.QComboBox()
        self.combo_shim_matT = QtWidgets.QComboBox()
        # FOS tab
        self.fosY= self.findChild(QtWidgets.QLineEdit, "fosY")
        self.fosU= self.findChild(QtWidgets.QLineEdit, "fosU")
        self.fosSlip= self.findChild(QtWidgets.QLineEdit, "fosSlip")
        self.fosGap= self.findChild(QtWidgets.QLineEdit, "fosGap")
        self.fosFit= self.findChild(QtWidgets.QLineEdit, "fosFit")
        # Loads tab
        self.loadsTable = self.findChild(QtWidgets.QTableWidget, "loadsTable")
        self.addRowButton = self.findChild(QtWidgets.QPushButton, "addRowButton")
        self.addRowButton.clicked.connect(self.addRowPressed)
        self.deleteRowButton = self.findChild(QtWidgets.QPushButton, "deleteRowButton")
        self.deleteRowButton.clicked.connect(self.deleteRowPressed)
        self.pasteLoadsExcel = self.findChild(QtWidgets.QPushButton, "pasteLoadsExcel")
        self.pasteLoadsExcel.clicked.connect(self.pasteFromExcel)
        self.copyLoadsTable = self.findChild(QtWidgets.QPushButton, "copyLoadsTable")
        self.copyLoadsTable.clicked.connect(self.copyLoadsTableToClipboard)
        self.deltaT = self.findChild(QtWidgets.QLineEdit, "deltaT")
        self.checkBoxVdiThermal = self.findChild(QtWidgets.QCheckBox, "checkBoxVdiThermal")
        self.checkBoxVdiThermal.stateChanged.connect(self.useVdiChecked)
        # Calculate tab
        self.inputFile = self.findChild(QtWidgets.QLineEdit, "inputFile")
        self.saveInputFileButton = self.findChild(QtWidgets.QPushButton, "saveInputFileButton")
        self.saveInputFileButton.clicked.connect(self.saveInputFilePressed)
        self.outputFile = self.findChild(QtWidgets.QLineEdit, "outputFile")
        self.saveOutputFileButton = self.findChild(QtWidgets.QPushButton, "saveOutputFileButton")
        self.saveOutputFileButton.clicked.connect(self.saveOutputFilePressed)
        self.calculateButton = self.findChild(QtWidgets.QPushButton, "calculateButton")
        self.calculateButton.clicked.connect(self.calculatePressed)
        self.radioJointMin = self.findChild(QtWidgets.QRadioButton, "radioJointMin")
        self.radioJointMean = self.findChild(QtWidgets.QRadioButton, "radioJointMean")
        # Output tab
        self.textEditOutput = self.findChild(QtWidgets.QTextEdit, "textEditOutput")
        #
        # INIT GUI
        self.init_gui()

    # key press handler
    def keyPressEvent(self, event):
        # load-table: delete items with delete-key
        if event.key()==Qt.Key_Delete and self.tabWidget.currentIndex()==3:
            for item in self.loadsTable.selectedItems():
                item.setText('') 

    # init gui - default settings
    def init_gui(self):
        # disable flange menu (under development)
        #self.actionBolted_Flange.setEnabled(False)
        # set radio-buttons
        self.radioEcss.setChecked(True)
        self.radioVdi.setEnabled(False) # not implemented yet
        #self.toolButton_mat_info.setEnabled(False) # not implemented yet
        self.radioJointMin.setChecked(True)
        self.radioJointMean.setEnabled(True)
        self.radioLockYes.setChecked(True)
        self.comboBoltMaterialT.setEnabled(False) # disable VDI bolt material
        # fill bolt combo-boxes
        for key in self.bolts.bolts:
            self.comboBolt.addItem(key)
        for key in self.materials.materials:
            self.comboBoltMaterial.addItem(key)
            self.comboBoltMaterialT.addItem(key)
        # set number of shear planes and loading plane factor
        self.numberOfShearPlanes.setValue(1)
        self.loadingPlaneFactor.setText("0.5")
        self.substDA.setText('')
        # fos tab
        self.fosY.setText("1.1")
        self.fosU.setText("1.25")
        self.fosSlip.setText("1.1")
        self.fosGap.setText("1.0")
        self.fosFit.setText("1.0")
        # set delta-T
        self.deltaT.setText("0")
        # loads-table init
        self.loadsTable.setColumnCount(4) # init load-table
        self.loadsTable.insertRow(0)
        self.loadsTable.setHorizontalHeaderLabels(\
            ["Bolt-ID\n\nLoad-Case", "FN\n\n[N]", "FQ1\n\n[N]", "FQ2\n(optional)\n[N]"])
        self.loadsTable.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.loadsTable.setItem(0,0,QtWidgets.QTableWidgetItem("test bolt"))
        self.checkBoxVdiThermal.setChecked(False)
        #
        # clamped-parts-table
        self.useShimCheck.setChecked(True)
        self.clampedPartsTable.setColumnCount(3) # init clamped-parts-table
        self.clampedPartsTable.insertRow(0)
        self.clampedPartsTable.setHorizontalHeaderLabels(\
            ["Thickness [mm]\nor\nShim", "Material", "Material VDI-Temp."])
        header = self.clampedPartsTable.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        # add shim line CP(0)
        for i in self.bolts.washers:
            self.combo_shim.addItem(i)
        for i in self.materials.materials:
            self.combo_shim_mat.addItem(i)
            self.combo_shim_matT.addItem(i)
        self.clampedPartsTable.setCellWidget(0,0,self.combo_shim)
        self.clampedPartsTable.setCellWidget(0,1,self.combo_shim_mat)
        self.clampedPartsTable.setCellWidget(0,2,self.combo_shim_matT)
        self.clampedPartsTable.setVerticalHeaderItem(0, QtWidgets.QTableWidgetItem("CP(0)"))
        # add first clamped part - empty line
        combo_cp_mat = QtWidgets.QComboBox()
        combo_cp_matT = QtWidgets.QComboBox()
        self.clampedPartsTable.insertRow(1)
        self.clampedPartsTable.setVerticalHeaderItem(1, QtWidgets.QTableWidgetItem("CP(1)"))
        for i in self.materials.materials:
            combo_cp_mat.addItem(i)
            combo_cp_matT.addItem(i)
        self.clampedPartsTable.setItem(1,0,QtWidgets.QTableWidgetItem(''))
        self.clampedPartsTable.setCellWidget(1,1,combo_cp_mat)
        self.clampedPartsTable.setCellWidget(1,2,combo_cp_matT)
        self.useShimChecked()
        # output tab setup
        self.tabWidget.setTabEnabled(5, False) # disable output tab
        font = QtGui.QFont("Monospace", 9) # set monospace font (platform independent)
        font.setStyleHint(QtGui.QFont.TypeWriter)
        self.textEditOutput.setCurrentFont(font)
        self.textEditOutput.setLineWrapMode(QtWidgets.QTextEdit.NoWrap) # do not wrap text

    # erase gui - reset / new
    def erase_gui(self):
        self.radioEcss.setChecked(True)
        self.projectName.setText("new BAT project")
        self.radioTBJ.setChecked(True)
        self.radioJointMin.setChecked(True)
        self.comboBolt.setCurrentIndex(0)
        self.comboBoltMaterial.setCurrentIndex(0)
        self.comboBoltMaterialT.setCurrentIndex(0)
        # CoFs: [mu_head_max, mu_thread_max, mu_head_min, mu_thread_min]
        self.cofBoltHeadMax.setText('')
        self.cofThreadMax.setText('')
        self.cofBoltHeadMin.setText('')
        self.cofThreadMin.setText('')
        # fill torques etc
        self.tightTorque.setText('')
        self.tightTorqueTol.setText('')
        self.radioLockYes.setChecked(True)
        self.Mp_min.setText('')
        self.Mp_max.setText('')
        self.loadingPlaneFactor.setText("0.5")
        # clamped parts tab
        self.cofClampedParts.setText('')
        self.numberOfShearPlanes.setValue(1)
        self.throughHoleDiameter.setText('')
        self.substDA.setText('')
        row_offset = 0 # row-number changes after removeRow
        for row in range(1,self.clampedPartsTable.rowCount()): 
            self.clampedPartsTable.removeRow(row-row_offset) # delete all CPs
            row_offset += 1
        self.clampedPartsTable.selectRow(0) # add first clamped-part CP(1)
        self.addCpPressed() # add row below
        # fos tab
        self.fosY.setText("1.1")
        self.fosU.setText("1.25")
        self.fosSlip.setText("1.1")
        self.fosGap.setText("1.0")
        self.fosFit.setText("1.0")
        # loads tab
        self.deltaT.setText("0")
        self.loadsTable.clearContents()
        self.loadsTable.setRowCount(0)
        self.loadsTable.insertRow(0)
        self.loadsTable.setItem(0,0,QtWidgets.QTableWidgetItem("test bolt"))
        self.checkBoxVdiThermal.setChecked(False)
        self.useShimChecked()
        # calculate tab
        self.inputFile.setText('')
        self.outputFile.setText('')
        # output tab
        self.textEditOutput.clear()
        self.tabWidget.setTabEnabled(5, False)
        self.tabWidget.setCurrentIndex(0)
        # finally set statusbar
        self.statusbar.showMessage("New BAT project created")

    # use method radioButton to set embedding options
    def methodRadioClicked(self):
        radioButton = self.sender()
        if radioButton.isChecked():
            self.comboRz.clear()
            if radioButton.text()=="ESA PSS-03-208":
                self.comboRz.addItem("-")
            elif radioButton.text()=="ECSS-E-HB-32-23A":
                # fill embedding Rz combo-box
                self.comboRz.addItem("5%")
                self.comboRz.addItem("<10")
                self.comboRz.addItem("10-40")
                self.comboRz.addItem("40-160")

    # use locking device radioButton logic for prevailing torque QLineEdit
    def lockRadioClicked(self):
        radioButton = self.sender()
        if radioButton.isChecked():
            if radioButton.text()=="YES":
                self.Mp_min.setEnabled(True)
                self.Mp_max.setEnabled(True)
            elif radioButton.text()=="NO":
                self.Mp_min.setEnabled(False)
                self.Mp_max.setEnabled(False)

    # use-shim checkbox (includes useVdiChecked() method)
    def useShimChecked(self):
        if self.useShimCheck.isChecked():
            self.combo_shim_mat.setEnabled(True)
            self.combo_shim_matT.setEnabled(True)
            self.combo_shim.setEnabled(True)
        else:
            self.combo_shim_mat.setEnabled(False)
            self.combo_shim_matT.setEnabled(False)
            self.combo_shim.setEnabled(False)
        # check VDI checkbox
        self.useVdiChecked()

    # use VDI-thermal method checkbox
    def useVdiChecked(self):
        if self.checkBoxVdiThermal.isChecked():
            self.comboBoltMaterialT.setEnabled(True)
            # enable materialT column in clamped parts table
            for row in range(1,self.clampedPartsTable.rowCount()):
                self.clampedPartsTable.cellWidget(row,2).setEnabled(True)
            # handle row(0) for shim
            if self.useShimCheck.isChecked():
                self.clampedPartsTable.cellWidget(0,2).setEnabled(True)
        else:
            self.comboBoltMaterialT.setEnabled(False)
            # disable materialT column in clamped parts table
            for row in range(0,self.clampedPartsTable.rowCount()):
                self.clampedPartsTable.cellWidget(row,2).setEnabled(False)

    # clampedPartsTable - add clamped part button pressed
    def addCpPressed(self):
        # current selection in table
        selection = self.clampedPartsTable.selectedIndexes()
        if selection:
            # insert row: selected cell (row+1)
            ins_row = selection[0].row()+1
            self.clampedPartsTable.insertRow(ins_row)
            self.clampedPartsTable.setVerticalHeaderItem(ins_row,\
                QtWidgets.QTableWidgetItem("CP({0:d})".format(ins_row)))
            # insert CP materials combo-box in new row
            combo_cp_mat = QtWidgets.QComboBox()
            combo_cp_matT = QtWidgets.QComboBox()
            for i in self.materials.materials:
                combo_cp_mat.addItem(i)
                combo_cp_matT.addItem(i)
            self.clampedPartsTable.setItem(ins_row,0,QtWidgets.QTableWidgetItem(''))
            self.clampedPartsTable.setCellWidget(ins_row,1,combo_cp_mat)
            self.clampedPartsTable.setCellWidget(ins_row,2,combo_cp_matT)
            # renumber clamped parts CP(i); start at first CP(1)
            for row in range(1,self.clampedPartsTable.rowCount()):
                self.clampedPartsTable.setVerticalHeaderItem(row,\
                    QtWidgets.QTableWidgetItem("CP({0:d})".format(row)))
            self.useShimChecked() # check and set VDI-thermal method

    # clampedPartsTable - delete clamped part button pressed
    def deleteCpPressed(self):
        # get number of selections per row (in selection order)
        row_sel = Counter([i.row() for i in self.clampedPartsTable.selectedIndexes()])
        if row_sel:
            # key: row-number, value: selected-columns
            key = list(row_sel.keys())[0]
            value = list(row_sel.values())[0]
            # if selected-columns == 3 then complete row selected
            # delete row only if complete single row selected & not CP(0)
            if value==3 and len(row_sel)==1 and key>0:
                # remove row in clampedPartsTable
                self.clampedPartsTable.removeRow(key)
                # renumber clamped parts CP(i); start at first CP(1)
                for row in range(1,self.clampedPartsTable.rowCount()):
                    self.clampedPartsTable.setVerticalHeaderItem(row,\
                        QtWidgets.QTableWidgetItem("CP({0:d})".format(row)))

    # loadsTable - add row button pressed
    def addRowPressed(self):
        # current selection in table
        selection = self.loadsTable.selectedIndexes()
        if selection:
            # insert row: selected cell (row+1)
            self.loadsTable.insertRow(selection[0].row()+1)
        elif self.loadsTable.rowCount()==0:
            # insert row(0) - no row in table
            self.loadsTable.insertRow(0)

    # loadsTable - delete row button pressed
    def deleteRowPressed(self):
        # get number of selections per row (in selection order)
        row_sel = Counter([i.row() for i in self.loadsTable.selectedIndexes()])
        # order row-number ascending
        row_sel_asc = OrderedDict(sorted(row_sel.items()))
        # key: row-number, value: selected-columns
        # if selected-columns == 4 then complete row selected
        row_offset = 0 # if >1 rows selected
        for key, value in row_sel_asc.items():
            if value==4:
                self.loadsTable.removeRow(key-row_offset)
                row_offset += 1

    # save input file button pressed (equal to save-as)
    def saveInputFilePressed(self):
        self.menuSaveAs()
 
    # save output file button pressed
    def saveOutputFilePressed(self):
        # define output file
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        dialog = QFileDialog() # file-dialog
        dialog.setOptions(options)
        dialog.setDirectory(str(self.inp_dir))
        outputFileName, _ = dialog.getSaveFileName(self,\
            "BAT Output File",\
            "",\
            "BAT Output Files (*.out)")
        if outputFileName:
            # set fields in calculate tab & check if "out" is already added to file name
            tmp = outputFileName.split('.')
            if len(tmp) == 1 or (len(tmp) == 2 and tmp[1] == "out"):
                outputFileName = tmp[0]+".out"
            else:
                if not self.inputFile.text():
                    outputFileName = ""
                else:
                    outputFileName = self.inputFile.text().split('.')[0]+".out"
                log_str = "ERROR: output file name not correct - do not use any special characters"
                print(log_str)
                logging.warning(log_str)
            # set output-file in gui-widget
            self.outputFile.setText(outputFileName)
            print("Output-file redefined: " + outputFileName)
            logging.info("Output-file redefined: " + outputFileName)

    # calculate button pressed
    def calculatePressed(self):
        self.readGuiInputs() # read gui inputs
        compare = self.gih.compareInput(self.openedInputFile) # compare to opened input file
        if self.openedInputFile and not compare:
            if self.openedInputFile.method == "ESAPSS":
                # calc ESA-PSS
                ana_esapss = EsaPss(\
                    self.openedInputFile, self.materials, self.bolts, self.bat_version)
                output_results = ana_esapss.print_results(\
                    self.outputFile.text(), print_to_cmd=False)
                # enable output-tab and fill with results
                self.tabWidget.setTabEnabled(5, True)
                self.textEditOutput.setText(output_results)
            elif self.openedInputFile.method == "ECSS":
                # calc ESA-PSS
                ana_ecss = Ecss(\
                    self.openedInputFile, self.materials, self.bolts, self.bat_version)
                output_results = ana_ecss.print_results(\
                    self.outputFile.text(), print_to_cmd=False)
                # enable output-tab and fill with results
                self.tabWidget.setTabEnabled(5, True)
                self.textEditOutput.setText(output_results)
            else:
                print("Method not implemented in current BAT version.")
        else:
            print("Input does not match opened input file - save input file first.")
            self.messageBox(QMessageBox.Warning, "GUI Input vs. Input-File Missmatch",\
                "Input does not match opened input file - save input file first.",\
                "Deviating Items:\n{0:^}".format(str(compare)))

    # MENU - new
    def menuNew(self):
        # reset gui - erase
        self.erase_gui()

    # open input file
    def openInput(self, openedFileName):
        # read and parse input file
        self.openedInputFile = InputFileParser(openedFileName, self.bolts)
        # reset self.inp_dir and save new directory-path
        self.inp_dir = os.path.dirname(openedFileName)
        #
        # fill gui
        if self.openedInputFile.method == "ESAPSS":
            self.radioEsaPss.setChecked(True)
        elif self.openedInputFile.method == "ECSS":
            self.radioEcss.setChecked(True)
        else:
            print("ERROR: VDI2230 method not implemented yet")
        self.projectName.setText(self.openedInputFile.project_name)
        if self.openedInputFile.joint_mos_type == "min":
            self.radioJointMin.setChecked(True)
        else:
            self.radioJointMean.setChecked(True)
        if self.openedInputFile.joint_type == "TBJ":
            self.radioTBJ.setChecked(True)
        else:
            self.radioTTJ.setChecked(True)
        # set bolt and bolt-material combo-box (incl. VDI bolt mat)
        index = self.comboBolt.findText(\
            self.openedInputFile.bolt, QtCore.Qt.MatchFixedString)
        if index >= 0:
            self.comboBolt.setCurrentIndex(index)
        index = self.comboBoltMaterial.findText(\
            self.openedInputFile.bolt_material, QtCore.Qt.MatchFixedString)
        if index >= 0:
            self.comboBoltMaterial.setCurrentIndex(index)
        index = self.comboBoltMaterialT.findText(\
            self.openedInputFile.temp_bolt_material, QtCore.Qt.MatchFixedString)
        if index >= 0: # set VDI temp_bolt_material
            self.comboBoltMaterialT.setCurrentIndex(index)
        # fill CoFs
        # [mu_head_max, mu_thread_max, mu_head_min, mu_thread_min]
        self.cofBoltHeadMax.setText(str(self.openedInputFile.cof_bolt[0]))
        self.cofThreadMax.setText(str(self.openedInputFile.cof_bolt[1]))
        self.cofBoltHeadMin.setText(str(self.openedInputFile.cof_bolt[2]))
        self.cofThreadMin.setText(str(self.openedInputFile.cof_bolt[3]))
        # fill torques etc
        self.tightTorque.setText(str(self.openedInputFile.tight_torque))
        self.tightTorqueTol.setText(str(self.openedInputFile.torque_tol_tight_device))
        if self.openedInputFile.locking_mechanism == "yes":
            self.radioLockYes.setChecked(True)
            self.Mp_min.setText(str(self.openedInputFile.prevailing_torque[0]))
            self.Mp_max.setText(str(self.openedInputFile.prevailing_torque[1]))
        else:
            self.radioLockNo.setChecked(True)
            self.Mp_min.setEnabled(False)
            self.Mp_max.setEnabled(False)
        self.loadingPlaneFactor.setText(str(self.openedInputFile.loading_plane_factor))
        #
        # clamped parts tab
        self.cofClampedParts.setText(str(self.openedInputFile.cof_clamp))
        self.numberOfShearPlanes.setValue(self.openedInputFile.nmbr_shear_planes)
        self.throughHoleDiameter.setText(str(self.openedInputFile.through_hole_diameter))
        self.substDA.setText(str(self.openedInputFile.subst_da))
        # set Rz combo-box if method==ECSS
        if self.openedInputFile.method=="ECSS":
            index = self.comboRz.findText(\
                self.openedInputFile.emb_rz, QtCore.Qt.MatchFixedString)
            if index >= 0:
                self.comboRz.setCurrentIndex(index)
        # shim setup
        if self.openedInputFile.use_shim != "no":
            self.useShimCheck.setChecked(True)
            self.useShimChecked()
            # set CP(0) - shim if used
            # set shim and shim-material combo-box
            shim_combo = self.clampedPartsTable.cellWidget(0,0)
            index = shim_combo.findText(\
                self.openedInputFile.use_shim[1], QtCore.Qt.MatchFixedString)
            if index >= 0:
                shim_combo.setCurrentIndex(index)
            shim_mat_combo = self.clampedPartsTable.cellWidget(0,1)
            index = shim_mat_combo.findText(\
                self.openedInputFile.use_shim[0], QtCore.Qt.MatchFixedString)
            if index >= 0:
                shim_mat_combo.setCurrentIndex(index)
            # VDI shim material
            shim_temp_mat_combo = self.clampedPartsTable.cellWidget(0,2)
            index = shim_temp_mat_combo.findText(\
                self.openedInputFile.temp_use_shim[0], QtCore.Qt.MatchFixedString)
            if index >= 0:
                shim_temp_mat_combo.setCurrentIndex(index)
        else:
            self.useShimCheck.setChecked(False)
            self.useShimChecked()
        # delete all CPs after shim CP(0)
        row_offset = 0 # row-number changes after removeRow
        for row in range(1,self.clampedPartsTable.rowCount()): 
            self.clampedPartsTable.removeRow(row-row_offset) # delete all CPs
            row_offset += 1
        # fill clamped parts
        for i, cp in self.openedInputFile.clamped_parts.items():
            if i!=0:
                self.clampedPartsTable.selectRow(i-1) # select row
                self.addCpPressed() # add row below
                self.clampedPartsTable.item(i,0).setText(str(cp[1])) # set CP thickness
                # set CP material combo-box
                cp_mat_combo = self.clampedPartsTable.cellWidget(i,1)
                index = cp_mat_combo.findText(\
                    cp[0], QtCore.Qt.MatchFixedString)
                if index >= 0:
                    cp_mat_combo.setCurrentIndex(index)
        for i, temp_cp in self.openedInputFile.temp_clamped_parts.items():
                # set VDI CP material combo-box
                cp_temp_mat_combo = self.clampedPartsTable.cellWidget(i,2)
                index = cp_temp_mat_combo.findText(\
                    temp_cp[0], QtCore.Qt.MatchFixedString)
                if index >= 0:
                    cp_temp_mat_combo.setCurrentIndex(index)
        # fos tab
        self.fosY.setText(str(self.openedInputFile.fos_y))
        self.fosU.setText(str(self.openedInputFile.fos_u))
        self.fosSlip.setText(str(self.openedInputFile.fos_slip))
        self.fosGap.setText(str(self.openedInputFile.fos_gap))
        self.fosFit.setText(str(self.openedInputFile.fos_fit))
        # loads tab
        self.deltaT.setText(str(self.openedInputFile.delta_t))
        if self.openedInputFile.temp_use_vdi_method != "no": # VDI method checkbox
            self.checkBoxVdiThermal.setChecked(True)
            self.useShimChecked()
        else:
            self.checkBoxVdiThermal.setChecked(False)
            self.useShimChecked()
        self.loadsTable.setRowCount(0) # delete all rows
        for i, bi in enumerate(self.openedInputFile.bolt_loads):
            self.loadsTable.insertRow(i) # insert row
            # fill bolt-loads into table
            self.loadsTable.setItem(i,0,QtWidgets.QTableWidgetItem(bi[0]))
            self.loadsTable.setItem(i,1,QtWidgets.QTableWidgetItem(str(bi[1])))
            self.loadsTable.setItem(i,2,QtWidgets.QTableWidgetItem(str(bi[2])))
            self.loadsTable.setItem(i,3,QtWidgets.QTableWidgetItem(str(bi[3])))
        # calculate tab
        self.inputFile.setText(openedFileName)
        outp_file = openedFileName.split('.')[0]+".out"
        self.outputFile.setText(outp_file)
        # finally set statusbar
        self.statusbar.showMessage("Input File Opened: "+openedFileName)

    # MENU - open input file
    def menuOpenInput(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        dialog = QFileDialog() # file-dialog
        dialog.setOptions(options)
        #bat_home_dir = Path(os.path.dirname(os.path.realpath(__file__))).parents[0]
        dialog.setDirectory(str(self.inp_dir))
        openedFileName, _ = dialog.getOpenFileName(self,\
            "Open BAT Input File",\
            "",\
            "BAT Input Files (*.inp)")
        if openedFileName:
            self.openInput(openedFileName)

    # MENU - save
    def menuSave(self):
        self.readGuiInputs() # read gui inputs
        if self.openedInputFile: # check if input-file is already opened
            compare = self.gih.compareInput(self.openedInputFile) # compare to opened input file
            if compare:
                mbox = self.messageBox(QMessageBox.Information, "Save Info",\
                    "Input changed - saveing input file will overwrite following inputs:",\
                    "Deviating Items:\n{0:^}".format(str(compare)), "OkCancel")
                if mbox == QMessageBox.Ok:
                    self.gih.saveInputFile(self.openedInputFile.input_file)
                    print("Input-file saved: " + str(self.openedInputFile.input_file))
            else: 
                self.gih.saveInputFile(self.openedInputFile.input_file)
                print("Input-file saved: " + str(self.openedInputFile.input_file))
            # reopen new input file
            self.openInput(str(self.openedInputFile.input_file))
        else:
            # if no input file loaded - save-as new input file
            self.menuSaveAs()

    # MENU - save as
    def menuSaveAs(self):
        # read all GUI inputs 
        # TODO: check if inputs are correct / consistent
        self.readGuiInputs()
        # define and save new input-file
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        dialog = QFileDialog() # file-dialog
        dialog.setOptions(options)
        #bat_home_dir = Path(os.path.dirname(os.path.realpath(__file__))).parents[0]
        dialog.setDirectory(str(self.inp_dir))
        savedFileName, _ = dialog.getSaveFileName(self,\
            "Save New BAT Input File",\
            "",\
            "BAT Input Files (*.inp)")
        if savedFileName:
            # check if "inp" is already added to file name
            tmp = savedFileName.split('.')
            if len(tmp) == 1 or (len(tmp) == 2 and tmp[1] == "inp"):
                savedFileName = tmp[0]+".inp"
                # save GUI inputs into file
                self.gih.saveInputFile(savedFileName)
                print("Input-file saved: " + savedFileName)
                logging.info("Input-file saved: " + savedFileName)
                # set fields in calculate tab
                self.inputFile.setText(savedFileName)
                outp_file = savedFileName.split('.')[0]+".out"
                self.outputFile.setText(outp_file)
                # reopen new input file
                self.openInput(savedFileName)
            else:
                log_str = "ERROR: input file name not correct - do not use any special characters"
                print(log_str)
                logging.warning(log_str)

    # read gui entries and store to GuiInputHandler
    def readGuiInputs(self):
        # create new GuiInputHandler class
        self.gih = GuiInputHandler()
        # project name and method
        self.gih.project_name = self.projectName.text()
        method_string = ""
        if self.radioEsaPss.isChecked():
            method_string = "ESAPSS"
        elif self.radioEcss.isChecked():
            method_string = "ECSS"
        elif self.radioVdi.isChecked():
            method_string = "VDI"
        self.gih.method = method_string
        # Bolt tab
        joint_type_string = ""
        if self.radioTBJ.isChecked():
            joint_type_string = "TBJ"
        else:
            joint_type_string = "TTJ"
        self.gih.joint_type = joint_type_string
        self.gih.bolt = self.comboBolt.currentText()
        self.gih.bolt_material = self.comboBoltMaterial.currentText()
        self.gih.temp_bolt_material = self.comboBoltMaterialT.currentText()
        #[mu_head_max, mu_thread_max, mu_head_min, mu_thread_min]
        # TODO: error handling if input wrong
        self.gih.cof_bolt = (\
            float(self.cofBoltHeadMax.text()), float(self.cofThreadMax.text()),\
            float(self.cofBoltHeadMin.text()), float(self.cofThreadMin.text()) )
        self.gih.tight_torque = float(self.tightTorque.text())
        self.gih.torque_tol_tight_device = float(self.tightTorqueTol.text())
        if self.radioLockNo.isChecked():
            self.gih.locking_mechanism = "no"
        else:
            self.gih.locking_mechanism = "yes"
            self.gih.prevailing_torque = (float(self.Mp_min.text()),float(self.Mp_max.text()))
        self.gih.loading_plane_factor = float(self.loadingPlaneFactor.text())
        # Clamped Parts tab
        self.gih.cof_clamp = float(self.cofClampedParts.text())
        self.gih.nmbr_shear_planes = int(self.numberOfShearPlanes.value())
        self.gih.through_hole_diameter = float(self.throughHoleDiameter.text())
        self.gih.subst_da = float(self.substDA.text())
        self.gih.emb_rz = self.comboRz.currentText()
        if self.useShimCheck.isChecked(): # shim
            shim = self.clampedPartsTable.cellWidget(0,0).currentText()
            shim_mat = self.clampedPartsTable.cellWidget(0,1).currentText()
            temp_shim_mat = self.clampedPartsTable.cellWidget(0,2).currentText()
            self.gih.use_shim = (shim_mat, shim)
            self.gih.temp_use_shim = (temp_shim_mat, shim)
            # add shim to clamped parts dict
            self.gih.clamped_parts.update({ 0 : (shim_mat,\
                self.bolts.washers[shim].h) })
            self.gih.temp_clamped_parts.update({ 0 : (temp_shim_mat,\
                self.bolts.washers[shim].h) })
        else:
            self.gih.use_shim = "no"
            self.gih.temp_use_shim = "no"
        # get clamped parts
        rows = self.clampedPartsTable.rowCount()
        for row in range(1,rows): # start at first clamped-part CP(1)
            thk = float(self.clampedPartsTable.item(row,0).text())
            mat = self.clampedPartsTable.cellWidget(row,1).currentText()
            temp_mat = self.clampedPartsTable.cellWidget(row,2).currentText()
            self.gih.clamped_parts.update({row : (mat, thk)})
            self.gih.temp_clamped_parts.update({row : (temp_mat, thk)})
        # FOS tab
        self.gih.fos_y = float(self.fosY.text())
        self.gih.fos_u = float(self.fosU.text())
        self.gih.fos_slip = float(self.fosSlip.text())
        self.gih.fos_gap = float(self.fosGap.text())
        self.gih.fos_fit = float(self.fosFit.text())
        # Loads tab
        loads = [] # load table
        rows = self.loadsTable.rowCount()
        for row in range(0,rows): # get all load rows
            loads.append([self.loadsTable.item(row,0).text(),\
                        float(self.loadsTable.item(row,1).text()),\
                        float(self.loadsTable.item(row,2).text()),\
                        float(self.loadsTable.item(row,3).text())])
        self.gih.bolt_loads = loads
        self.gih.delta_t = float(self.deltaT.text())
        if self.checkBoxVdiThermal.isChecked():
            self.gih.temp_use_vdi_method = "yes"
        else:
            self.gih.temp_use_vdi_method = "no"
        # Calculate tab
        if self.radioJointMin.isChecked():
            self.gih.joint_mos_type = "min"
        else:
            self.gih.joint_mos_type = "mean"
        
    # MENU - About BAT
    def menuAboutBat(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText("Bolt Analysis Tool - BAT{0:^30}".format(" "))
        msg.setInformativeText("Version: v" + self.bat_version)
        msg.setWindowTitle("About BAT Info")
        msg.setDetailedText(
            "Author: Michael Sams\nProject: https://github.com/misams/BAT")
        msg.setStandardButtons(QMessageBox.Ok)
        retval = msg.exec_()

    # MENU - Bolted-flange
    def menuBoltedFlange(self, checked):
        if self.w_bolted_flange is None:
            print("Bolted-Flange window created")
            self.w_bolted_flange = FlangeWindow(self.ui_dir, self.loadsTable, self.tabWidget)
        self.w_bolted_flange.setWindowModality(Qt.ApplicationModal) # lock main window
        self.w_bolted_flange.show()

    # display gui error-messagebox
    # QMessageBox.Information, Warning, Critical
    def messageBox(self, type, title, text, det_text=None, button_opt="Ok"):
        msg = QMessageBox()
        msg.setIcon(type)
        msg.setText("{0:^}".format(text))
        msg.setWindowTitle(title)
        if det_text is not None:
            msg.setDetailedText(det_text)
        if button_opt == "Ok":
            msg.setStandardButtons(QMessageBox.Ok)
        elif button_opt == "OkCancel":
            msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        return msg.exec_()

    # use data in clipboard and paste loads from excel
    def pasteFromExcel(self):
        # get text out of clipboard
        text = QApplication.clipboard().text()
        if text:
            #print(repr(text)) # print raw-string
            text_rows = text.rstrip('\n').split('\n') # split string at newline-chars (rows in Excel)
            # clear loadsTable and delete all rows - empty table
            self.loadsTable.clearContents()
            self.loadsTable.setRowCount(0)
            # add data out of Excel
            for i, row in enumerate(text_rows):
                row_items = row.split('\t')
                if len(row_items) == 3:
                    self.loadsTable.insertRow(i) # insert row
                    # set cell values
                    self.loadsTable.setItem(i,0,QtWidgets.QTableWidgetItem(row_items[0]))
                    self.loadsTable.setItem(i,1,QtWidgets.QTableWidgetItem(row_items[1]))
                    self.loadsTable.setItem(i,2,QtWidgets.QTableWidgetItem(row_items[2]))
                    self.loadsTable.setItem(i,3,QtWidgets.QTableWidgetItem('0'))
                elif len(row_items) == 4:
                    self.loadsTable.insertRow(i) # insert row
                    # set cell values
                    self.loadsTable.setItem(i,0,QtWidgets.QTableWidgetItem(row_items[0]))
                    self.loadsTable.setItem(i,1,QtWidgets.QTableWidgetItem(row_items[1]))
                    self.loadsTable.setItem(i,2,QtWidgets.QTableWidgetItem(row_items[2]))
                    self.loadsTable.setItem(i,3,QtWidgets.QTableWidgetItem(row_items[3]))
                else:
                    print("ERROR: Excel load format incorrect.")
                    self.messageBox(QMessageBox.Warning, "Excel Load Error",\
                        "ERROR: Excel load format incorrect.")
                    break

    # Button: copy loads-table to clipboard
    def copyLoadsTableToClipboard(self):
        # read values of loads-table
        loadsTableStr = ""
        rows = self.loadsTable.rowCount()
        for row in range(0,rows): # get all load rows
            loadsTableStr += "{0:^}\t{1:^}\t{2:^}\t{3:^}\n".format(\
                self.loadsTable.item(row,0).text(), \
                self.loadsTable.item(row,1).text(), \
                self.loadsTable.item(row,2).text(), \
                self.loadsTable.item(row,3).text())
        # get global clipboard, clear it and set text
        cb = QApplication.clipboard()
        cb.clear(mode=cb.Clipboard)
        cb.setText(loadsTableStr, mode=cb.Clipboard)
        print("Loads-Table copied to Clipboard")

    # tool-Button: Bolt-Info
    def boltInfoPressed(self):
        if self.w_bolt_info is None:
            print("Bolt-Info window created")
            self.w_bolt_info = BoltInfoWindow(self.bolts.db_path)
        self.w_bolt_info.setWindowModality(Qt.ApplicationModal) # lock main window
        self.w_bolt_info.show()

    # tool-Button: Mat-Info
    def matInfoPressed(self, checked):
        if self.w_mat_info is None:
            print("Material-Info window created")
            self.w_mat_info = MatInfoWindow(self.materials)
        self.w_mat_info.setWindowModality(Qt.ApplicationModal) # lock main window
        self.w_mat_info.show()

