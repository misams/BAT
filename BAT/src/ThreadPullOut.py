from src.functions.MaterialManager import MaterialManager
from src.functions.BoltManager import BoltManager
from pathlib import Path
import math
"""
Thread pull-out analysis acc. to VDI2230 §5.5.5
"""
class ThreadPullOut:
    def __init__( self, materials : MaterialManager, bolts : BoltManager):
        # main analysis inputs
        self.materials = materials
        self.bolts = bolts
        # calculate torque table
        self._calc_thread_pull_out()

    def _calc_thread_pull_out(self):
        # define bolt type and material
        bolt = "S_M10"
        bolt_mat = "8.8"
        bolt_ssr = 0.8 # shear strength ratio Tau_B/R_m (VDI2230: Table 6)
        # define female-thread material
        nut_D1 = 8.376 # Kerndurchmesser-Mutter 
        nut_mat = "S355"
        nut_ssr = 0.8 # shear strength ratio Tau_B/R_m (VDI2230: Table 6)
        nut_s = 16 # Schluesselweite der Mutter

        # calculate strength ratio R_S
        tau_BM = self.materials.materials[nut_mat].sig_u*nut_ssr # shear strength of nut (female thread)
        tau_BS = self.materials.materials[bolt_mat].sig_u*bolt_ssr # shear strength of nut (female thread)
        b = self.bolts.bolts[bolt] # used bolt
        R_S = tau_BM/tau_BS * (b.d*(b.p/2*(b.d-b.d2)*math.tan(30*math.pi/180))) \
            / (nut_D1*(b.p/2*(b.d2-nut_D1)*math.tan(30*math.pi/180)))
        # if R_S>1 the nut or internal thread is critical --> at risk of stripping
        # calculate nut-coefficients C_1 and C3
        if 1.4 <= nut_s/b.d <= 1.9:
            C_1 = 3.8*nut_s/b.d - (nut_s/b.d)**2 - 2.61
        elif nut_s/b.d >1.9:
            C_1 = 1.0
        else:
            C_1 = 0.0
            print("ERROR: s/d < 1.4")
        # C_3
        if 0.4 < R_S < 1.0:
            C_3 = 0.728 + 1.769*R_S - 2.896*R_S**2 + 1.296*R_S**3
        elif R_S <= 0.4:
            R_S = 0.4 # if R_S<0.4 --> set R_S=0.4
            C_3 = 0.728 + 1.769*R_S - 2.896*R_S**2 + 1.296*R_S**3
        else:
            C_3 = 0.897 # if R_S >= 1.0
        # m_ges
        m_ges = self.materials.materials[bolt_mat].sig_u*b.As*b.p / (C_1 * C_3 * tau_BM \
            *(b.p/2+(b.d-b.d2)*math.tan(30*math.pi/180))*math.pi*b.d) + b.p*2
        print("R_S = {0:.3f}".format(R_S))
        print("C_1 = {0:.3f}".format(C_1))
        print("C_3 = {0:.3f}".format(C_3))
        print("\nm_ges = {0:.2f} mm".format(m_ges))