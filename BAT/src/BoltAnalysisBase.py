from src.functions.InputFileParser import InputFileParser
from src.functions.MaterialManager import MaterialManager
from src.functions.BoltManager import BoltManager
from pathlib import Path
import math
import logging
from abc import ABC, abstractmethod
from src.functions.exceptions import JointMosTypeError
"""
Bolt analysis BASE-class
ECSS-E-HB-32-23A & VDI2230 nomenclature-mix is used
(conversion is listed in comment for each variable)
"""
class BoltAnalysisBase(ABC):
    def __init__(self, 
                inp_file : InputFileParser,
                materials : MaterialManager,
                bolts : BoltManager):
        # main analysis inputs
        self.inp_file = inp_file
        self.materials = materials
        self.bolts = bolts
        # used bolt and bolt-material for analysis (set by input-file)
        self.used_bolt = bolts.bolts[self.inp_file.bolt]
        self.used_bolt_mat = self.materials.materials[self.inp_file.bolt_material]
        # calculated variables
        self.M_p = 0.0 # prevailing torque (VDI2230:M_ue)
        self.l_K = 0.0 # joint / clamped length (ECSS:L_j)
        #?self.DA = 0.0 # 
        self.A_sub = 0.0 # substitution area of clamped parts
        #?self.Dsub = 0.0 # subst. diameter out of Asub
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
        self.F_V_at = None # preload after tightening [min, max]
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

    # calculate thermal effects on preload (preload loss / increase)
    # preload change in bolt: clamped parts - bolts (convention)
    # sign-convention: minus (-) is loss in preload
    # if alpha_c > alpha_b : FT_res (+)
    # if alpha_c < alpha_b : FT_res (-)
    def _calc_thermal_loss(self):
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

    # VDI method for thermal preload loss (Young's Modulus variation taken into account)
    # VDI2230 nomenclature used
    def _calc_thermal_loss_VDI(self, F_VRT_min, F_VRT_max):
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
        E_PRT = self.cP*self.lk/self.A_sub # E_overall_mean of clamped parts at RT
        E_PT = cPT*self.lk/self.A_sub
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
        alpha_PRT = d_l_P/(self.inp_file.delta_t*self.lk)
        alpha_PT = d_l_P_T/(self.inp_file.delta_t*self.lk)
        self.alpha_c_th = [alpha_PRT, alpha_PT] # CTE clamped parts @RT and @T
        # calculate preload loss with E taken into account
        # reduction of preload (alpha_ST and alpha_PT used acc. to VDI2230)
        # sign (-) is loss in preload
        dS = 1./self.cB # compliance of bolt
        dP = 1./self.cP # compliance of clamped parts
        denom = dS*E_SRT/E_ST + dP*E_PRT/E_PT # denominator
        # multiply d_F_th with (-1) to get correct sign convention
        dF_th_min = (F_VRT_min * (1 - (dS+dP)/denom) \
            + self.lk*(alpha_ST - alpha_PT)*self.inp_file.delta_t/denom)*(-1)
        dF_th_max = (F_VRT_max * (1 - (dS+dP)/denom) \
            + self.lk*(alpha_ST - alpha_PT)*self.inp_file.delta_t/denom)*(-1)
        self.dF_V_th = [dF_th_min, dF_th_max]

    # calculate joint results 
    def _calc_joint_results(self):
        # check if prevailing torque is defined (e.g. helicoils used)
        # prevailing torque if locking mechanism defined
        if self.inp_file.locking_mechanism == "yes":
            self.M_p = self.inp_file.prevailing_torque
        # COF_BOLT = [mu_head_max, mu_thread_max, mu_head_min, mu_thread_min] 
        mu_uhmax = self.inp_file.cof_bolt[0]
        mu_thmax = self.inp_file.cof_bolt[1]
        mu_uhmin = self.inp_file.cof_bolt[2]
        mu_thmin = self.inp_file.cof_bolt[3]
        # NOTE: friction angle valid ONLY for 60deg threads!! (metric + unified threads)
        rho_max = math.atan(mu_thmax/math.cos(30.*math.pi/180.))
        rho_min = math.atan(mu_thmin/math.cos(30.*math.pi/180.))
        # effective diameter of friction moment under bolt head
        # VDI2230 D_Km; ECSS d_uh [5.4.6]
        D_Km = (self.inp_file.through_hole_diameter+self.used_bolt.dh)/2
        # min / max joint coefficient (with CoF-min and max)
        Kmax = self.used_bolt.d2/2*math.tan(self.used_bolt.slope+rho_max) +\
            mu_uhmax*D_Km/(2*math.sin(self.used_bolt.lbd*math.pi/180/2))
        Kmin = self.used_bolt.d2/2*math.tan(self.used_bolt.slope+rho_min) +\
            mu_uhmin*D_Km/(2*math.sin(self.used_bolt.lbd*math.pi/180/2))
        # calculate bolt preload for tightening torque
        TA = self.inp_file.tight_torque
        Tscatter = self.inp_file.torque_tol_tight_device
        TAmin = TA - Tscatter
        TAmax = TA + Tscatter
        # min / max init. preload after tightening (*1000 to get N)
        # includes prevailing-torque
        # F_V_at: preload after tightening [min, max]
        self.F_V_at = [(TAmin-self.M_p)/Kmax*1000, (TAmax-self.M_p)/Kmin*1000]
        # calculate tightening factor (preload scatter incl. friction and tight. dev. tolerance)
        self.alpha_A = self.F_V_at[1]/self.F_V_at[0]
        # check if VDI thermal method is used
        if self.inp_file.temp_use_vdi_method == "yes":
            # [FPreMin, FPreMax]
            self.dF_V_th = self._calc_thermal_loss_VDI(self.F_V_at[0], self.F_V_at[1])
        # service preload with embedding and thermal loss (ECSS ch. 6.3.2.2)
        self.F_V = [self.F_V_at[0] + self.F_Z + self.dF_V_th[0], self.F_V_at[1] + self.dF_V_th[1]]
        # mean preload in the complete joint (incl. all bolts)
        sum_F_V_mean = self.nmbr_of_bolts*(self.F_V[0]+self.F_V[1])/2
        #
        # Calculate stresses
        #
        # max. torsional stress after tightening
        Wp = (self.used_bolt.ds**3)*math.pi/16 #  polar section modulus
        # NOTE: only applicable for metric threads
        # ECSS Equ. [6.5.3] without thermal term
        MG_max = TAmax*1000 - self.F_V_at[1]*mu_uhmin*D_Km/math.sin(self.used_bolt.lbd*math.pi/180/2)/2
        MG_min = TAmin*1000 - self.F_V_at[0]*mu_uhmax*D_Km/math.sin(self.used_bolt.lbd*math.pi/180/2)/2
        self.tau = [MG_min/Wp, MG_max/Wp] # [min, max] torsional stress aft. tightening
        # max. normal stress after tightening [min, max]
        self.sig_n = [self.F_V_at[0]/self.used_bolt.As, self.F_V_at[1]/self.used_bolt.As]
        # von-Mises equivalent stress in bolt after tightening [min, max]
        self.sig_v = [math.sqrt(self.sig_n[0]**2 + 3*(self.tau[0])**2), \
                    math.sqrt(self.sig_n[1]**2 + 3*(self.tau[1])**2)]
        # degree of utilization (utilization of the minimum yield point)
        self.nue = [self.sig_v[0]/self.used_bolt_mat.sig_y, \
            self.sig_v[1]/self.used_bolt_mat.sig_y]
        #
        # calculate yield MOS under bolt head / first clamped part after tightening
        self.MOS_pres = self._mos_pres(self.F_V_at[1])
        #
        # perform calculation for all bolts / loadcases
        #
        sum_FPA = 0.0
        sum_FQ = 0.0
        for bi in self.inp_file.bolt_loads:
            # bi : ['Bolt-ID', FN, FQ1, FQ2]
            FA = bi[1] # axial bolt force
            FQ = math.sqrt(bi[2]**2+bi[3]**2) # shear bolt force
            FPA = FA*(1-self.Phi_n) # reduction in clamping force
            FSA = FA*self.Phi_n # additional bolt force
            # required clamping force for friction grip per bolt
            FKreq = FQ/(self.inp_file.nmbr_shear_planes*self.inp_file.cof_clamp)
            # calc sums for global slippage margin
            sum_FPA += FPA
            sum_FQ += FQ
            #
            # calculate local slippage margin
            if FKreq==0:
                MOS_loc_slip = math.inf # set to "inf" if no shear load defined
            else:
                if self.inp_file.joint_mos_type.casefold() == "min":
                    MOS_loc_slip = (self.F_V[0]-FPA)/(FKreq*self.inp_file.fos_slip)-1
                elif self.inp_file.joint_mos_type.casefold() == "mean":
                    MOS_loc_slip = ((self.F_V[0]+self.F_V[1])*0.5-FPA)/(FKreq*\
                        self.inp_file.fos_slip)-1
                else:
                    MOS_loc_slip = -999
                    err_str = "Wrong *JOINT_MOS_TYPE defined in input file"
                    logging.error(err_str)
                    raise JointMosTypeError(err_str)
            # local gapping margin
            if self.inp_file.joint_mos_type.casefold() == "min":
                MOS_gap = self.F_V[0]/(self.inp_file.fos_gap*FPA)-1
            elif self.inp_file.joint_mos_type.casefold() == "mean":
                MOS_gap = (self.F_V[0]+self.F_V[1])*0.5/(self.inp_file.fos_gap*FPA)-1
            else:
                MOS_gap = -999
                err_str = "Wrong *JOINT_MOS_TYPE defined in input file"
                logging.error(err_str)
                raise JointMosTypeError(err_str)
            # bolt margin
            # if VDI thermal method used, use temp. dependent sig_y and sig_u for MOS evaluation
            if self.inp_file.temp_use_vdi_method.casefold() == "yes":
                bolt_sig_y = self.materials.materials[self.inp_file.temp_bolt_material].sig_y
                bolt_sig_u = self.materials.materials[self.inp_file.temp_bolt_material].sig_u
                log_str = "Temperature dependent yield and ultimate bolt strength used for MOS"
                print(log_str)
                logging.info(log_str)
            else:
                bolt_sig_y = self.materials.materials[self.inp_file.bolt_material].sig_y
                bolt_sig_u = self.materials.materials[self.inp_file.bolt_material].sig_u
            # yield bolt margin (with 50% shear stress relaxation)
            MOS_y = bolt_sig_y/math.sqrt( ((self.F_V[1]+\
                FSA*self.inp_file.fos_y)/self.used_bolt.As)**2 +\
                    3*(0.5*self.tau[1])**2 )-1
            # ultimate bolt margin (with 50% shear stress relaxation)
            MOS_u = bolt_sig_u/math.sqrt( ((self.F_V[1]+\
                FSA*self.inp_file.fos_u)/self.used_bolt.As)**2 +\
                    3*(0.5*self.tau[1])**2 )-1
            # yield margin for pressure under bolt head
            MOS_loc_pres = self._mos_pres(self.F_V[1]+FSA*self.inp_file.fos_y,\
                self.inp_file.temp_use_vdi_method)
            # save data for each bolt/loadcase to result dict
            # lc_name : [FA, FQ, FSA, FPA, MOS_loc_slip, MOS_gap, MOS_y, MOS_u, MOS_loc_pres]
            self.bolt_results.update({bi[0] : [FA, FQ, FSA, FPA, MOS_loc_slip, MOS_gap,\
                MOS_y, MOS_u, MOS_loc_pres]})
        # calculate global slippage margin
        # total lateral joint force which can be transmitted via friction
        F_tot_lat = (sum_F_V_mean-sum_FPA)*self.inp_file.cof_clamp*self.inp_file.nmbr_shear_planes
        self.MOS_glob_slip = F_tot_lat/(sum_FQ*self.inp_file.fos_slip)-1

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

    # get analysis input (file) string for printout
    def _get_input_str(self):
        output_str = "" # use output_str for print() or print-to-file
        output_str += "{0:=^95}\n".format('=') # global splitter
        output_str += "| {0:^91} |\n".format("BAT Bolt Analysis Input")
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
        output_str += "| {0:<50} {1:^20.2f} {2:^20}|\n".format(\
            "Torque tolerance of tight. device [Nm]:", self.inp_file.torque_tol_tight_device, "")
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
            "Edge dist. of the flanges [mm]:", self.inp_file.egde_dist_flange, "")
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
        output_str += "| {0:^91} |\n".format("ESA PSS-03-208 Issue 1 ANALYSIS RESULTS")
        output_str += "{0:=^95}\n".format('=')
        output_str += "| {0:<50} {1:^20.1f} {2:^20}|\n".format(\
            "Tightening torque with prevailing torque [Nm]:", self.inp_file.tight_torque, "")
        output_str += "| {0:<50} {1:^20.1f} {2:^20}|\n".format(\
            "Prevailing torque [Nm]:", self.Tp, "")
        output_str += "| {0:<50} {1:^20.1f} {2:^20}|\n".format(\
            "Tightening torque w/o prevailing torque [Nm]:", \
                self.inp_file.tight_torque-self.Tp, "")
        output_str += "|{0:-^93}|\n".format('-') # empty line within section
        output_str += "| {0:<50} {1:^20.2f} {2:^20}|\n".format(\
            "Clamped length lk [mm]:", self.lk, "")
        output_str += "| {0:<50} {1:^20.2f} {2:^20}|\n".format(\
            "Subst. outside diameter DA [mm]:", self.DA, "")
        output_str += "| {0:<50} {1:^20.2f} {2:^20}|\n".format(\
            "Subst. area of cP Asub [mm^2]:", self.Asub, "")
        output_str += "| {0:<50} {1:^20.2f} {2:^20}|\n".format(\
            "Subst. diameter of cP Dsub [mm]:", self.Dsub, "")
        output_str += "| {0:<50} {1:^20.4g} {2:^20}|\n".format(\
            "Bolt stiffness cB [N/mm]:", self.cB, "")
        output_str += "| {0:<50} {1:^20.4g} {2:^20}|\n".format(\
            "Clamped part stiffness cP [N/mm]:", self.cP, "")
        output_str += "| {0:<50} {1:^20.4f} {2:^20}|\n".format(\
            "Load factor Phi_K [-]:", self.phi_K, "")
        output_str += "| {0:<50} {1:^20.4f} {2:^20}|\n".format(\
            "Load factor Phi_n [-]:", self.phi_n, "")
        output_str += "| {0:<50} {1:^20d} {2:^20}|\n".format(\
            "Number of interfaces for embedding [-]:", self.nmbr_interf, "")
        output_str += "| {0:<50} {1:^20.2f} {2:^20}|\n".format(\
            "Embedding [micron]:", self.emb_micron, "")
        output_str += "| {0:<50} {1:^20.1f} {2:^20}|\n".format(\
            "Preload loss due embedding FZ [N]:", self.FZ, "")
        # if VDI method used
        if self.inp_file.temp_use_vdi_method == "yes":
            output_str += "| Preload loss due to thermal effects {0:^56}|\n".format(" ")
            output_str += "| {0:<50} {1:>14.1f} / {2:<24.1f}|\n".format(\
                "  based on FVmin / FVmax [N] (VDI method):",\
                    self.FT[0], self.FT[1])
        else:
            output_str += "| {0:<50} {1:^20.1f} {2:^20}|\n".format(\
                "Preload loss due thermal effects FT [N]:", self.FT[0], "")
        # min / max table
        output_str += "{0:=^95}\n".format('=') # global splitter
        output_str += "| {0:^50}|{1:^20}|{2:^20}|\n".format("", "MIN (mu_max)", "MAX (mu_min)")
        output_str += "{0:=^95}\n".format('=')
        output_str += "| {0:<50}|{1:^20.3f}|{2:^20.3f}|\n".format(\
            "Coefficient of friction under bolt head:", self.inp_file.cof_bolt[2],\
                self.inp_file.cof_bolt[0])
        output_str += "| {0:<50}|{1:^20.3f}|{2:^20.3f}|\n".format(\
            "Coefficient of friction in thread:", self.inp_file.cof_bolt[3],\
                self.inp_file.cof_bolt[1])
        output_str += "| {0:<50}|{1:^41.2f}|\n".format(\
            "Coefficient of friction between clamped parts:", self.inp_file.cof_clamp)
        output_str += "|-{0:-^50}+{1:-^20}+{2:-^20}|\n".format("-", "-", "-") # empty line in table
        output_str += "| {0:<50}|{1:^20.1f}|{2:^20.1f}|\n".format(\
            "Bolt preload after tightening [N]:", self.FPreMin, self.FPreMax)
        output_str += "| {0:<50}|{1:^41.1f}|\n".format(\
            "MEAN Bolt preload after tightening [N]:", self.FPreMean)
        output_str += "| {0:<50}|{1:>19.2f} / \u00B1{2:<18.1%}|\n".format(\
            "Preload Scatter / Tightening Factor Alpha_A [-]:",\
                self.alpha_A, (self.alpha_A-1)/(self.alpha_A+1))
        # if VDI method is used
        if self.inp_file.temp_use_vdi_method == "yes":
            output_str += "| {0:<50}|{1:^20.1f}|{2:^20.1f}|\n".format(\
                "Total preload loss incl. emb. & temp. [N]:", self.FT[0]+self.FZ, self.FT[1]+self.FZ)
        else:
            output_str += "| {0:<50}|{1:^41.1f}|\n".format(\
                "Total preload loss incl. emb. & temp. [N]:", self.FT[0]+self.FZ)
        output_str += "| {0:<50}|{1:^20.1f}|{2:^20.1f}|\n".format(\
            "Bolt preload at service incl. emb. & temp. [N]:", self.FPreMinServ, self.FPreMaxServ)
        output_str += "| {0:<50}|{1:^41.1f}|\n".format(\
            "MEAN Bolt preload at serv. incl. emb. & temp. [N]:", self.FPreMeanServ)
        output_str += "|-{0:-^50}+{1:-^20}+{2:-^20}|\n".format("-", "-", "-")
        output_str += "| {0:<50}|{1:^20.1f}|{2:^20.1f}|\n".format(\
            "Torsional stress after tightening [MPa]:", self.tau_min, self.tau_max)
        output_str += "| {0:<50}|{1:^20.1f}|{2:^20.1f}|\n".format(\
            "Normal stress after tightening [MPa]:", self.sig_n_min, self.sig_n_max)
        output_str += "| {0:<50}|{1:^20.1f}|{2:^20.1f}|\n".format(\
            "Von-Mises equiv. stress aft. tightening [MPa]:", self.sig_v_min, self.sig_v_max)
        output_str += "| {0:<50}|{1:^20.1%}|{2:^20.1%}|\n".format(\
            "Bolt utilization [%]:", self.nue_min, self.nue_max)
        output_str += "|-{0:-^50}+{1:-^20}+{2:-^20}|\n".format("-", "-", "-")
        output_str += "| {0:<50}|{1:^20}|{2:^20.0%}|\n".format(\
            "Min. MoS (yield) under bolt head / washer [%]:", "-", self.MOS_pres)
        output_str += "{0:=^95}\n".format('=')
        # return output_str
        return output_str

    # print analysis results per bolt/loadcase
    def _get_bolt_result_str(self):
        output_str = "" # use output_str for print() or print-to-file
        # define header
        output_str += "{0:=^127}\n".format('=')
        # lc_name : [FA, FQ, FSA, FPA, MOS_loc_slip, MOS_gap, MOS_y, MOS_u, MOS_loc_pres]
        output_str += "|{0:^8}|{1:^12}|{2:^12}|{3:^12}|{4:^12}|{5:^12}|{6:^12}|{7:^12}|{8:^12}|{9:^12}|\n"\
            .format("Number", "Bolt /", "Axial Bolt", "Shear Bolt", "Add. Bolt", "Red. Clmp.", \
            "Slippage", "Gapping", "Yield", "Ultimate")
        output_str += "|{0:^8}|{1:^12}|{2:^12}|{3:^12}|{4:^12}|{5:^12}|{6:^12}|{7:^12}|{8:^12}|{9:^12}|\n"\
            .format("#", "Loadcase", "Force", "Force", "Force", "Force", "MoS", "MoS", "MoS", "MoS")
        output_str += "|{0:^8}|{1:^12}|{2:^12}|{3:^12}|{4:^12}|{5:^12}|{6:^12}|{7:^12}|{8:^12}|{9:^12}|\n"\
            .format("", "", "FA [N]", "FQ [N]", "FSA [N]", "FPA [N]", "FoS="+str(self.inp_file.fos_slip),\
            "FoS="+str(self.inp_file.fos_gap), "FoS="+str(self.inp_file.fos_y), "FoS="+str(self.inp_file.fos_u))
        output_str += "{0:=^127}\n".format('=')
        # loop through bolts / loadcases
        bolt_nmbr = 0 # to fill Number-# column
        min_mos = [math.inf, math.inf, math.inf, math.inf, math.inf]
        for lc_name, lc in self.bolt_results.items():
            bolt_nmbr += 1 # count bolts / loadcases
            #         lc[0   1   2     3   4             5        6       7     8           ]
            # lc_name : [FA, FQ, FSA, FPA, MOS_loc_slip, MOS_gap, MOS_y, MOS_u, MOS_loc_pres]
            output_str += "|{0:^8d}|{1:^12}|{2:^12.1f}|{3:^12.1f}|{4:^12.1f}|{5:^12.1f}|{6:^12.0%}|{7:^12.0%}|{8:^12.0%}|{9:^12.0%}|\n"\
                .format(bolt_nmbr, lc_name, lc[0], lc[1], lc[2], lc[3], lc[4], lc[5], lc[6], lc[7])
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

    # print results to terminal and/or file
    def print_results(self, output_file=None, print_to_cmd=True):
        if print_to_cmd is True:
            print() # print empty line
            # print BAT input
            print(self._get_input_str())
            # print results to terminal
            print(self._get_global_result_str())
            if self.inp_file.temp_use_vdi_method == "yes":
                print(self.FT_outp_str)
            print(self._get_bolt_result_str())
        # print results to output_file
        if output_file != None:
            output_file = Path(output_file)
            log_str = "Output file written: {0:^}".format(str(output_file.absolute()))
            print(log_str)
            logging.info(log_str)
            # write output file
            with open(output_file, 'w') as fid:
                # wirte BAT input to file
                fid.write(self._get_input_str())
                # write global results to file
                fid.write(self._get_global_result_str())
                # if VDI method used write to file
                if self.inp_file.temp_use_vdi_method == "yes":
                    fid.write(self.FT_outp_str)
                # write bolts results to file
                fid.write(self._get_bolt_result_str())
                # write timestamp to output file
                fid.write("BAT Analysis Timestamp: {0:^}\n".format(\
                    str(datetime.now().strftime("%d-%m-%Y %H:%M:%S"))))
        # return string
        return self._get_input_str() + self._get_global_result_str() + self._get_bolt_result_str()

