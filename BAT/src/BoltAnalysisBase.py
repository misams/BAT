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
        self.ana_method = "" # analysis method for printed output
        # used bolt and bolt-material for analysis (set by input-file)
        self.used_bolt = bolts.bolts[self.inp_file.bolt]
        self.used_bolt_mat = self.materials.materials[self.inp_file.bolt_material]
        # calculated variables
        self.M_p = self.inp_file.prevailing_torque # prevailing torque (VDI2230:M_ue)
        self.T_scatter = 0.0 # scatter of tightening device (e.g. torque-wench)
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
        # set T_scatter
        self._set_T_scatter()

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

    # get analysis input (file) string for printout
    def _get_input_str(self):
        output_str = "" # use output_str for print() or print-to-file
        output_str += "{0:=^95}\n".format('=') # global splitter
        output_str += "| {0:^91} |\n".format("BAT Bolt Analysis Input (v"+self.bat_version+")")
        output_str += "| {0:^91} |\n".format(" ")
        output_str += "| {0:^91} |\n".format(self.inp_file.project_name)
        output_str += "{0:=^95}\n".format('=')
        output_str += "| {0:<50} {1:^20} {2:^20}|\n".format(\
            "BAT method:", self.inp_file.method, "")
        output_str += "| {0:<50} {1:^20} {2:^20}|\n".format(\
            "Joint type:", self.inp_file.joint_type, "")
        output_str += "| {0:<50} {1:^20} {2:^20}|\n".format(\
            "Joint MoS type:", self.inp_file.joint_mos_type, "")
        output_str += "| {0:<50} {1:^20} {2:^20}|\n".format(\
            "Bolt:", self.inp_file.bolt, "")
        output_str += "| {0:<50} {1:^20} {2:^20}|\n".format(\
            "Bolt material:", self.inp_file.bolt_material, "")
        if self.inp_file.torque_tol_tight_device.find('%')!=-1:
            scatter_str = "\u00B1{1:.2f} ({0:^})".format(self.inp_file.torque_tol_tight_device, self.T_scatter)
        else:
            scatter_str = "\u00B1{0:.2f}".format(self.T_scatter)
        output_str += "| {0:<50} {1:^20} {2:^20}|\n".format(\
            "Torque tolerance of tight. device [Nm]:", scatter_str, "")
        output_str += "| {0:<50} {1:^20} {2:^20}|\n".format(\
            "Locking mechanism used:", self.inp_file.locking_mechanism, "")
        output_str += "| {0:<50} {1:^20.2f} {2:^20}|\n".format(\
            "Loading plane factor - n:", self.inp_file.loading_plane_factor, "")
        output_str += "| {0:<50} {1:^20d} {2:^20}|\n".format(\
            "Number of shear planes:", self.inp_file.nmbr_shear_planes, "")
        output_str += "| {0:<50} {1:^20.2f} {2:^20}|\n".format(\
            "Through hole diameter [mm]:", self.inp_file.through_hole_diameter, "")
        output_str += "| {0:<50} {1:^20} {2:^20}|\n".format(\
            "Shim used:", "yes" if self.inp_file.use_shim!="no" else "no", "")
        output_str += "| {0:<50} {1:^20.2f} {2:^20}|\n".format(\
            "Subst. outs. dia. of basic solid DA [mm]:", self.inp_file.subst_da, "")
        output_str += "| {0:<50} {1:^20} {2:^20}|\n".format(\
            "Embedding surf. rough. Rz [micron]:", self.inp_file.emb_rz, "")
        output_str += "|{0:-^93}|\n".format('-') # empty line within section
        # factors of safety
        output_str += "| {0:<40} {1:<30} {2:^20.2f}|\n".format(\
            "Factor of safety yield", "FOS_y:", self.inp_file.fos_y)
        output_str += "| {0:<40} {1:<30} {2:^20.2f}|\n".format(\
            "Factor of safety ultimate", "FOS_u:", self.inp_file.fos_u)
        output_str += "| {0:<40} {1:<30} {2:^20.2f}|\n".format(\
            "Factor of safety slippage", "FOS_slip:", self.inp_file.fos_slip)
        output_str += "| {0:<40} {1:<30} {2:^20.2f}|\n".format(\
            "Factor of safety gapping", "FOS_gap:", self.inp_file.fos_gap)
        output_str += "| {0:<40} {1:<30} {2:^20.2f}|\n".format(\
            "Fitting-Factor", "FITF:", self.inp_file.fos_fit)
        output_str += "|{0:-^93}|\n".format('-') # empty line within section
        # list clamped parts with properties
        cp = self.inp_file.clamped_parts
        tmp_shim_str = "" # add "Shim" to CP(0)
        for i in range(len(cp)):
            # shim handling for output string
            if self.inp_file.use_shim != "no" and i==0:
                tmp_shim_str = " - Shim / Washer" 
            elif self.inp_file.use_shim != "no" and i>0:
                tmp_shim_str = ""
            else:
                i += 1 # add 1 if no shim is used; shim is always [0]
            output_str += "| {0:<40} {1:<30} {2:^20}|\n".format(\
                "Clamped-Part ("+str(i)+")"+tmp_shim_str, "Material:", cp[i][0])
            output_str += "| {0:<40} {1:<30} {2:^20.2f}|\n".format(\
                " ", "Thickness [mm]:", cp[i][1])
            output_str += "| {0:<40} {1:<30} {2:^20.1f}|\n".format(\
                " ", "Young's modulus @RT [MPa]:", self.materials.materials[cp[i][0]].E)
            output_str += "| {0:<40} {1:<30} {2:^20.1f}|\n".format(\
                " ", "Yield strength @RT [MPa]:", self.materials.materials[cp[i][0]].sig_y)
            output_str += "| {0:<40} {1:<30} {2:^20.1f}|\n".format(\
                " ", "Ultimate strength @RT [MPa]:", self.materials.materials[cp[i][0]].sig_u)
            output_str += "| {0:<40} {1:<30} {2:^20.3e}|\n".format(\
                " ", "CTE [1/K]:", self.materials.materials[cp[i][0]].alpha)
        output_str += "{0:=^95}\n".format('=') # global splitter
        return output_str

    # get global analysis results string
    def _get_global_result_str(self):
        output_str = "" # use output_str for print() or print-to-file
        output_str += "{0:=^95}\n".format('=') # global splitter
        output_str += "| {0:^91} |\n".format(self.ana_method)
        output_str += "{0:=^95}\n".format('=')
        output_str += "| {0:<50} {1:^20.2f} {2:^20}|\n".format(\
            "Clamped length l_K [mm]:", self.l_K, "")
        output_str += "| {0:<50} {1:^20.2f} {2:^20}|\n".format(\
            "Subst. area of CP compliance Asub [mm^2]:", self.A_sub, "")
        output_str += "| {0:<50} {1:^20.4g} {2:^20}|\n".format(\
            "Bolt stiffness c_B [N/mm]:", 1/self.delta_b, "")
        output_str += "| {0:<50} {1:^20.4g} {2:^20}|\n".format(\
            "Clamped part stiffness c_c [N/mm]:", 1/self.delta_c, "")
        output_str += "| {0:<50} {1:^20.4f} {2:^20}|\n".format(\
            "Load factor Phi [-]:", self.Phi, "")
        output_str += "| {0:<50} {1:^20.4f} {2:^20}|\n".format(\
            "Load factor Phi_n [-]:", self.Phi_n, "")
        output_str += "| {0:<50} {1:^20.2f} {2:^20}|\n".format(\
            "Embedding f_Z [micron]:", self.f_Z, "")
        output_str += "| {0:<50} {1:^20.1f} {2:^20}|\n".format(\
            "Preload loss due embedding F_Z [N]:", self.F_Z, "")
        # if VDI method used
        if self.inp_file.temp_use_vdi_method.casefold() == "yes":
            output_str += "| Preload loss due to thermal effects {0:^56}|\n".format(" ")
            output_str += "| {0:<50} {1:>14.1f} / {2:<24.1f}|\n".format(\
                "  based on FVmin / FVmax [N] (VDI method):",\
                    self.dF_V_th[0], self.dF_V_th[1])
        else:
            output_str += "| {0:<50} {1:^20.1f} {2:^20}|\n".format(\
                "Preload loss due thermal effects dF_V_th [N]:", self.dF_V_th[0], "")
        # min / max table
        output_str += "{0:=^95}\n".format('=') # global splitter
        output_str += "| {0:^50}|{1:^20}|{2:^20}|\n".format("", "MIN (mu_max)", "MAX (mu_min)")
        output_str += "{0:=^95}\n".format('=')
        output_str += "| {0:<50}|{1:^41.1f}|\n".format(\
            "Tightening torque with prevailing torque [Nm]:", self.inp_file.tight_torque)
        output_str += "| {0:<50}|{1:^20.1f}|{2:^20.1f}|\n".format(\
            "Tightening torque with tight. device scatter [Nm]:", \
                self.inp_file.tight_torque-self.T_scatter, self.inp_file.tight_torque+self.T_scatter)
        output_str += "| {0:<50}|{1:^20.1f}|{2:^20.1f}|\n".format(\
            "Prevailing torque (max | min) [Nm]:", self.M_p[1], self.M_p[0])
        output_str += "| {0:<50}|{1:^20.1f}|{2:^20.1f}|\n".format(\
            "Tightening torque w/o prevailing torque [Nm]:", self.inp_file.tight_torque-self.M_p[1]-self.T_scatter,\
                self.inp_file.tight_torque-self.M_p[0]+self.T_scatter)
        output_str += "|-{0:-^50}+{1:-^20}+{2:-^20}|\n".format("-", "-", "-") # empty line in table
        output_str += "| {0:<50}|{1:^20.3f}|{2:^20.3f}|\n".format(\
            "Coefficient of friction under bolt head:", self.inp_file.cof_bolt[0],\
                self.inp_file.cof_bolt[2])
        output_str += "| {0:<50}|{1:^20.3f}|{2:^20.3f}|\n".format(\
            "Coefficient of friction in thread:", self.inp_file.cof_bolt[1],\
                self.inp_file.cof_bolt[3])
        output_str += "| {0:<50}|{1:^41.2f}|\n".format(\
            "Coefficient of friction between clamped parts:", self.inp_file.cof_clamp)
        output_str += "|-{0:-^50}+{1:-^20}+{2:-^20}|\n".format("-", "-", "-") # empty line in table
        output_str += "| {0:<50}|{1:^20.1f}|{2:^20.1f}|\n".format(\
            "Bolt preload after tightening [N]:", self.F_M[0], self.F_M[1])
        output_str += "| {0:<50}|{1:^41.1f}|\n".format(\
            "MEAN Bolt preload after tightening [N]:", 0.5*(self.F_M[0]+self.F_M[1]))
        output_str += "| {0:<50}|{1:>19.2f} / \u00B1{2:<18.1%}|\n".format(\
            "Preload Scatter / Tightening Factor Alpha_A [-]:",\
                self.alpha_A, (self.alpha_A-1)/(self.alpha_A+1))
        output_str += "| {0:<50}|{1:^20.1f}|{2:^20.1f}|\n".format(\
                "Total preload loss incl. emb. & temp. [N]:", \
                    self.dF_V_th[0]+self.F_Z, self.dF_V_th[1])
        output_str += "| {0:<50}|{1:^20.1f}|{2:^20.1f}|\n".format(\
            "Bolt preload at service incl. emb. & temp. [N]:", self.F_V[0], self.F_V[1])
        output_str += "| {0:<50}|{1:^41.1f}|\n".format(\
            "MEAN Bolt preload at serv. incl. emb. & temp. [N]:", 0.5*(self.F_V[0]+self.F_V[1]))
        output_str += "|-{0:-^50}+{1:-^20}+{2:-^20}|\n".format("-", "-", "-")
        output_str += "| {0:<50}|{1:^20.1f}|{2:^20.1f}|\n".format(\
            "Torsional stress after tightening [MPa]:", self.tau[0], self.tau[1])
        output_str += "| {0:<50}|{1:^20.1f}|{2:^20.1f}|\n".format(\
            "Normal stress after tightening [MPa]:", self.sig_n[0], self.sig_n[1])
        output_str += "| {0:<50}|{1:^20.1f}|{2:^20.1f}|\n".format(\
            "Von-Mises equiv. stress aft. tightening [MPa]:", self.sig_v[0], self.sig_v[1])
        output_str += "| {0:<50}|{1:^20.1%}|{2:^20.1%}|\n".format(\
            "Bolt utilization [%]:", self.nue[0], self.nue[1])
        output_str += "|-{0:-^50}+{1:-^20}+{2:-^20}|\n".format("-", "-", "-")
        output_str += "| {0:<50}|{1:^20}|{2:^20.0%}|\n".format(\
            "Min. MoS (yield) under bolt head / washer [%]:", "-", self.MOS_pres)
        output_str += "{0:=^95}\n".format('=')
        # return output_str
        return output_str

    # get results per bolt/loadcase string
    def _get_bolt_result_str(self):
        output_str = "" # use output_str for print() or print-to-file
        # define header
        output_str += "{0:=^127}\n".format('=')
        # lc_name : [FA, FQ, FSA, FPA, MOS_loc_slip, MOS_gap, MOS_y, MOS_u, MOS_loc_pres]
        output_str += "|{0:^8}|{1:^12}|{2:^12}|{3:^12}|{4:^12}|{5:^12}|{6:^12}|{7:^12}|{8:^12}|{9:^12}|\n"\
            .format("Number", "Bolt-ID", "Axial Bolt", "Shear Bolt", "Add. Bolt", "Red. Clmp.", \
            "Slippage", "Gapping", "Yield", "Ultimate")
        output_str += "|{0:^8}|{1:^12}|{2:^12}|{3:^12}|{4:^12}|{5:^12}|{6:^12}|{7:^12}|{8:^12}|{9:^12}|\n"\
            .format("#", "or", "Force", "Force", "Force", "Force", "MOS", "MOS", "MOS", "MOS")
        output_str += "|{0:^8}|{1:^12}|{2:^12}|{3:^12}|{4:^12}|{5:^12}|{6:^12}|{7:^12}|{8:^12}|{9:^12}|\n"\
            .format("", "Loadcase", "FA [N]", "FQ [N]", "FSA [N]", "FPA [N]", "", "", "", "")
        output_str += "|{0:^8}|{1:^12}|{2:^12}|{3:^12}|{4:^12}|{5:^12}|{6:^12}|{7:^12}|{8:^12}|{9:^12}|\n"\
            .format("", "", "FITF="+str(self.inp_file.fos_fit), "FITF="+str(self.inp_file.fos_fit), "", "", \
                "FOS="+str(self.inp_file.fos_slip), "FOS="+str(self.inp_file.fos_gap),\
                "FOS="+str(self.inp_file.fos_y), "FOS="+str(self.inp_file.fos_u))
        output_str += "{0:=^127}\n".format('=')
        # loop through bolts / loadcases
        bolt_nmbr = 0 # to fill Number-# column
        min_mos = [math.inf, math.inf, math.inf, math.inf, math.inf]
        for lc_name, lc in self.bolt_results.items():
            bolt_nmbr += 1 # count bolts / loadcases
            #         lc[0   1   2     3   4             5        6       7     8             9        ]
            # lc_name : [FA, FQ, FSA, FPA, MOS_loc_slip, MOS_gap, MOS_y, MOS_u, MOS_loc_pres, gap_check]
            output_str += "|{0:^8d}|{1:^12}|{2:^12.1f}|{3:^12.1f}|{4:^12.1f}|{5:^12.1f}|{6:^12.0%}|{7:^12.0%}|{8:^12.0%}|{9:^12.0%}|"\
                .format(bolt_nmbr, lc_name, lc[0], lc[1], lc[2], lc[3], lc[4], lc[5], lc[6], lc[7])
            if lc[9] is True:
                output_str += "GC\n"
            else:
                output_str += '\n'
            # get mininum margins of safety
            min_mos = [min(min_mos[0], lc[4]), min(min_mos[1], lc[5]), \
                min(min_mos[2], lc[6]), min(min_mos[3], lc[7]), min(min_mos[4], lc[8])]
        output_str += "|-{0:-^72}+{1:-^12}+{2:-^12}+{3:-^12}+{4:-^12}|\n".format("-", "-", "-", "-", "-")
        output_str += "|{0:>73}|{1:^12.0%}|{2:^12.0%}|{3:^12.0%}|{4:^12.0%}|\n".format(\
                "Minimum Margins of Safety: ", min_mos[0], min_mos[1], min_mos[2], min_mos[3])
        output_str += "|-{0:-^72}+{1:-^12}+{2:-^12}+{3:-^12}+{4:-^12}|\n".format("-", "-", "-", "-", "-")
        output_str += "|{0:>73}|{1:^12.0%}|{2:^12}|{3:^12}|{4:^12}|\n".format(\
                "Global Slippage Margin: ", self.MOS_glob_slip, "-", "-", "-")
        output_str += "|-{0:-^72}+{1:-^12}+{2:-^12}+{3:-^12}+{4:-^12}|\n".format("-", "-", "-", "-", "-")
        output_str += "|{0:>73}|{1:^12}|{2:^12}|{3:^12.0%}|{4:^12}|\n".format(\
                "Minimum MoS against Yield under bolt head / first clamp part: ", "-", "-", min_mos[4], "-")
        output_str += "{0:=^127}\n".format('=')
        # return output_str
        return output_str

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

    # get output string
    def _get_output_str(self):
        outp_str = ""
        if self.inp_file.delta_t != 0: # add thermal output str if delta_T is not 0
            outp_str = self._get_input_str() + self._get_global_result_str() +\
                self._get_thermal_result_str() + self._get_bolt_result_str()
        else:
            outp_str = self._get_input_str() + self._get_global_result_str() +\
                self._get_bolt_result_str()
        return outp_str

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
        #print("*** Pressure below bolt head / shim ***")
        #print("sig_y_pres:      {0:.2f} MPa".format(sig_y_pres))
        #print("sig_y_pres_shim: {0:.2f} MPa".format(sig_y_pres_shim))
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
            #print("MOS_pres_1:      {0:.1%} MPa".format(MOS_pres_1))
            #print("MOS_pres_2:      {0:.1%} MPa".format(MOS_pres_2))
            # minimum MOS_pres
            MOS_pres = min(MOS_pres_1, MOS_pres_2)
        else: # without washer
            # minimal area under bolt head
            A_pres = (self.used_bolt.dh**2)*math.pi/4 - \
                (self.inp_file.through_hole_diameter**2)*math.pi/4
            MOS_pres = sig_y_pres / (F_axial/A_pres) - 1
            #print("MOS_pres:        {0:.1%} MPa".format(MOS_pres))
        return MOS_pres

    # set T_scatter
    def _set_T_scatter(self):
        # use %-value or direct input of tightening-device-torque-tolerance
        if self.inp_file.torque_tol_tight_device.find('%')!=-1:
            self.T_scatter = self.inp_file.tight_torque * \
                float(self.inp_file.torque_tol_tight_device.split('%')[0])/100.0
        else:
            self.T_scatter = float(self.inp_file.torque_tol_tight_device)

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

    # clean margins in self.bolt_results --> set >1000% to inf & <1000% to -inf
    def _clean_margins(self):
        #        [0   1   2     3   4             5        6       7     8             9        ]
        # value: [FA, FQ, FSA, FPA, MOS_loc_slip, MOS_gap, MOS_y, MOS_u, MOS_loc_pres, gap_check]
        for key, value in self.bolt_results.items():
            # MOS_loc_slip, MOS_gap, MOS_y, MOS_u, MOS_loc_pres
            for i in [4, 5, 6, 7, 8]:
                if value[i]*100 > 1000:
                    value[i] = math.inf
                elif value[i]*100 < -1000:
                    value[i] = -math.inf
            # global slippage margin
            if self.MOS_glob_slip*100 > 1000:
                self.MOS_glob_slip = math.inf
            elif self.MOS_glob_slip*100 < -1000:
                self.MOS_glob_slip = -math.inf
