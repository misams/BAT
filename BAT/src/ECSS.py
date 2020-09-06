from src.BoltAnalysisBase import BoltAnalysisBase
from src.functions.InputFileParser import InputFileParser
from src.functions.MaterialManager import MaterialManager
from src.functions.BoltManager import BoltManager
from src.functions.exceptions import EmbeddingInterfacesError
from pathlib import Path
import math
import logging
from datetime import datetime
"""
Bolt analysis according to ECSS-E-HB-32-23A, 16 April 2010
Space engineering - Threaded fasteners handbook

Concentric axially loaded joints
"""
class ECSS(BoltAnalysisBase):
    def __init__(self, inp_file : InputFileParser, materials : MaterialManager, bolts : BoltManager):
        # instantiate base class
        super().__init__(inp_file, materials, bolts)
        # 
        # calculate clamped-part stiffness
        self._calc_joint_stiffness()
        # calculate embedding and thermal losses of joint
        self._calc_embedding()
        self._calc_thermal_loss() # default: standard thermal method
        # calculate joint properties
        self._calc_joint_results()

    # Override: joint stiffness for bolt and clamped parts
    def _calc_joint_stiffness(self):
        # calc clamping length of all clamped parts
        for _, c in self.inp_file.clamped_parts.items():
            self.l_K += c[1] # add thickness of all clamped parts to l_K
        #
        # compliance of bolt / fastener [7.5.5, p.74]
        # 0.4*d used for head and nut/locking-device; see Table 7-1
        self.delta_b = 1/self.used_bolt_mat.E*( 0.4*self.used_bolt.d/self.used_bolt.A1 +\
            self.l_K/self.used_bolt.A3 + 0.4*self.used_bolt.d/self.used_bolt.A3)
        #
        # compliance of clamped parts
        D_avail = self.inp_file.egde_dist_flange*2
        # compression cone half angle [ch.7.6.3.3]
        x_phi = self.l_K/self.used_bolt.dh
        y_phi = D_avail/self.used_bolt.dh
        if self.inp_file.joint_type == "TBJ":
            tan_phi = 0.362+0.032*math.log(x_phi/2)+0.153*math.log(y_phi)
            w = 1
        else: # TTJ
            tan_phi = 1.295-0.246*math.log(x_phi)+0.94*math.log(y_phi)
            w = 2
        # limit diameter of compression cone
        D_lim = self.used_bolt.dh + w*self.l_K*tan_phi
        # existence of cone and sleeve
        # calculate A_sub (substitution are of clamped parts compliance)
        # delta_c = l_K/(E_c * A_sub) ...compliance equation
        if D_avail > D_lim:
            print("CASE 1: fully developed into a cone")
            print("D_avail > D_lim : {0:.2f} > {1:.2f}".format(D_avail,D_lim))
            tmp_log_D = ((self.used_bolt.dh+self.used_bolt.d)*(D_lim-self.used_bolt.d)) \
                      / ((self.used_bolt.dh-self.used_bolt.d)*(D_lim+self.used_bolt.d))
            # Equ. [7.6.10]
            x_c = 2*math.log(tmp_log_D)\
                           / (w*math.pi*self.used_bolt.d*tan_phi) # x_c = l_K/A_sub
        elif self.used_bolt.dh > D_avail:
            print("CASE 2: sleeve only")
            print("d_uh > D_avail : {0:.2f} > {1:.2f}".format(self.used_bolt.dh, D_avail))
            # Equ. [7.6.14]
            x_c = 4*self.l_K/(math.pi*(D_avail**2-self.used_bolt.d**2)) # x_c = l_K/A_sub
        else: 
            print("CASE 3: partial compression sleeve and cones")
            print("d_uh < D_avail < D_lim : {0:.2f} < {1:.2f} < {2:.2f}".format(\
                self.used_bolt.dh, D_avail, D_lim))
            tmp_log_D = ((self.used_bolt.dh+self.used_bolt.d)*(D_avail-self.used_bolt.d)) \
                      / ((self.used_bolt.dh-self.used_bolt.d)*(D_avail+self.used_bolt.d))
            # Equ. [7.6.11]
            x_c = (2/(w*self.used_bolt.d*tan_phi)*math.log(tmp_log_D) +\
                4/(D_avail**2-self.used_bolt.d**2)*(self.l_K-(D_avail-self.used_bolt.dh)/(w*tan_phi)))\
                    /(math.pi) # x_c = l_K/A_sub
        self.A_sub = self.l_K/x_c # substitutional area of clamped part compliance
        # calculate overall clamped part compliance
        self.delta_c = 0.0
        for _, c in self.inp_file.temp_clamped_parts.items():
            self.delta_c += c[1]/(self.A_sub*self.materials.materials[c[0]].E)
        # calculate force ratio
        self.Phi = self.delta_c/(self.delta_b+self.delta_c)
        self.Phi_n = self.inp_file.loading_plane_factor*self.Phi

    # Override: calculate embedding preload loss
    def _calc_embedding(self):
        # apprx. values for plastic deformation caused by embedding
        # Table 6-3 (larger value axial/shear used)
        if self.inp_file.emb_rz == "<10":
            f_Z_i = [3,3,2]
        elif self.inp_file.emb_rz == "10-40":
            f_Z_i = [3,4.5,2.5]
        elif self.inp_file.emb_rz == "40-160":
            f_Z_i = [3,6.5,3.5]
        else:
            f_Z_i = [999,999,999]
            # outside tabled values
            err_str = "Embedding: outside tabled values of Rz"
            logging.error(err_str)
            raise EmbeddingInterfacesError(err_str)
        #
        # calculate number of embedding interfaces (in mm)
        # 1 x thread
        # TBJ: 2 x under-head interface / TTJ: 1 x under-head interface
        # TBJ: #CP-1 / TTJ: #CP
        if self.inp_file.joint_type == "TBJ":
            self.f_Z = (f_Z_i[0] + 2*f_Z_i[1] + (len(self.inp_file.clamped_parts)-1)*f_Z_i[2])/1000
        else: # TTJ
            self.f_Z = (f_Z_i[0] + 1*f_Z_i[1] + len(self.inp_file.clamped_parts)*f_Z_i[2])/1000
        #
        # calculate embedding force
        self.F_Z = self.f_Z/(self.delta_b+self.delta_c)
