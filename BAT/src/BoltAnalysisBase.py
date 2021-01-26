from src.functions.InputFileParser import InputFileParser
from src.functions.MaterialManager import MaterialManager
from src.functions.BoltManager import BoltManager
from pathlib import Path
import math
import logging
from datetime import datetime
from abc import ABC, abstractmethod
from src.functions.exceptions import JointMosTypeError
"""
Bolt analysis BASE-class
ECSS-E-HB-32-23A & VDI2230 nomenclature-mix is used
(conversion is listed in comment for each variable)
"""
class BoltAnalysisBase(ABC):
    def __init__( self, 
                inp_file : InputFileParser,
                materials : MaterialManager,
                bolts : BoltManager,
                bat_version ):
        # main analysis inputs
        self.inp_file = inp_file
        self.materials = materials
        self.bolts = bolts
        self.bat_version = bat_version
        # used bolt and bolt-material for analysis (set by input-file)
        self.used_bolt = bolts.bolts[self.inp_file.bolt]
        self.used_bolt_mat = self.materials.materials[self.inp_file.bolt_material]
        # calculated variables
        self.M_p = None # prevailing torque (VDI2230:M_ue)
        self.l_K = 0.0 # joint / clamped length (ECSS:L_j)
        self.A_sub = 0.0 # substitution area of clamped parts compliance
        self.delta_b = 0.0 # bolt compliance (VDI2230:delta_S)
        self.delta_c = 0.0 # compliance of clamped parts (VDI2230:delta_P) 
        self.Phi = 0.0 # basic force ratio of a concentric joint (VDI2230:Phi)
        self.Phi_n = 0.0 # with loading plane factor effect (VDI2230:Phi_n)
        self.f_Z = 0.0 # plastic deform. due to embedding (VDI2230:f_Z)
        self.F_Z = 0.0 # preload loss due to embedding (VDI2230:F_Z)
        self.dF_V_th = None # change in preload due to CTE missmatch [FT_min, FT_max]
        self.E_b_th = None # Youngs Modulus bolt [E_b_RT, E_b_T]
        self.E_c_th = None # Youngs Modulus clamped parts [E_c_RT, E_c_T]
        self.alpha_b_th = None # CTE bolt [alpha_b_RT, alpha_b_T]
        self.alpha_c_th = None # CTE clamped parts [alpha_c_RT, alpha_c_T]
        self.nmbr_of_bolts = len(self.inp_file.bolt_loads) # for global slippage analysis
        self.F_M = None # preload after tightening / assembly preload [min, max]
        self.F_V = None # service preload (incl. embedding and thermal losses) [min, max]
        self.alpha_A = 0.0 # tightening factor 
        self.tau = None # 100% torsional stress aft. tightening [min, max]
        self.sig_n = None # normal stress aft. tightening [min, max]
        self.sig_v = None # von-Mises stress aft. tightening [min, max]
        self.nue = None # bolt utilization [min, max] (ECSS: gamma)
        self.bolt_results = {} # results per bolt / loadcase
        self.MOS_glob_slip = 0.0 # global slippage margin
        self.MOS_pres = 0.0 # yield check under bolt head 

    # joint stiffness for bolt and clamped parts
    @abstractmethod
    def _calc_joint_stiffness(self):
        pass

    # calculate embedding preload loss
    @abstractmethod
    def _calc_embedding(self):
        pass

    # calculate joint results 
    @abstractmethod
    def _calc_joint_results(self):
        pass

    # get output string
    @abstractmethod
    def _get_output_str(self):
        pass

    # calculate thermal effects on preload (preload loss / increase)
    # preload change in bolt: clamped parts - bolts (convention)
    # sign-convention: minus (-) is loss in preload
    # if alpha_c > alpha_b : FT_res (+)
    # if alpha_c < alpha_b : FT_res (-)
    def _calc_thermal(self):
        # thermal expansion of bolt
        d_l_b = self.used_bolt_mat.alpha * self.l_K * self.inp_file.delta_t
        # add all clamped parts thermal expansions
        d_l_c = 0.0
        for _, c in self.inp_file.clamped_parts.items():
            d_l_c += self.materials.materials[c[0]].alpha * c[1] * self.inp_file.delta_t
        # delta-length between clamped parts and bolt
        d_l = d_l_c - d_l_b
        # preload loss due to thermal effects
        c_b = 1/self.delta_b # bolt stiffness
        c_c = 1/self.delta_c # clamped parts stiffness
        FT_res = d_l*(c_b*c_c)/(c_b+c_c)
        self.dF_V_th = [FT_res, FT_res] # save FT for FPreMin & FPreMax
        #
        # set Young's modulus and CTE for output
        self.E_b_th = [self.used_bolt_mat.E, self.used_bolt_mat.E] # bolt E @RT and @T
        E_c = self.l_K/(self.delta_c*self.A_sub) # Young's modulus of clamped parts
        self.E_c_th = [E_c, E_c] # clamped parts E @RT and @T
        self.alpha_b_th = [self.used_bolt_mat.alpha, self.used_bolt_mat.alpha] # CTE bolt @RT and @T
        # add all clamped parts thermal expansions; delta_T = 1 for average alpha analysis
        d_l_P = 0.0 # at RT
        for _, c in self.inp_file.clamped_parts.items():
            d_l_P += self.materials.materials[c[0]].alpha * c[1] * 1.0
        # overall/mean alpha of clamped parts
        alpha_PRT = d_l_P/(1.0*self.l_K)
        self.alpha_c_th = [alpha_PRT, alpha_PRT] # CTE clamped parts @RT and @T

    # VDI method for thermal preload loss (Young's Modulus variation taken into account)
    # VDI2230 nomenclature used
    def _calc_thermal_VDI(self, F_VRT_min, F_VRT_max):
        # calculate clamped part stiffness cPT at temperature T
        # --> used for Young's Modulus E_PT calculation only
        cPT = 0.0
        for _, c in self.inp_file.temp_clamped_parts.items():
            cPT += 1./(self.A_sub*self.materials.materials[c[0]].E/c[1])
        cPT = 1./cPT # clamped part stiffness' in series
        # get material properties at correct temperatures
        E_SRT = self.used_bolt_mat.E # E of bolt at RT
        E_ST = self.materials.materials[self.inp_file.temp_bolt_material].E
        self.E_b_th = [E_SRT, E_ST] # bolt E @RT and @T
        E_PRT = (1/self.delta_c)*self.l_K/self.A_sub # E_overall_mean of clamped parts at RT
        E_PT = cPT*self.l_K/self.A_sub
        self.E_c_th = [E_PRT, E_PT] # clamped parts E @RT and @T
        alpha_SRT = self.used_bolt_mat.alpha
        alpha_ST = self.materials.materials[self.inp_file.temp_bolt_material].alpha
        self.alpha_b_th = [alpha_SRT, alpha_ST] # CTE bolt @RT and @T
        # add all clamped parts thermal expansions
        d_l_P = 0.0 # at RT
        for _, c in self.inp_file.clamped_parts.items():
            d_l_P += self.materials.materials[c[0]].alpha * c[1] * self.inp_file.delta_t
        d_l_P_T = 0.0 # at T
        for _, c in self.inp_file.temp_clamped_parts.items():
            d_l_P_T += self.materials.materials[c[0]].alpha * c[1] * self.inp_file.delta_t
        # overall/mean alpha of clamped parts
        alpha_PRT = d_l_P/(self.inp_file.delta_t*self.l_K)
        alpha_PT = d_l_P_T/(self.inp_file.delta_t*self.l_K)
        self.alpha_c_th = [alpha_PRT, alpha_PT] # CTE clamped parts @RT and @T
        # calculate preload loss with E taken into account
        # reduction of preload (alpha_ST and alpha_PT used acc. to VDI2230)
        # sign (-) is loss in preload
        dS = self.delta_b # compliance of bolt
        dP = self.delta_c # compliance of clamped parts
        denom = dS*E_SRT/E_ST + dP*E_PRT/E_PT # denominator
        # multiply d_F_th with (-1) to get correct sign convention
        dF_th_min = (F_VRT_min * (1 - (dS+dP)/denom) \
            + self.l_K*(alpha_ST - alpha_PT)*self.inp_file.delta_t/denom)*(-1)
        dF_th_max = (F_VRT_max * (1 - (dS+dP)/denom) \
            + self.l_K*(alpha_ST - alpha_PT)*self.inp_file.delta_t/denom)*(-1)
        self.dF_V_th = [dF_th_min, dF_th_max]

    # check yield MoS under bolt head and between washer and first clamped part
    def _mos_pres(self, F_axial, use_temp_mat_props="no"):
        # yield strength of first clamped part (under washer)
        # if VDI thermal method used, use temp. dependent sig_y and sig_u for MOS evaluation
        if use_temp_mat_props == "yes":
            sig_y_pres = self.materials.materials[self.inp_file.temp_clamped_parts[1][0]].sig_y
            sig_y_pres_shim = self.materials.materials[self.inp_file.temp_use_shim[0]].sig_y \
                if self.inp_file.use_shim!="no" else 0.0
            log_str = "Temperature dependent yield strength of shim and first "\
                + "clamped part used for MOS_pres, F_axial = {0:.1f}".format(F_axial)
            print(log_str)
            logging.info(log_str)
        else:
            sig_y_pres = self.materials.materials[self.inp_file.clamped_parts[1][0]].sig_y
            sig_y_pres_shim = self.materials.materials[self.inp_file.use_shim[0]].sig_y \
                if self.inp_file.use_shim!="no" else 0.0
        # MOS with or without washer
        if self.inp_file.use_shim != "no": # with washer
            # minimal area under bolt head
            A_pres_1 = (self.used_bolt.dh**2)*math.pi/4 - \
                (self.bolts.washers[self.inp_file.use_shim[1]].dmin**2)*math.pi/4
            # yield strength of first washer (under bolt head)
            MOS_pres_1 = sig_y_pres_shim / (F_axial/A_pres_1) - 1
            # minimal area under washer and first clamped part
            A_pres_2 = (self.bolts.washers[self.inp_file.use_shim[1]].dmaj**2)*math.pi/4 - \
                (self.inp_file.through_hole_diameter**2)*math.pi/4
            MOS_pres_2 = sig_y_pres / (F_axial/A_pres_2) - 1
            # minimum MOS_pres
            MOS_pres = min(MOS_pres_1, MOS_pres_2)
        else: # without washer
            # minimal area under bolt head
            A_pres = (self.used_bolt.dh**2)*math.pi/4 - \
                (self.inp_file.through_hole_diameter**2)*math.pi/4
            MOS_pres = sig_y_pres / (F_axial/A_pres) - 1
        return MOS_pres

    # print results to terminal and/or file
    def print_results(self, output_file=None, print_to_cmd=True):
        if print_to_cmd is True:
            print() # print empty line
            # print BAT output
            print(self._get_output_str())
         # print results to output_file
        if output_file != None:
            output_file = Path(output_file)
            log_str = "Output file written: {0:^}".format(str(output_file.absolute()))
            print(log_str)
            logging.info(log_str)
            # write output file
            with open(output_file, 'w') as fid:
                # write BAT output to file
                fid.write(self._get_output_str())
                # write timestamp to output file
                fid.write("BAT Analysis Timestamp: {0:^}\n".format(\
                    str(datetime.now().strftime("%d-%m-%Y %H:%M:%S"))))
        # return string
        return self._get_output_str()