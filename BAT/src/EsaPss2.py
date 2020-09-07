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
Bolt analysis according to ESA PSS-03-208 Issue 1, December 1989
Guidelines for threaded fasteners, european space agency

Concentric axially loaded joints
"""
class EsaPss2(BoltAnalysisBase):
    def __init__(self, inp_file : InputFileParser, materials : MaterialManager, 
                bolts : BoltManager, bat_version):
        # instantiate base class
        super().__init__(inp_file, materials, bolts, bat_version)
        # 
        # calculate clamped-part stiffness
        self._calc_joint_stiffness()
        # calculate embedding and thermal preload changes of joint
        self._calc_embedding()
        self._calc_thermal()
        # calculate joint properties
        self._calc_joint_results()

    # @Override: joint stiffness for bolt and clamped parts
    def _calc_joint_stiffness(self):
        # calc clamping length of all clamped parts
        for _, c in self.inp_file.clamped_parts.items():
            self.l_K += c[1] # add thickness of clamped parts to lk
        # add length for bolt head + nut for stiffness
        lB = self.l_K + 0.8*self.used_bolt.d
        # stiffness of bolt - cB
        # calc stiffness of bolt, p.5-3; stiffer, average value (SHM)
        cB = (self.used_bolt_mat.E*(self.used_bolt.A1+\
            self.used_bolt.Ap)/2.0)/lB # stiffness cB bolt
        self.delta_b = 1/cB # bolt compliance SHM
        # bolt compliance p.5-15 ESA-PSS
        #TODO: check different cB values for result impact; cB SHM conservative??
        #self.delta_b = 1/self.used_bolt_mat.E*( 0.4*self.used_bolt.d/self.used_bolt.A1 +\
        #    self.l_K/self.used_bolt.A3 + 0.4*self.used_bolt.d/self.used_bolt.A3)
        #
        # Joint elastic compliance for joints with large areas of contact, p.6-7ff.
        # TODO: rework SUBST_DA topic!
        # calc substitutional area for clamped parts
        if self.lk/self.used_bolt.d >= 1.0 and self.lk/self.used_bolt.d <=2:
            logging.info("Calculate Asub acc. to case (ii)")
            # if *SUBST_DA = no use rule of thumb for DA estimation, p.6-11
            if self.inp_file.subst_da != "no":
                self.DA = float(self.inp_file.subst_da)
                logging.info("Substitutional diameter DA set: {0:.2f}".format(self.DA))
            else:
                self.DA = self.used_bolt.dh*(2.+3.)/2. # mean value betw. range 2-3 used, p.6-11
                logging.info("Mean substitutional diameter DA set (rule of thumb): {0:.2f}".format(self.DA))
            # calc subst. area for clamped parts
            self.Asub = math.pi/4*( self.used_bolt.dh**2-self.inp_file.through_hole_diameter**2 ) +\
                math.pi/8*( self.DA/self.used_bolt.dh-1 ) *\
                ( self.used_bolt.dh*self.lk/5+(self.lk**2)/100 )
        elif self.lk/self.used_bolt.d > 2.0:
            logging.info("Calculate Asub acc. to case (iii)")
            self.Asub = math.pi/4*((self.used_bolt.dh+self.lk/10)**2 - \
                self.inp_file.through_hole_diameter**2)
        else:
            self.Asub = math.pi/4*(self.used_bolt.dh**2 - self.inp_file.through_hole_diameter**2)
            warn_str = "WARNING: Asub acc. to case (i). DA == dK --> use with caution!"
            print(warn_str)
            logging.warning(warn_str)
        # calc Dsub out of Asub
        self.Dsub = math.sqrt(4*self.Asub/math.pi + self.inp_file.through_hole_diameter**2)

        # Asub (SHM)
        #self.lk = self.lk - self.used_washer.h
        #self.used_bolt.dh = 12.3
        #self.used_washer.dmaj = 16
        #self.inp_file.through_hole_diameter = 8.4
        #self.Asub = math.pi/4*(self.used_bolt.dh**2-self.inp_file.through_hole_diameter**2+math.pi/8*\
        #    (self.used_washer.dmaj/self.used_bolt.dh-1)*(self.used_bolt.dh*self.lk/5+\
        #        self.lk**2/100)) # with wrong parentheses 
        #self.Asub = math.pi/4*( self.used_bolt.dh**2-self.inp_file.through_hole_diameter**2 ) +\
        #    math.pi/8*( self.used_washer.dmaj/self.used_bolt.dh-1 ) *\
        #        ( self.used_bolt.dh*self.lk/5+self.lk**2/100 ) # with corrected parentheses

        # calculate stiffness of clamped parts - cP
        for _, c in self.inp_file.clamped_parts.items():
            self.cP += 1./(self.Asub*self.materials.materials[c[0]].E/c[1])
        self.cP = 1./self.cP # clamped part stiffness' in series

        # load-factor
        self.phi_K = self.cB/(self.cB+self.cP) # load factor - load under bolt head
        self.phi_n = self.inp_file.loading_plane_factor*self.phi_K # load factor - load at n*lk


    # @Override: calculate embedding preload loss
    def _calc_embedding(self):
        pass

    # @Override: calculate joint results 
    def _calc_joint_results(self):
        pass

    # get analysis input (file) string for printout
    def _get_input_str(self):
        pass

    # get global analysis results string
    def _get_global_result_str(self):
        pass

    # get results per bolt/loadcase string
    def _get_bolt_result_str(self):
        pass

    # get thermal analysis string
    def _get_thermal_result_str(self):
        output_str = "" # use output_str for print() or print-to-file
        output_str += "{0:=^95}\n".format('=') # global splitter
        if self.inp_file.temp_use_vdi_method.casefold() == "yes":
            output_str += "| {0:^50}|{1:^20}|{2:^20}|\n".format("VDI 2230 Thermal Preload Method",\
                "Room-Temp (ref)", "defined Temp.")
        else:
            output_str += "| {0:^50}|{1:^20}|{2:^20}|\n".format("Thermal Preload Analysis",\
                "Room-Temp (ref)", "defined Temp.")
        output_str += "{0:=^95}\n".format('=')
        output_str += "| {0:<50}|{1:^20.1f}|{2:^20.1f}|\n".format(\
            "Young's Modulus of bolt [MPa]:", self.E_b_th[0], self.E_b_th[1])
        output_str += "| {0:<50}|{1:^20.1f}|{2:^20.1f}|\n".format(\
            "Young's Modulus of clamped parts [MPa]:", self.E_c_th[0], self.E_c_th[1])
        output_str += "| {0:<50}|{1:^20.3e}|{2:^20.3e}|\n".format(\
            "CTE of bolt [1/K]:", self.alpha_b_th[0], self.alpha_b_th[1])
        output_str += "| {0:<50}|{1:^20.3e}|{2:^20.3e}|\n".format(\
            "CTE of clamped parts [1/K]:", self.alpha_c_th[0], self.alpha_c_th[1])
        output_str += "|-{0:-^50}+{1:-^20}+{2:-^20}|\n".format("-", "-", "-")
        output_str += "| {0:<64} {1:^27.1f}|\n".format(\
            "Temperature difference delta_T [K]:", self.inp_file.delta_t)
        output_str += "|-{0:-^50}-{1:-^20}-{2:-^20}|\n".format("-", "-", "-")
        #output_str += "| {0:<64} {1:>12.1f} / {2:<12.1f}|\n".format(\
        #    "Term-1 preload loss based on FVmin / FVmax [N]:",\
        #    F_VRT_min*(1-(dS+dP)/denom)*(-1), F_VRT_max*(1-(dS+dP)/denom)*(-1) )
        #output_str += "| {0:<64} {1:^27.1f}|\n".format(\
        #    "Term-2 Preload loss based on CTE [N]:",\
        #        self.lk*(alpha_ST-alpha_PT)*self.inp_file.delta_t/denom*(-1) )
        output_str += "| {0:<64} {1:>12.1f} / {2:<12.1f}|\n".format(\
            "Preload loss due to thermal effects based on FVmin / FVmax [N]:",\
                self.dF_V_th[0], self.dF_V_th[1])
        output_str += "{0:=^95}\n".format('=') # global splitter
        return output_str

    # @Override: get output string
    def _get_output_str(self):
        outp_str = ""
        if self.inp_file.delta_t != 0: # add thermal output str if delta_T is not 0
            outp_str = self._get_input_str() + self._get_global_result_str() +\
                self._get_thermal_result_str() + self._get_bolt_result_str()
        else:
            outp_str = self._get_input_str() + self._get_global_result_str() +\
                self._get_bolt_result_str()
        return outp_str
