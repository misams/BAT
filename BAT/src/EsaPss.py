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
class EsaPss(BoltAnalysisBase):
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
        # bolt compliance p.5-15 ESA-PSS
        self.delta_b = 1/self.used_bolt_mat.E*( 0.4*self.used_bolt.d/self.used_bolt.A1 +\
            self.l_K/self.used_bolt.A3 + 0.4*self.used_bolt.d/self.used_bolt.A3)
        #
        # Joint elastic compliance for joints with large areas of contact, p.6-7ff.
        # calc substitutional area for clamped parts
        if self.l_K/self.used_bolt.d >= 1.0 and self.l_K/self.used_bolt.d <=2:
            logging.info("Calculate Asub acc. to case (ii)")
            # NOTE: if *SUBST_DA=0.0 use rule of thumb for DA estimation, p.6-11
            if self.inp_file.subst_da != 0.0:
                DA = self.inp_file.subst_da
                logging.info("Substitutional diameter DA set: {0:.2f}".format(DA))
            else:
                DA = self.used_bolt.dh*(2.+3.)/2. # mean value betw. range 2-3 used, p.6-11
                logging.info("Mean substitutional diameter DA set (rule of thumb): {0:.2f}".format(DA))
            # calc subst. area for clamped parts
            self.A_sub = math.pi/4*( self.used_bolt.dh**2-self.inp_file.through_hole_diameter**2 ) +\
                math.pi/8*( DA/self.used_bolt.dh-1 ) *\
                ( self.used_bolt.dh*self.l_K/5+(self.l_K**2)/100 )
        elif self.l_K/self.used_bolt.d > 2.0:
            logging.info("Calculate Asub acc. to case (iii)")
            self.A_sub = math.pi/4*((self.used_bolt.dh+self.l_K/10)**2 - \
                self.inp_file.through_hole_diameter**2)
        else:
            self.A_sub = math.pi/4*(self.used_bolt.dh**2 - self.inp_file.through_hole_diameter**2)
            warn_str = "WARNING: Asub acc. to case (i). DA == dK --> use with caution!"
            print(warn_str)
            logging.warning(warn_str)
        #
        # calculate clamped part compliance
        self.delta_c = 0.0
        for _, c in self.inp_file.clamped_parts.items():
            self.delta_c += c[1]/(self.A_sub*self.materials.materials[c[0]].E)
        #
        # force ratio
        self.Phi = self.delta_c/(self.delta_b+self.delta_c)
        self.Phi_n = self.inp_file.loading_plane_factor*self.Phi

    # @Override: calculate embedding preload loss
    def _calc_embedding(self):
        # calculate number of interfaces, incl. threads (#cl_parts + 1 + 1xthread)
        nmbr_interf = len(self.inp_file.clamped_parts) + 1
        # Table 18.4, p.18-7
        lkd = self.l_K/self.used_bolt.d # ratio for embedding lookup
        # embedding table 18.4 fitted between ratios 1.0 < ldk < 11.0
        # above and below these values - limit values used
        if nmbr_interf==2 or nmbr_interf==3:
            logging.info("Embedding: 2 to 3 interfaces")
            if lkd < 1.0:
                self.f_Z = self._embedding_2_to_3(1.0)
            elif lkd > 11.0:
                self.f_Z= self._embedding_2_to_3(11.0)
            else:
                self.f_Z= self._embedding_2_to_3(lkd)
        elif nmbr_interf==4 or nmbr_interf==5:
            logging.info("Embedding: 4 to 5 interfaces")
            if lkd < 1.0:
                self.f_Z= self._embedding_4_to_5(1.0)
            elif lkd > 11.0:
                self.f_Z= self._embedding_4_to_5(11.0)
            else:
                self.f_Z= self._embedding_4_to_5(lkd)
        elif nmbr_interf==6 or nmbr_interf==7:
            logging.info("Embedding: 6 to 7 interfaces")
            if lkd < 1.0:
                self.f_Z= self._embedding_6_to_7(1.0)
            elif lkd > 11.0:
                self.f_Z= self._embedding_6_to_7(11.0)
            else:
                self.f_Z= self._embedding_6_to_7(lkd)
        else:
            # number of interfaces too large
            err_str = "Number of interfaces out of tabled range"
            logging.error(err_str)
            raise EmbeddingInterfacesError(err_str)
        # calculate complete embedding in micron = delta_l_Z
        self.f_Z*= nmbr_interf
        # calculate preload loss due to embedding (micron to mm: 1/1000)
        # sigen-convention: minus (-) is loss in preload
        self.F_Z = -self.f_Z*self.Phi*(1/self.delta_c)/1000

    # fitted embedding Table 18.4, p.18-7
    # valid quadratic fit between values: 1.0 < ldk < 11.0
    def _embedding_2_to_3(self, lkd):
        return -0.0133*lkd**2+0.3*lkd+0.8333
    def _embedding_4_to_5(self, lkd):
        return -0.0067*lkd**2+0.15*lkd+0.6667
    def _embedding_6_to_7(self, lkd):
        return -0.0053*lkd**2+0.12*lkd+0.4333

    # @Override: calculate joint results 
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
        # mean diameter of bolt head 
        Dkm = (self.inp_file.through_hole_diameter+self.used_bolt.dh)/2
        # min / max joint coefficient
        Kmax = ( self.used_bolt.d2/2*math.tan(self.used_bolt.slope+rho_max) +\
            mu_uhmax*Dkm/2 )
        Kmin = ( self.used_bolt.d2/2*math.tan(self.used_bolt.slope+rho_min) +\
            mu_uhmin*Dkm/2 )
        # calculate bolt preload for tightening torque
        TA = self.inp_file.tight_torque # tight. torque with prevailing included 
        Tscatter = self.inp_file.torque_tol_tight_device
        TAmin = TA - Tscatter
        TAmax = TA + Tscatter
        # min / max init. preload after tightening (*1000 to get N)
        self.F_M = [(TAmin-self.M_p[1])/Kmax*1000, (TAmax-self.M_p[0])/Kmin*1000]
        # calculate tightening factor (preload scatter incl. friction and tight. dev. tolerance)
        self.alpha_A = self.F_M[1]/self.F_M[0]
        # check if VDI thermal method is used 
        if self.inp_file.temp_use_vdi_method.casefold() == "yes":
            # [FPreMin, FPreMax]
            self._calc_thermal_VDI(self.F_M[0], self.F_M[1])
        # service preload with embedding and thermal loss (ECSS ch. 6.3.2.2)
        self.F_V = [ self.F_M[0] + self.F_Z + self.dF_V_th[0],\
                     self.F_M[1] + self.dF_V_th[1] ]
        # mean preload in the complete joint (incl. all bolts)
        sum_F_V_mean = self.nmbr_of_bolts*(self.F_V[0]+self.F_V[1])/2
        #
        # Calculate stresses
        # max. torsional stress after tightening - see VDI2230 p.24
        Wp = (self.used_bolt.ds**3)*math.pi/16
        # NOTE: only applicable for metric threads
        #MG_max = self.F_M[1]*self.used_bolt.d2/2*(self.used_bolt.p/(self.used_bolt.d2*math.pi)+\
        #    1.155*mu_thmin)
        #MG_min = self.F_M[0]*self.used_bolt.d2/2*(self.used_bolt.p/(self.used_bolt.d2*math.pi)+\
        #    1.155*mu_thmax)
        # ECSS equations used
        MG_max = TAmax*1000 - self.F_M[1]*mu_uhmin*Dkm/math.sin(self.used_bolt.lbd*math.pi/180/2)/2
        MG_min = TAmin*1000 - self.F_M[0]*mu_uhmax*Dkm/math.sin(self.used_bolt.lbd*math.pi/180/2)/2
        self.tau = [MG_min/Wp, MG_max/Wp] # [min, max] torsional stress aft. tightening
        # max. normal stress after tightening
        self.sig_n = [self.F_M[0]/self.used_bolt.As, self.F_M[1]/self.used_bolt.As]
        # von-Mises equivalent stress in bolt
        self.sig_v = [math.sqrt(self.sig_n[0]**2 + 3*(self.tau[0])**2), \
                    math.sqrt(self.sig_n[1]**2 + 3*(self.tau[1])**2)]
        # degree of utilization (utilization of the minimum yield point)
        self.nue = [self.sig_v[0]/self.used_bolt_mat.sig_y,\
                    self.sig_v[1]/self.used_bolt_mat.sig_y]
        #
        # calculate yield MOS under bolt head / first clamped part after tightening
        self.MOS_pres = self._mos_pres(self.F_M[1])
        #
        # perform calculation for all bolts / loadcases
        sum_FPA = 0.0
        sum_FQ = 0.0
        for bi in self.inp_file.bolt_loads:
            ffit = self.inp_file.fos_fit # fitting-factor
            # bi : ['Bolt-ID', FN, FQ1, FQ2] --> bolt forces for each bolt 'bi'
            FA = bi[1]*ffit # axial bolt force
            FQ = math.sqrt((bi[2]*ffit)**2+(bi[3]*ffit)**2) # shear bolt force
            FPA = FA*(1-self.Phi_n) # reduction in clamping force
            FSA = FA*self.Phi_n # additional bolt force
            # required clamping force for friction grip
            FKreq = FQ/(self.inp_file.nmbr_shear_planes*self.inp_file.cof_clamp)
            # calc sums for global slippage margin
            sum_FPA += FPA
            sum_FQ += FQ
            #
            # local slippage margin
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
            # local gapping margin (always with minimal service preload)
            MOS_gap = self.F_V[0]/(self.inp_file.fos_gap*FPA)-1
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
            # yield bolt margin (with 50% tau relaxation; see VDI2230 ch. 5.5.2.1)
            MOS_y = bolt_sig_y/math.sqrt( ((self.F_V[1]+\
                FSA*self.inp_file.fos_y)/self.used_bolt.As)**2 +\
                    3*(0.5*self.tau[1])**2 )-1
            # ultimate bolt margin (with 50% tau relaxation; see VDI2230 ch. 5.5.2.1)
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
        # global slippage margin
        if sum_FQ != 0.0:
            self.MOS_glob_slip = F_tot_lat/(sum_FQ*self.inp_file.fos_slip)-1
        else:
            self.MOS_glob_slip = math.inf

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
            "Fitting-Factor", "FOS_fit:", self.inp_file.fos_fit)
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
        #output_str += "| {0:<50} {1:^20.1f} {2:^20}|\n".format(\
        #    "Tightening torque with prevailing torque [Nm]:", self.inp_file.tight_torque, "")
        #output_str += "| {0:<50} {1:^20.1f} {2:^20}|\n".format(\
        #    "Prevailing torque [Nm]:", self.M_p, "")
        #output_str += "| {0:<50} {1:^20.1f} {2:^20}|\n".format(\
        #    "Tightening torque w/o prevailing torque [Nm]:", \
        #        self.inp_file.tight_torque-self.M_p, "")
        #output_str += "|{0:-^93}|\n".format('-') # empty line within section
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
            "Prevailing torque (max | min) [Nm]:", self.M_p[1], self.M_p[0])
        output_str += "| {0:<50}|{1:^20.1f}|{2:^20.1f}|\n".format(\
            "Tightening torque w/o prevailing torque [Nm]:", self.inp_file.tight_torque-self.M_p[1],\
                self.inp_file.tight_torque-self.M_p[0])
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
