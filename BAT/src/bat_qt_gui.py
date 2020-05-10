
import sys
import os
from pathlib import Path
from src.functions.InputFileParser import InputFileParser
from PyQt5 import QtWidgets, uic, QtCore
from PyQt5.QtWidgets import QFileDialog
from src.gui.table_models import LoadTableModel

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
        self.radioEsaPss.setChecked(True)
        self.radioEcss = self.findChild(QtWidgets.QRadioButton, "radioEcss")
        self.radioEcss.setEnabled(False) # not implemented yet
        self.radioVdi = self.findChild(QtWidgets.QRadioButton, "radioVdi")
        self.radioVdi.setEnabled(False) # not implemented yet
        self.projectName = self.findChild(QtWidgets.QLineEdit, "projectName")
        # Bolt tab
        self.radioJointMin = self.findChild(QtWidgets.QRadioButton, "radioJointMin")
        self.radioJointMin.setChecked(True)
        self.radioJointMean = self.findChild(QtWidgets.QRadioButton, "radioJointMean")
        self.radioJointMean.setEnabled(False) # not implemented yet
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
        self.radioLockYes.setChecked(True)
        self.radioLockNo = self.findChild(QtWidgets.QRadioButton, "radioLockNo")
        self.radioLockNo.toggled.connect(self.lockRadioClicked)
        self.prevailingTorque = self.findChild(QtWidgets.QLineEdit, "prevailingTorque")
        self.loadingPlaneFactor = self.findChild(QtWidgets.QLineEdit, "loadingPlaneFactor")
        # Clamped Parts tab
        self.cofClampedParts = self.findChild(QtWidgets.QLineEdit, "cofClampedParts")
        self.numberOfShearPlanes = self.findChild(QtWidgets.QSpinBox, "numberOfShearPlanes")
        self.numberOfShearPlanes.setValue(1)
        self.throughHoleDiameter = self.findChild(QtWidgets.QLineEdit, "throughHoleDiameter")
        self.substDiameter = self.findChild(QtWidgets.QLineEdit, "substDiameter")
        self.clampedPartsTable = self.findChild(QtWidgets.QTableView, "clampedPartsTable")
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
        self.loadsTable = self.findChild(QtWidgets.QTableView, "loadsTable")
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
        #
        # INIT GUI
        self.init_gui()

    # init gui
    def init_gui(self):
        # fill bolt combo-box
        for key in self.bolts.bolts:
            self.comboBolt.addItem(key)
        # fill bolt-material combo-box
        for key in self.materials.materials:
            self.comboBoltMaterial.addItem(key)

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
        print("new")

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
            # TODO: loads table
            tableModel = LoadTableModel(self.openedInputFile.bolt_loads)
            self.loadsTable.setModel(tableModel)
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


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = Ui()
    window.show()
    sys.exit(app.exec_())