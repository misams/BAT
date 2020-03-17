from .InputFileParser import InputFileParser
from .MaterialManager import MaterialManager
from .BoltManager import BoltManager
import math
"""
Bolt analysis according to ESA-PSS xx??
"""
class EsaPss:
    def __init__(self, inp_file : InputFileParser, materials : MaterialManager, bolts : BoltManager):
        self.inp_file = inp_file
        self.materials = materials
        self.bolts = bolts
        #
        self.used_bolt = bolts.bolts[self.inp_file.bolt_size] # used bolt
        self.used_bolt_mat = self.materials.bolt_mat[self.inp_file.bolt_material]
        self.used_washer = bolts.washers[self.inp_file.use_shim] # "no" or washer-id
        # calculate clamped-part stiffness
        self.__calc_stiff_clamp_parts()

    # clamped part stiffness
    def __calc_stiff_clamp_parts(self):
        # calc clamping length of all clamped parts
        lk = 0.0
        for _, c in self.inp_file.clamped_parts.items():
            lk += c[1] # add thickness of clamped parts to lk
        # calc length of tensional bolt incl. washer and part of the head
        if self.used_washer.name.lower() != "no":
            lB = lk + self.used_washer.h + 0.8*self.used_bolt.d
        else:
            lB = lk + 0.8*self.used_bolt.d
        # calc stiffness of bolt
        AB = math.pow(self.used_bolt.d, 2.0)*math.pi/4.0
        Ap = math.pow(self.used_bolt.d2, 2.0)*math.pi/4.0
        cB = (self.used_bolt_mat.E*(AB+Ap)/2.0)/lB # stiffness cB bolt
