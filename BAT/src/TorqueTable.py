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
        bolt_list = ["S_M4", "S_M5", "S_M6", "S_M36"]
        # define bolt material list
        bolt_mat_list = ["8.8", "10.9", "12.9"]
        #Rpmin = [640, 940, 1100] # acc. DIN EN ISO 898-1
        # define mu_G and mu_K
        mu_GK = 0.1
        # define bolt utilization
        nue = 0.9
        #
        # calculate table for metric threads
        # define header
        print("{0:=^77}".format('='))
        print("|{0:^12}|{1:^20}|{2:^41}|"\
            .format("", "", "Bolt utilization \u03BD="+str(nue)))
        print("|{0:^12}|{1:^20}|{2:^20}|{3:^20}|"\
            .format("Bolt Size", "Strength grade", "Assembly preload", "Tightening torque"))
        print("|{0:^12}|{1:^20}|{2:^20}|{3:^20}|"\
            .format("", "", "F_M_tab [kN]", "M_A [Nm]"))
        print("|{0:^12}|{1:^20}|{2:^20}|{3:^20}|"\
            .format("", "", "\u00B5G="+str(mu_GK), "\u00B5G=\u00B5K="+str(mu_GK)))
        print("{0:=^77}".format('='))
        for b in bolt_list:
            used_bolt = self.bolts.bolts[b]
            for m in bolt_mat_list:
                used_bolt_mat = self.materials.materials[m]
                # sig_m_zul acc. equ. (143) VDI2230
                # uses: Wp = d^3*pi/12 --> full tau plasticity 
                sig_m_zul = used_bolt_mat.sig_y/math.sqrt(1+3*(3/2*used_bolt.d2/used_bolt.ds*\
                    (used_bolt.p/(math.pi*used_bolt.d2)+1.155*mu_GK))**2)
                print("{0:.1f} MPa with Wp=d^3*pi/12".format(sig_m_zul))
                # uses: Wp = d^3*pi/16 --> tau fully elastic
                # use for ECSS / ESA PSS
                sig_m_zul = used_bolt_mat.sig_y/math.sqrt(1+3*(2*used_bolt.d2/used_bolt.ds*\
                    (used_bolt.p/(math.pi*used_bolt.d2)+1.155*mu_GK))**2)
                print("{0:.1f} MPa with Wp=d^3*pi/16".format(sig_m_zul))
                # permissible assembly preload
                F_M_zul = sig_m_zul*used_bolt.As*nue
                # tightening torque
                M_A = F_M_zul*(0.16*used_bolt.p+0.58*used_bolt.d2*mu_GK+used_bolt.dh/2*mu_GK)
                print("|{0:^12}|{1:^20}|{2:^20.1f}|{3:^20.1f}|"\
                    .format(b, m, F_M_zul/1000, M_A/1000))
            print("{0:-^77}".format('-'))

