
import sys
import os
from pathlib import Path
from collections import Counter, OrderedDict
from src.functions.InputFileParser import InputFileParser
from PyQt5 import QtWidgets, uic, QtCore
from PyQt5.QtWidgets import QFileDialog
from PyQt5.Qt import Qt, QApplication, QClipboard

# inherit correct QMainWindow class as defined in UI file (designer)
class Ui(QtWidgets.QMainWindow):
    def __init__(self, materials=None, bolts=None):
        super(Ui, self).__init__()
        # load *.ui file (relative path to ./gui/bat_gui.ui from bat_qt_gui.py location)
        ui_file = os.path.dirname(os.path.realpath(__file__)) + "/gui/bat_gui.ui"
        uic.loadUi(ui_file, self)
        #
        # INIT variables
        self.materials = materials
        self.bolts = bolts
        self.openedInputFile = None
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
        # base options
        self.radioEsaPss = self.findChild(QtWidgets.QRadioButton, "radioEsaPss")
        self.radioEcss = self.findChild(QtWidgets.QRadioButton, "radioEcss")
        self.radioVdi = self.findChild(QtWidgets.QRadioButton, "radioVdi")
        self.projectName = self.findChild(QtWidgets.QLineEdit, "projectName")
        self.tabWidget = self.findChild(QtWidgets.QTabWidget, "tabWidget")
        # Bolt tab
        self.radioJointMin = self.findChild(QtWidgets.QRadioButton, "radioJointMin")
        self.radioJointMean = self.findChild(QtWidgets.QRadioButton, "radioJointMean")
        self.comboBolt = self.findChild(QtWidgets.QComboBox, "comboBolt")
        self.comboBoltMaterial = self.findChild(QtWidgets.QComboBox, "comboBoltMaterial")
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
        self.prevailingTorque = self.findChild(QtWidgets.QLineEdit, "prevailingTorque")
        self.loadingPlaneFactor = self.findChild(QtWidgets.QLineEdit, "loadingPlaneFactor")
        # Clamped Parts tab
        self.cofClampedParts = self.findChild(QtWidgets.QLineEdit, "cofClampedParts")
        self.numberOfShearPlanes = self.findChild(QtWidgets.QSpinBox, "numberOfShearPlanes")
        self.throughHoleDiameter = self.findChild(QtWidgets.QLineEdit, "throughHoleDiameter")
        self.substDiameter = self.findChild(QtWidgets.QLineEdit, "substDiameter")
        self.clampedPartsTable = self.findChild(QtWidgets.QTableWidget, "clampedPartsTable")
        self.addCpButton = self.findChild(QtWidgets.QPushButton, "addCpButton")
        self.addCpButton.clicked.connect(self.addCpPressed)
        self.deleteCpButton = self.findChild(QtWidgets.QPushButton, "deleteCpButton")
        self.deleteCpButton.clicked.connect(self.deleteCpPressed)
        self.useShimCheck = self.findChild(QtWidgets.QCheckBox, "useShimCheck")
        # FOS tab
        self.fosY= self.findChild(QtWidgets.QLineEdit, "fosY")
        self.fosU= self.findChild(QtWidgets.QLineEdit, "fosU")
        self.fosSlip= self.findChild(QtWidgets.QLineEdit, "fosSlip")
        self.fosGap= self.findChild(QtWidgets.QLineEdit, "fosGap")
        # Loads tab
        self.loadsTable = self.findChild(QtWidgets.QTableWidget, "loadsTable")
        self.addRowButton = self.findChild(QtWidgets.QPushButton, "addRowButton")
        self.addRowButton.clicked.connect(self.addRowPressed)
        self.deleteRowButton = self.findChild(QtWidgets.QPushButton, "deleteRowButton")
        self.deleteRowButton.clicked.connect(self.deleteRowPressed)
        self.pasteLoadsExcel = self.findChild(QtWidgets.QPushButton, "pasteLoadsExcel")
        self.pasteLoadsExcel.clicked.connect(self.pasteFromExcel)
        self.deltaT= self.findChild(QtWidgets.QLineEdit, "deltaT")
        # Calculate tab
        self.inputFile= self.findChild(QtWidgets.QLineEdit, "inputFile")
        self.saveInputFileButton= self.findChild(QtWidgets.QPushButton, "saveInputFileButton")
        self.saveInputFileButton.clicked.connect(self.saveInputFilePressed)
        self.outputFile= self.findChild(QtWidgets.QLineEdit, "outputFile")
        self.saveOutputFileButton= self.findChild(QtWidgets.QPushButton, "saveOutputFileButton")
        self.saveOutputFileButton.clicked.connect(self.saveOutputFilePressed)
        self.calculateButton= self.findChild(QtWidgets.QPushButton, "calculateButton")
        self.calculateButton.clicked.connect(self.calculatePressed)
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
        # set radio-buttons
        self.radioEsaPss.setChecked(True)
        self.radioEcss.setEnabled(False) # not implemented yet
        self.radioVdi.setEnabled(False) # not implemented yet
        self.radioJointMin.setChecked(True)
        self.radioJointMean.setEnabled(False) # not implemented yet
        self.radioLockYes.setChecked(True)
        # fill bolt combo-boxes
        for key in self.bolts.bolts:
            self.comboBolt.addItem(key)
        for key in self.materials.materials:
            self.comboBoltMaterial.addItem(key)
        # set number of shear planes and loading plane factor
        self.numberOfShearPlanes.setValue(1)
        self.loadingPlaneFactor.setText("0.5")
        # fos tab
        self.fosY.setText("1.1")
        self.fosU.setText("1.25")
        self.fosSlip.setText("1.1")
        self.fosGap.setText("1.0")
        # set delta-T
        self.deltaT.setText("0")
        # loads-table init
        self.loadsTable.setColumnCount(4) # init load-table
        self.loadsTable.insertRow(0)
        self.loadsTable.setHorizontalHeaderLabels(\
            ["Bolt-ID\n\nLoad-Case", "FN\n\n[N]", "FQ1\n\n[N]", "FQ2\n(optional)\n[N]"])
        self.loadsTable.setItem(0,0,QtWidgets.QTableWidgetItem("test bolt"))
        #
        # clamped-parts-table
        self.clampedPartsTable.setColumnCount(2) # init clamped-parts-table
        self.clampedPartsTable.insertRow(0)
        self.clampedPartsTable.setHorizontalHeaderLabels(\
            ["Material\nor\nShim", "Thickness\n[mm]"])
        header = self.clampedPartsTable.horizontalHeader()       
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)#ResizeToContents)
        #header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        combo = QtWidgets.QComboBox()
        combo_box_options = ["bla1", "bla2"]
        for t in combo_box_options:
            combo.addItem(t)
        self.clampedPartsTable.setCellWidget(0,0,combo)
        self.clampedPartsTable.setVerticalHeaderItem(0, QtWidgets.QTableWidgetItem("CP(0)"))

    # erase gui - reset / new
    def erase_gui(self):
        self.radioEsaPss.setChecked(True)
        self.projectName.setText("new BAT project")
        self.radioJointMin.setChecked(True)
        self.comboBolt.setCurrentIndex(0)
        self.comboBoltMaterial.setCurrentIndex(0)
        # CoFs: [mu_head_max, mu_thread_max, mu_head_min, mu_thread_min]
        self.cofBoltHeadMax.setText('')
        self.cofThreadMax.setText('')
        self.cofBoltHeadMin.setText('')
        self.cofThreadMin.setText('')
        # fill torques etc
        self.tightTorque.setText('')
        self.tightTorqueTol.setText('')
        self.radioLockYes.setChecked(True)
        self.prevailingTorque.setText('')
        self.loadingPlaneFactor.setText('')
        # clamped parts tab
        self.cofClampedParts.setText('')
        self.numberOfShearPlanes.setValue(1)
        self.throughHoleDiameter.setText('')
        self.substDiameter.setText('')
        # fos tab
        self.fosY.setText("1.1")
        self.fosU.setText("1.25")
        self.fosSlip.setText("1.1")
        self.fosGap.setText("1.0")
        # loads tab
        self.deltaT.setText("0")
        self.loadsTable.clearContents()
        self.loadsTable.setRowCount(0)
        self.loadsTable.insertRow(0)
        self.loadsTable.setItem(0,0,QtWidgets.QTableWidgetItem("test bolt"))
        # calculate tab
        self.inputFile.setText('')
        self.outputFile.setText('')
        # finally set statusbar
        self.statusbar.showMessage("New BAT project created")

    # use locking device radioButton logic for prevailing torque QLineEdit
    def lockRadioClicked(self):
        radioButton = self.sender()
        if radioButton.isChecked():
            if radioButton.text()=="YES":
                self.prevailingTorque.setEnabled(True)
            elif radioButton.text()=="NO":
                self.prevailingTorque.setEnabled(False)

    # add clamped part button pressed
    def addCpPressed(self):
        print("Add CP")

    # delete clamped part button pressed
    def deleteCpPressed(self):
        print("Delete CP")

    # add row button pressed
    def addRowPressed(self):
        # current selection in table
        selection = self.loadsTable.selectedIndexes()
        if selection:
            # insert row: selected cell (row+1)
            self.loadsTable.insertRow(selection[0].row()+1)

    # delete row button pressed
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

    # save input file button pressed
    def saveInputFilePressed(self):
        print("Save Input File")
 
    # save output file button pressed
    def saveOutputFilePressed(self):
        print("Save Output File")

    # calculate button pressed
    def calculatePressed(self):
        print("BAT Calculation Start")

    # MENU - new
    def menuNew(self):
        # reset gui - erase
        self.erase_gui()

    # MENU - open input file
    def menuOpenInput(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        dialog = QFileDialog() # file-dialog
        dialog.setOptions(options)
        bat_home_dir = Path(os.path.dirname(os.path.realpath(__file__))).parents[0]
        dialog.setDirectory(str(bat_home_dir))
        openedFileName, _ = dialog.getOpenFileName(self,\
            "QFileDialog.getOpenFileName()",\
            "",\
            "BAT Input Files (*.inp)")
        if openedFileName:
            # read and parse input file
            self.openedInputFile = InputFileParser(openedFileName)
            #
            # fill gui
            if self.openedInputFile.method == "ESAPSS":
                self.radioEsaPss.setChecked(True)
            else:
                print("ERROR: ECSS/VDI method not implemented yet")
            self.projectName.setText(self.openedInputFile.project_name)
            if self.openedInputFile.joint_mos_type == "min":
                self.radioJointMin.setChecked(True)
            else:
                print("ERROR: MEAN method not implemented yet")
            # set bolt and bolt-material combo-box
            index = self.comboBolt.findText(\
                self.openedInputFile.bolt, QtCore.Qt.MatchFixedString)
            if index >= 0:
                self.comboBolt.setCurrentIndex(index)
            index = self.comboBoltMaterial.findText(\
                self.openedInputFile.bolt_material, QtCore.Qt.MatchFixedString)
            if index >= 0:
                self.comboBoltMaterial.setCurrentIndex(index)
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
                self.prevailingTorque.setText(str(self.openedInputFile.prevailing_torque))
            else:
                self.radioLockNo.setChecked(True)
                self.prevailingTorque.setEnabled(False)
            self.loadingPlaneFactor.setText(str(self.openedInputFile.loading_plane_factor))
            # clamped parts tab
            self.cofClampedParts.setText(str(self.openedInputFile.cof_clamp))
            self.numberOfShearPlanes.setValue(self.openedInputFile.nmbr_shear_planes)
            self.throughHoleDiameter.setText(str(self.openedInputFile.through_hole_diameter))
            self.substDiameter.setText(str(self.openedInputFile.subst_da))
            # TODO: clamped parts table
            # fos tab
            self.fosY.setText(str(self.openedInputFile.fos_y))
            self.fosU.setText(str(self.openedInputFile.fos_u))
            self.fosSlip.setText(str(self.openedInputFile.fos_slip))
            self.fosGap.setText(str(self.openedInputFile.fos_gap))
            # loads tab
            self.deltaT.setText(str(self.openedInputFile.delta_t))
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

    # MENU - save
    def menuSave(self):
        print("save")

    # MENU - save as
    def menuSaveAs(self):
        print("save as")

    # use data in clipboard and paste loads from excel
    def pasteFromExcel(self):
        text = QApplication.clipboard().text()
        print(text+'\n')


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = Ui()
    window.show()
    sys.exit(app.exec_())