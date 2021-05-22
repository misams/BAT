from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget
from PyQt5.QtWidgets import QTextEdit
from PyQt5 import QtGui
import math
"""
Torque-Info-Window
"""
class TorqueInfoWindow(QWidget):
    def __init__(self, bolt, bolt_mat, mu_th_min, mu_uh_min):
        super(TorqueInfoWindow, self).__init__()
        # set analysis variables
        self.bolt = bolt
        self.bolt_mat = bolt_mat
        self.mu_th_min = mu_th_min
        self.mu_uh_min = mu_uh_min
        # set window title
        self.setWindowTitle("Tightening Torque Info")
        # set layout and add widgets
        layout = QVBoxLayout()
        label = QLabel("Tightening Torque Info Text:")
        layout.addWidget(label)
        self.setLayout(layout)
        self.resize(800, 400) # resize window
        # add QTextEdit for file display
        textEdit = QTextEdit()
        # write text to textEdit
        if self.mu_th_min=="" or self.mu_uh_min=="":
            bolt_info_text = "Minimum CoF is not set --> NO torque analysis possible."
        else:
            bolt_info_text = self._calculate_torques()
        textEdit.setReadOnly(True)
        font = QtGui.QFont("Monospace", 9) # set monospace font (platform independent)
        font.setStyleHint(QtGui.QFont.TypeWriter)
        textEdit.setCurrentFont(font)
        textEdit.setText(bolt_info_text)
        layout.addWidget(textEdit)
        # close window button
        Quit = QPushButton('Close', self) #button object
        Quit.setGeometry(10, 10, 60, 35) # Set the position and size of the button
        Quit.setStyleSheet("font-weight: bold") # Set the style and color of the button
        Quit.clicked.connect(self.close) # Close the window after clicking the button
        layout.addWidget(Quit)

    def _calculate_torques(self):
        # define bolt utilization list
        nue_list = [0.6, 0.7, 0.8, 0.85, 0.9, 0.95]
        # Wp-option for shear stress analysis
        # "VDI"  : Wp=d^3*pi/12 full plasticity
        # "ECSS" : Wp=d^3*pi/16 fully elastic
        WP_OPTION = "ECSS"
        #
        # Calculate tightening torque and preload force
        self.mu_th_min = float(self.mu_th_min)
        self.mu_uh_min = float(self.mu_uh_min)
        if WP_OPTION == "VDI":
            # sig_m_zul acc. equ. (143) VDI2230
            # uses: Wp = d^3*pi/12 --> full tau plasticity 
            sig_m_zul = self.bolt_mat.sig_y/math.sqrt(1+3*(3/2*self.bolt.d2/self.bolt.ds*\
                (self.bolt.p/(math.pi*self.bolt.d2)+1.155*self.mu_th_min))**2)
        elif WP_OPTION == "ECSS":
            # uses: Wp = d^3*pi/16 --> tau fully elastic
            # use for ECSS / ESA PSS
            sig_m_zul = self.bolt_mat.sig_y/math.sqrt(1+3*(2*self.bolt.d2/self.bolt.ds*\
                (self.bolt.p/(math.pi*self.bolt.d2)+1.155*self.mu_th_min))**2)
        # calculate assembly preload and tightening torque for nue_list
        F_M_zul = []
        T_A = []
        for nue in nue_list:
            # permissible assembly preload in [kN]
            F_M_zul.append(sig_m_zul*self.bolt.As*nue/1000)
            # tightening torque for metric threads in [Nm]
            # with 1/sin(2*lambda) for countersunk bolts
            Dkm = (self.bolt.dh+self.bolt.d)/2 # approximate value; through hole dia. not used
            T_A.append(F_M_zul[-1]*(0.16*self.bolt.p+0.58*self.bolt.d2*self.mu_th_min+\
                Dkm/(2*math.sin(self.bolt.lbd*math.pi/180/2))*self.mu_uh_min))
        # create output string
        # define header
        output_str =  "\nF_M: preload after tightening (assembly preload) [kN]\n"
        output_str += "\nT_A: total installation torque of bolt (assembly tightening torque) [Nm]\n\n"
        output_str += "{0:=^100}\n".format('=')
        #nue_list = [0.6, 0.7, 0.8, 0.85, 0.9, 0.95]
        output_str += "|{0:^20}|{1:^12}|{2:^12}|{3:^12}|{4:^12}|{5:^12}|{6:^12}|\n"\
            .format("Bolt", "", "", "", "", "", "")
        output_str += "|{0:^20}|{1:^12}|{2:^12}|{3:^12}|{4:^12}|{5:^12}|{6:^12}|\n"\
            .format("Utilization", "60%", "70%", "80%", "85%", "90%", "95%")
        output_str += "|{0:^20}|{1:^12}|{2:^12}|{3:^12}|{4:^12}|{5:^12}|{6:^12}|\n"\
            .format("Factor (nue):", "", "", "", "", "", "")
        output_str += "{0:=^100}\n".format('=')
        if F_M_zul[0]<1.0 or T_A[0]<1.0:
            output_str += "|{0:^20}|{1:^12.2f}|{2:^12.2f}|{3:^12.2f}|{4:^12.2f}|{5:^12.2f}|{6:^12.2f}|\n"\
                .format("F_M [kN]:", F_M_zul[0], F_M_zul[1], F_M_zul[2], F_M_zul[3], F_M_zul[4], F_M_zul[5])
            output_str += "|{0:-^20}+{1:-^12}+{2:-^12}+{3:-^12}+{4:-^12}+{5:-^12}+{6:-^12}|\n"\
                .format("-", "-", "-", "-", "-", "-", "-")
            output_str += "|{0:^20}|{1:^12.2f}|{2:^12.2f}|{3:^12.2f}|{4:^12.2f}|{5:^12.2f}|{6:^12.2f}|\n"\
                .format("T_A [Nm]:", T_A[0], T_A[1], T_A[2], T_A[3], T_A[4], T_A[5])
        else:
            output_str += "|{0:^20}|{1:^12.1f}|{2:^12.1f}|{3:^12.1f}|{4:^12.1f}|{5:^12.1f}|{6:^12.1f}|\n"\
                .format("F_M [kN]:", F_M_zul[0], F_M_zul[1], F_M_zul[2], F_M_zul[3], F_M_zul[4], F_M_zul[5])
            output_str += "|{0:-^20}+{1:-^12}+{2:-^12}+{3:-^12}+{4:-^12}+{5:-^12}+{6:-^12}|\n"\
                .format("-", "-", "-", "-", "-", "-", "-")
            output_str += "|{0:^20}|{1:^12.1f}|{2:^12.1f}|{3:^12.1f}|{4:^12.1f}|{5:^12.1f}|{6:^12.1f}|\n"\
                .format("T_A [Nm]:", T_A[0], T_A[1], T_A[2], T_A[3], T_A[4], T_A[5])
        output_str += "{0:=^100}\n".format('=')
        output_str += "\n# Used data for F_M and T_A calculation (apprx. value for D_km used)\n"
        output_str += "Bolt:          {0:^}\n".format(self.bolt.name)
        output_str += "Bolt Material: {0:^} (Sig_y = {1:.1f} MPa)\n".format(self.bolt_mat.name, self.bolt_mat.sig_y)
        output_str += "mu_th_min:     {0:.2f}\n".format(self.mu_th_min)
        output_str += "mu_uh_min:     {0:.2f}\n".format(self.mu_uh_min)
        return output_str