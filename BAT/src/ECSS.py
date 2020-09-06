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
        self._calc_joint_stiffness()

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
        if D_avail > D_lim:
            print("D_avail > D_lim : {0:.2f} > {1:.2f}".format(D_avail,D_lim))
            print("CASE 1: fully developed into a cone")
        elif self.used_bolt.dh > D_avail:
            print("d_uh > D_avail : {0:.2f} > {1:.2f}".format(self.used_bolt.dh, D_avail))
            print("CASE 2: sleeve only")
        else: 
            print("d_uh < D_avail < D_lim : {0:.2f} < {1:.2f} < {2:.2f}".format(\
                self.used_bolt.dh, D_avail, D_lim))
            print("CASE 3: partial compression sleeve and cones")

    # Override: calculate embedding preload loss
    def _calc_embedding(self):
        pass

