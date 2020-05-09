
import sys
import os

from PyQt5 import QtWidgets, uic
import sys

# inherit correct QMainWindow class as defined in UI file (designer)
class Ui(QtWidgets.QMainWindow):
    def __init__(self):
        super(Ui, self).__init__()
        # load *.ui file
        uic.loadUi('BAT/BAT/src/gui/bat_gui.ui', self)
        #
        # set widgets pointers and connections
        #
        # status bar
        self.statusbar = self.findChild(QtWidgets.QStatusBar, "statusbar")
        self.statusbar.showMessage("BAT initialized and ready.")
        # menu bar
        #self.actionNew.triggered.connect()
        #self.actionOpen.triggered.connect()
        #self.actionSave.triggered.connect()
        #self.actionSave_as.triggered.connect()
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

    # test button function
    def testButtonPressed(self):
        print(self.cofBoltHeadMin.text())

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


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = Ui()
    window.show()
    sys.exit(app.exec_())