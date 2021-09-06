import sys, os
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.Qt import Qt
from src.gui.ImageInfoWindow import ImageInfoWindow

"""
Bolted-Flange-Window
"""
class FlangeWindow(QtWidgets.QMainWindow):
    def __init__(self, init_dict, ui_dir, loadsTable=None, tabWidget=None):
        super(FlangeWindow, self).__init__()
        # item to be modified in main-window
        self.loadsTabletoBeModified = loadsTable
        self.tabWidgetToBeModified = tabWidget
        # load *.ui file
        self.ui_dir = ui_dir
        uic.loadUi(self.ui_dir+"/bat_flange.ui", self)
        #
        # set window title
        #
        self.setWindowTitle("Bolted Flange Definition")
        #
        # set widgets pointers and connections
        #
        self.tabWidget = self.findChild(QtWidgets.QTabWidget, "tabWidget")
        self.nmbrBolts = self.findChild(QtWidgets.QSpinBox, "nmbrBolts")
        self.lineEditPcd = self.findChild(QtWidgets.QLineEdit, "lineEditPcd")
        self.lineEditPcd.setValidator(self.decimalValidator())
        self.lineEditHNeutral = self.findChild(QtWidgets.QLineEdit, "lineEditHNeutral")
        self.lineEditHNeutral.setValidator(self.decimalValidator())
        self.radioEqual = self.findChild(QtWidgets.QRadioButton, "radioEqual")
        self.radioSine = self.findChild(QtWidgets.QRadioButton, "radioSine")
        self.forceCompTable = self.findChild(QtWidgets.QTableWidget, "forceCompTable")
        self.forceLocTable = self.findChild(QtWidgets.QTableWidget, "forceLocTable")
        #
        # button box and normal buttons
        self.buttonBox = self.findChild(QtWidgets.QDialogButtonBox, "buttonBox")
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Close).clicked.connect(self.close)
        #self.buttonBox.button(QtWidgets.QDialogButtonBox.Apply).clicked.connect(self.click_apply)
        self.buttonCalc = self.findChild(QtWidgets.QPushButton, "buttonCalc")
        self.buttonCalc.clicked.connect(self.click_calculate)
        self.buttonWriteResults = self.findChild(QtWidgets.QPushButton, "buttonWriteResults")
        self.buttonWriteResults.clicked.connect(self.click_writeToTable)
        self.toolButton_help = self.findChild(QtWidgets.QToolButton, "toolButton_help")
        self.toolButton_help.clicked.connect(self.helpButtonPressed)
        self.w_help_window = None # help window
        #
        # analysis results
        self.phi_array = None
        self.Fbn_array = None
        self.Fbs_array = None
        self.Fbs_lat_array = None
        self.Fbs_tors_array = None
        self.circ_analysis_summary = None
        #
        # INIT GUI
        self.init_gui(init_dict)

    # regular expression validator for QLineEdit Format mask (decimal number only)
    def decimalValidator(self):
        return QtGui.QRegExpValidator(QtCore.QRegExp("^\d*\.?\d*$"))

    # init gui - default settings
    def init_gui(self, init_dict):
        # disable arbitrary flange tab (under development)
        self.tabWidget.setTabEnabled(1, False)
        # set default neutral line location and shear load distribution
        self.nmbrBolts.setValue(init_dict["nmbr_bolts"])
        self.lineEditPcd.setText(str(init_dict["pcd"]))
        self.lineEditHNeutral.setText(str(init_dict["nl_loc"]))
        if init_dict["fq_dist"] == "EQUAL":
            self.radioEqual.setChecked(True)
        else:
            self.radioSine.setChecked(True)
        # force components table init
        self.forceCompTable.setColumnCount(4)
        self.forceCompTable.insertRow(0)
        self.forceCompTable.setHorizontalHeaderLabels(\
            ["FX\n[N]", "FY\n[N]", "FZ\n[N]", "Remark"])
        self.forceCompTable.horizontalHeader().setSectionResizeMode(3, QtWidgets.QHeaderView.Stretch)
        self.forceCompTable.setItem(0,0,QtWidgets.QTableWidgetItem(str(init_dict["force_comp"][0])))
        self.forceCompTable.setItem(0,1,QtWidgets.QTableWidgetItem(str(init_dict["force_comp"][1])))
        self.forceCompTable.setItem(0,2,QtWidgets.QTableWidgetItem(str(init_dict["force_comp"][2])))
        self.forceCompTable.setItem(0,3,QtWidgets.QTableWidgetItem(init_dict["force_remark"]))
        # force location table init
        self.forceLocTable.setColumnCount(3)
        self.forceLocTable.insertRow(0)
        self.forceLocTable.setHorizontalHeaderLabels(\
            ["X (long.)\n[mm]", "Y (lat.)\n[mm]", "Z (vert.)\n[mm]"])
        self.forceLocTable.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.forceLocTable.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        self.forceLocTable.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        self.forceLocTable.setItem(0,0,QtWidgets.QTableWidgetItem(str(init_dict["force_loc"][0])))
        self.forceLocTable.setItem(0,1,QtWidgets.QTableWidgetItem(str(init_dict["force_loc"][1])))
        self.forceLocTable.setItem(0,2,QtWidgets.QTableWidgetItem(str(init_dict["force_loc"][2])))
        
    # BUTTON - click "Calculate Bolt Forces"
    def click_calculate(self):
        # calculate bolt loads for circular-flange
        self.circ_flange()

    # BUTTON - click "Write Bolt Forces to Load-Table"
    def click_writeToTable(self):
        try:
            # switch to "Loads-Tab"
            self.tabWidgetToBeModified.setCurrentIndex(3)
            # clear loadsTable and delete all rows - empty table
            self.loadsTabletoBeModified.clearContents()
            self.loadsTabletoBeModified.setRowCount(0)
            # write loads to table
            for i, row in enumerate(self.phi_array):
                self.loadsTabletoBeModified.insertRow(i) # insert row
                #bolt_id_string = "Bolt:{0:d}-{1:.1f}°".format(i+1,row) # long id-string
                bolt_id_string = "Bolt:{0:d}".format(i+1)
                self.loadsTabletoBeModified.setItem(i,0,QtWidgets.QTableWidgetItem(bolt_id_string))
                self.loadsTabletoBeModified.setItem(i,1,QtWidgets.QTableWidgetItem("{0:.2f}".format(self.Fbn_array[i])))
                self.loadsTabletoBeModified.setItem(i,2,QtWidgets.QTableWidgetItem("{0:.2f}".format(self.Fbs_array[i])))
                self.loadsTabletoBeModified.setItem(i,3,QtWidgets.QTableWidgetItem("{0:.2f}".format(0)))
        except Exception as e:
            print("Circular-Flange Exception B: " + str(e))

    # circular flange analysis
    def circ_flange(self):
        try:
            # inputs
            n_bolts = int(self.nmbrBolts.value())
            pcd = float(self.lineEditPcd.text()) # [mm]
            h_neutral = float(self.lineEditHNeutral.text())
            xF = float(self.forceLocTable.item(0,0).text())# [mm] normal distance from I/F flange
            yF = float(self.forceLocTable.item(0,1).text()) # [mm] lateral distance from circular center
            zF = float(self.forceLocTable.item(0,2).text()) # [mm] vertical distance from circular center
            Fx = float(self.forceCompTable.item(0,0).text()) # [N] axial force
            Fy = float(self.forceCompTable.item(0,1).text()) # [N] lateral force 1
            Fz = float(self.forceCompTable.item(0,2).text()) # [N] lateral force 2
            #
            # analysis
            Fax = Fx # [N] axial force acting on bolt flange
            Flat = np.sqrt(Fy**2+Fz**2) # [N] lateral force acting on bolt flange
            lat_arm = np.sqrt(yF**2+zF**2) # [mm] lateral force arm for torque
            Mblat = Flat*xF/1000 # [Nm] bending moment on bolt flange caused by lateral force
            Mbax = Fax*lat_arm/1000 # [Nm] bending moment on bolt flange caused by axial force
            Mt = Flat*lat_arm/1000 # [Nm] torsion moment by lateral offset
            self.circ_analysis_summary = [Fax, Flat, Mblat, Mbax, Mt]
            #
            self.phi_array = np.arange(0,360,360/n_bolts) # vector of bolt angles (start at top)
            z_arm_array = pcd/2*np.cos(np.deg2rad(self.phi_array)) # bolt central distance in z-dir
            z_neutral_array = z_arm_array+pcd/2-pcd*h_neutral # distance from neutral line
            # axial bolt force Fbn (Mblat+Mbax --> conservative)
            self.Fbn_array = (Mblat+Mbax)*1000*z_neutral_array/np.sum(z_neutral_array**2) + Fax/n_bolts
            # shear load caused by lateral force
            if self.radioEqual.isChecked(): # homogenous shear force distribution
                print("Bolt Shear Load Distribution: EQUAL")
                self.Fbs_lat_array = np.ones(n_bolts)*Flat/n_bolts
            else: # sine shear force distribution
                print("Bolt Shear Load Distribution: SINE")
                sin_norm = np.abs(np.sin(np.deg2rad(self.phi_array)))
                self.Fbs_lat_array = Flat/np.sum(sin_norm)*sin_norm
            # overall bolt shear force: add shear force out of moment Mt
            self.Fbs_tors_array = 2*Mt*1000/(n_bolts*pcd)*np.sign(np.sin(np.deg2rad(self.phi_array+0.01*360/n_bolts)))
            self.Fbs_array = np.abs(self.Fbs_lat_array + self.Fbs_tors_array) # linear addition (correct for worst case bolt locations)

            # Plot bolt forces in window
            w_plot = PlotWindowCircFlange(self.phi_array, self.Fbn_array, self.Fbs_array, \
                self.Fbs_lat_array, self.Fbs_tors_array, self.circ_analysis_summary)
            w_plot.setWindowModality(Qt.ApplicationModal) # lock main window
            w_plot.show()
        except Exception as e:
            print("Circular-Flange Exception A: " + str(e))

    # get circular-flange dict with all values
    def get_circular_flange_dict(self):
        if self.radioEqual.isChecked():
            fq_dist = "EQUAL"
        else:
            fq_dist = "SINE"
        circular_flange_dict = {
            "nmbr_bolts" : int(self.nmbrBolts.value()),
            "pcd" : float(self.lineEditPcd.text()),
            "nl_loc" : float(self.lineEditHNeutral.text()),
            "fq_dist" : fq_dist,
            "force_loc" : [float(self.forceLocTable.item(0,0).text()), \
                           float(self.forceLocTable.item(0,1).text()), \
                           float(self.forceLocTable.item(0,2).text())],
            "force_comp" : [float(self.forceCompTable.item(0,0).text()), \
                            float(self.forceCompTable.item(0,1).text()), \
                            float(self.forceCompTable.item(0,2).text())],
            "force_remark" : self.forceCompTable.item(0,3).text()
        }
        return circular_flange_dict

    # arbitrary flange analysis
    def arb_flange(self):
        # define force and force-location (definition: z-component set to 0)
        # JPL17: LC1.2
        force = np.array([54704, 162923, 0]) # [N] (Fx, Fy, Fz=0)
        force_loc = np.array([-119.5, -125, 0]) # [mm] (px, py, pz=0)

        # define location and area of bolts
        diam = 16 # [mm]
        area = diam**2*np.pi/4 # area [mm^2] 
        bolts = np.array( \
                [[0, 0, area], \
                 [0, -70, area], \
                 [0, -180, area], \
                 [0, -250, area], \
                 [30.6, -35, area], \
                 [30.6, -215, area], \
                 [61.2, 0, area], \
                 [61.2, -70, area], \
                 [61.2, -180, area], \
                 [61.2, -250, area]])

        # number of bolts
        boltsCount = bolts[:,0].size
        # calculate bolt-CoG
        AiXi = np.multiply(bolts[:,2], bolts[:,0])
        AiYi = np.multiply(bolts[:,2], bolts[:,1])
        Asum = np.sum(bolts[:,2])
        cog = np.array([np.divide(np.sum(AiXi),Asum), np.divide(np.sum(AiYi),Asum), 0])
        # calculate vectors from cog to bolts and angle of vectors
        rx = bolts[:,0]-cog[0]
        ry = bolts[:,1]-cog[1]
        r = np.sqrt(np.square(rx)+np.square(ry))
        Airiri = np.multiply(bolts[:,2],np.square(r))
        alpha = np.arctan2(ry, rx)
        # vector to force point
        rF = np.array([force_loc[0]-cog[0], force_loc[1]-cog[1], 0])
        # moment around cog
        M = np.cross(rF, force) 
        # calculate bolt forces
        FxS = np.full(boltsCount, force[0]/boltsCount)
        FyS = np.full(boltsCount, force[1]/boltsCount)
        FiM = np.divide(np.multiply(bolts[:,2],r), np.sum(Airiri))*M[2]
        FiMx = np.multiply(FiM,np.cos(np.pi/2-alpha))*-1
        FiMy = np.multiply(FiM,np.sin(np.pi/2-alpha))
        Fx = FxS+FiMx
        Fy = FyS+FiMy
        Fmax = np.sqrt(np.square(Fx)+np.square(Fy))

        print("Fmax: {0:.1f} N".format(max(Fmax)))
        print("{0:d} bolts".format(boltsCount))
        print(M)

        # scale for arrow plot
        fscale = 0.003

        # define circle (bolt) objects for plot
        circles = []
        for b in bolts:
            circles.append(plt.Circle((b[0], b[1]), diam/2))
        fCircle = plt.Circle((force_loc[0], force_loc[1]), diam/2, color='r')
        cogCircle = plt.Circle((cog[0], cog[1]), diam/2, color='k')

        # define vectors for bolts
        print("Bold-ID\tFx[N]\tFy[N]\tMAG[N]")
        soa = np.array([[force_loc[0], force_loc[1], force[0]*fscale, force[1]*fscale]])
        for i in range(0,boltsCount):
            b = np.array([[bolts[i,0], bolts[i,1], Fx[i]*fscale, Fy[i]*fscale]])
            soa = np.concatenate((soa,b), axis=0)
            # print max bolt forces
            print("{0:d}\t{1:.1f}\t{2:.1f}\t{3:.1f}".format(i+1, Fx[i], Fy[i], Fmax[i]))
        print("{0:^}\t-\t-\t{1:.1f}".format("MAX:", max(Fmax)))

        # plot
        X, Y, U, V = zip(*soa)
        plt.figure()
        ax = plt.gca()
        for c in circles:
            ax.add_artist(c)
        ax.add_artist(fCircle)
        ax.add_artist(cogCircle)
        ax.quiver(X, Y, U, V, angles='xy', scale_units='xy', scale=1, color='r')
        plt.axis('equal')
        #ax.set_xlim([1800, 2200])
        ax.set_ylim([-300, 300])
        plt.draw()
        plt.show()

    # tool-button: help
    def helpButtonPressed(self):
        # create image help window
        help_image = os.path.join(Path(self.ui_dir).parents[1],"doc/BAT_doc/flange_1_help.png")
        self.w_help_window = ImageInfoWindow(\
            help_image, 770, 600, "Circular Flange Help Window")
        self.w_help_window.setWindowModality(Qt.WindowModal) # do not lock main window
        self.w_help_window.show()

