from src.functions.MaterialManager import MaterialManager
from src.functions.BoltManager import BoltManager
from pathlib import Path
import math
"""
Generate standard torque table acc. VDI2230
"""
class TorqueTable:
    def __init__( self, materials : MaterialManager, bolts : BoltManager):
        # main analysis inputs
        self.materials = materials
        self.bolts = bolts
        # calculate torque table
        self._calc_torque_table()

    def _calc_torque_table(self):
        # define bolt list
        #bolt_list = ["S_M4", "S_M5", "S_M6", "S_M8", "S_M10", "S_M12", "S_M14", "S_M16", \
        #             "S_M18", "S_M20", "S_M22", "S_M24", "S_M27", "S_M30", "S_M36"]
        #bolt_list = ["H_M4", "H_M5", "H_M6", "H_M8", "H_M10", "H_M12", "H_M14", "H_M16", \
        #             "H_M18", "H_M20", "H_M22", "H_M24", "H_M27", "H_M30", "H_M36",]
        bolt_list = ["CS_M2"]
        # define bolt material list
        bolt_mat_list = ["A2-70"]
        # define mu_G and mu_K
        #mu_GK_list = [0.08, 0.1, 0.12, 0.14, 0.16, 0.2, 0.24]
        mu_GK_list = [0.1, 0.12]
        # define bolt utilization
        nue = 0.8
        # Wp-option for shear stress analysis
        # "VDI"  : Wp=d^3*pi/12 full plasticity
        # "ECSS" : Wp=d^3*pi/16 fully elastic
        WP_OPTION = "ECSS"
        #
        # calculate table for metric threads
        # define header (unicode mu: \u00B5G; nu: \u03BD)
        print("{0:=^77}".format('='))
        print("|{0:^12}|{1:^20}|{2:^41}|"\
            .format("", "", "Bolt utilization \u03BD="+str(nue)))
        print("|{0:^12}|{1:^20}|{2:^20}|{3:^20}|"\
            .format("Bolt Size", "Strength grade", "Assembly preload", "Tightening torque"))
        print("|{0:^12}|{1:^20}|{2:^20}|{3:^20}|"\
            .format("", "", "F_M_tab [kN]", "M_A [Nm]"))
        print("{0:=^77}".format('='))
        print("-\t-\t", end='')
        for i in mu_GK_list:
            print("{0:.2f}\t".format(i), end='')
        for i in mu_GK_list:
            print("{0:.2f}\t".format(i), end='')
        print("\n{0:=^77}".format('='))

        for b in bolt_list:
            used_bolt = self.bolts.bolts[b]
            for m in bolt_mat_list:
                used_bolt_mat = self.materials.materials[m]
                #if used_bolt.d > 16: used_bolt_mat.sig_y = 660 # VDI 2230 hack
                F_M_zul = [] # F_M_tab for each mu
                M_A = [] # M_A for each mu
                #used_bolt_mat.sig_y = 1100 # hack for VDI2230 torque table
                for mu in mu_GK_list:
                    if WP_OPTION == "VDI":
                        # sig_m_zul acc. equ. (143) VDI2230
                        # uses: Wp = d^3*pi/12 --> full tau plasticity 
                        sig_m_zul = used_bolt_mat.sig_y/math.sqrt(1+3*(3/2*used_bolt.d2/used_bolt.ds*\
                            (used_bolt.p/(math.pi*used_bolt.d2)+1.155*mu))**2)
                    elif WP_OPTION == "ECSS":
                        # uses: Wp = d^3*pi/16 --> tau fully elastic
                        # use for ECSS / ESA PSS
                        sig_m_zul = used_bolt_mat.sig_y/math.sqrt(1+3*(2*used_bolt.d2/used_bolt.ds*\
                            (used_bolt.p/(math.pi*used_bolt.d2)+1.155*mu))**2)
                    # permissible assembly preload in [kN]
                    F_M_zul.append(sig_m_zul*used_bolt.As*nue/1000)
                    # tightening torque for metric threads in [Nm]
                    # with 1/sin(2*lambda) for countersunk bolts
                    Dkm = (used_bolt.dh+used_bolt.d)/2
                    M_A.append(F_M_zul[-1]*(0.16*used_bolt.p+0.58*used_bolt.d2*mu+\
                        Dkm/(2*math.sin(used_bolt.lbd*math.pi/180/2))*mu))
                # print table for Excel
                print("{0:^}\t{1:^}\t".format(b,m), end='')
                self.print_values(F_M_zul)
                self.print_values(M_A)
                print()

    # for table printing
    def print_values(self, li):
        for i in li:
            print("{0:.1f}\t".format(i), end='')