# plot-window with matplotlib am pyQt5
class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)

# plot window for circular-flange
class PlotWindowCircFlange(QtWidgets.QMainWindow):
    def __init__(self, phi_array, Fbn_array, Fbs_array, Fbs_lat_array, Fbs_tors_array, circ_analysis_summary):
        super(PlotWindowCircFlange, self).__init__()

        sc = MplCanvas(self, width=7, height=6, dpi=100)
        sc.axes.plot(phi_array,Fbn_array,"bo-",label="$F_{bn}$")
        sc.axes.plot(phi_array,Fbs_array,"rd-", label="$F_{bs}$")
        sc.axes.plot(phi_array,Fbs_lat_array,"k*", label="$F_{bs}^{lat}$")
        sc.axes.plot(phi_array,Fbs_tors_array,"m*", label="$F_{bs}^{tors}$")
        sc.axes.legend(loc="lower left")
        sc.axes.set_title("Circular Flange - Bolt Forces")
        sc.axes.set_xlabel("bolt angular location [deg]")
        sc.axes.set_ylabel("bolt force [N]")
        sc.axes.grid(True)
        sc.axes.set_xlim([0,360])
        sc.axes.set_xticks(np.arange(0,361,20))

        # Create toolbar, passing canvas as first parament, parent (self, the MainWindow) as second.
        toolbar = NavigationToolbar(sc, self)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(toolbar)
        layout.addWidget(sc)
        # add label with summary text
        # self.circ_analysis_summary = [Fax, Flat, Mblat, Mbax, Mt]
        label_summary_str = "\nCircular-Flange Analysis Summary:\n\n"
        label_summary_str += "Axial Force:            Fax   = {0:.1f} N\n".format(circ_analysis_summary[0])
        label_summary_str += "Lateral Force :         Flat  = {0:.1f} N\n".format(circ_analysis_summary[1])
        label_summary_str += "Lateral Bending Moment: Mblat = {0:.1f} Nm\n".format(circ_analysis_summary[2])
        label_summary_str += "Axial Bending Moment:   Mbax  = {0:.1f} Nm\n".format(circ_analysis_summary[3])
        label_summary_str += "Torsional Moment:       Mt    = {0:.1f} Nm\n".format(circ_analysis_summary[4])
        label = QtWidgets.QLabel()
        font = QtGui.QFont("Monospace", 9) # set monospace font (platform independent)
        font.setStyleHint(QtGui.QFont.TypeWriter)
        label.setFont(font)
        label.setText(label_summary_str)
        layout.addWidget(label)

        # Create a placeholder widget to hold our toolbar and canvas.
        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)
        self.resize(800,600)