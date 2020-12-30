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
class Ecss(BoltAnalysisBase):
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
            self.l_K += c[1] # add thickness of all clamped parts to l_K
        #
        # compliance of bolt / fastener [7.5.5, p.74]
        if self.inp_file.joint_type == "TBJ":
            L_eng_sub = 0.4*self.used_bolt.d
        else: # TTJ
            L_eng_sub = 0.33*self.used_bolt.d
        # 0.4*d used for head and nut/locking-device; see Table 7-1
        self.delta_b = 1/self.used_bolt_mat.E*( 0.4*self.used_bolt.d/self.used_bolt.A1 +\
            self.l_K/self.used_bolt.A3 + 0.4*self.used_bolt.d/self.used_bolt.A1 +\
            L_eng_sub/self.used_bolt.A3)
        #
        # compliance of clamped parts
        D_avail = self.inp_file.subst_da
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
        #
        # existence of cone and sleeve
        # calculate A_sub (substitution are of clamped parts compliance)
        # delta_c = l_K/(E_c * A_sub) ...compliance equation
        if D_avail > D_lim:
            print("CASE 1: fully developed into a cone")
            print("D_avail > D_lim : {0:.2f} > {1:.2f}".format(D_avail,D_lim))
            tmp_log_D = ((self.used_bolt.dh+self.used_bolt.d)*(D_lim-self.used_bolt.d)) \
                      / ((self.used_bolt.dh-self.used_bolt.d)*(D_lim+self.used_bolt.d))
            # Equ. [7.6.10]
            x_c = 2*math.log(tmp_log_D)/(w*math.pi*self.used_bolt.d*tan_phi) # x_c = l_K/A_sub
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
        for _, c in self.inp_file.clamped_parts.items():
            self.delta_c += c[1]/(self.A_sub*self.materials.materials[c[0]].E)
        # calculate force ratio
        self.Phi = self.delta_c/(self.delta_b+self.delta_c)
        self.Phi_n = self.inp_file.loading_plane_factor*self.Phi

    # @Override: calculate embedding preload loss
    def _calc_embedding(self):
        # if 5%-option NOT used calculate embedding acc. to Table 6-3
        if self.inp_file.emb_rz != "5%":
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
            # calculate number of embedding interfaces (micron to mm: 1/1000)
            # 1 x thread
            # TBJ: 2 x under-head interface / TTJ: 1 x under-head interface
            # TBJ: #CP-1 / TTJ: #CP
            if self.inp_file.joint_type == "TBJ":
                self.f_Z = f_Z_i[0] + 2*f_Z_i[1] + (len(self.inp_file.clamped_parts)-1)*f_Z_i[2]
            else: # TTJ
                self.f_Z = f_Z_i[0] + 1*f_Z_i[1] + len(self.inp_file.clamped_parts)*f_Z_i[2]
            #
            # calculate embedding force
            # sigen-convention: minus (-) is loss in preload
            self.F_Z = -self.f_Z/1000/(self.delta_b+self.delta_c)

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
        # effective diameter of friction moment under bolt head
        # VDI2230 D_Km; ECSS d_uh [5.4.6]
        D_Km = (self.inp_file.through_hole_diameter+self.used_bolt.dh)/2
        # min / max joint coefficient (with CoF-min and max)
        Kmax = self.used_bolt.d2/2*(math.tan(self.used_bolt.slope)+\
            math.tan(rho_max)) + mu_uhmax*D_Km/(2*math.sin(self.used_bolt.lbd*math.pi/180/2))
        Kmin = self.used_bolt.d2/2*(math.tan(self.used_bolt.slope)+\
            math.tan(rho_min)) + mu_uhmin*D_Km/(2*math.sin(self.used_bolt.lbd*math.pi/180/2))
        # calculate bolt preload for tightening torque
        TA = self.inp_file.tight_torque # tight. torque with prevailing included
        Tscatter = self.inp_file.torque_tol_tight_device
        TAmin = TA - Tscatter
        TAmax = TA + Tscatter
        # min / max init. preload after tightening (*1000 to get N)
        # includes prevailing-torque
        # F_M: preload after tightening [min, max]; equ.6.3.14 / 6.3.15
        self.F_M = [(TAmin-self.M_p)/Kmax*1000, (TAmax-self.M_p)/Kmin*1000]
        # calculate tightening factor (preload scatter incl. friction and tight. dev. tolerance)
        self.alpha_A = self.F_M[1]/self.F_M[0]
        # check if VDI thermal method is used
        if self.inp_file.temp_use_vdi_method.casefold() == "yes":
            # [FPreMin, FPreMax]
            self._calc_thermal_VDI(self.F_M[0], self.F_M[1])
        # check if 5%-embedding used
        if self.inp_file.emb_rz == "5%":
            self.F_Z = -0.05*self.F_M[1] # 5% of F_M_max used for F_Z
            self.f_Z = -self.F_Z*(self.delta_b+self.delta_c)*1000 # in micron
            print("5%-embedding used: {0:.1f} N".format(self.F_Z))
        # service preload with embedding and thermal loss (ECSS ch. 6.3.2.2)
        # see equ.6.3.14 / 6.3.15
        self.F_V = [ self.F_M[0] + self.F_Z + self.dF_V_th[0],\
                     self.F_M[1] + self.dF_V_th[1] ]
        # mean preload in the complete joint (incl. all bolts)
        sum_F_V_mean = self.nmbr_of_bolts*(self.F_V[0]+self.F_V[1])/2
        #
        # Calculate stresses
        #
        # max. torsional stress after tightening
        Wp = (self.used_bolt.ds**3)*math.pi/16 #  polar section modulus
        # NOTE: only applicable for metric threads
        # ECSS Equ. [6.5.3] without thermal term (not thermal load during preloading)
        # equ.[6.3.4 & 6.5.2] used
        MG_max = TAmax*1000 - self.F_M[1]*mu_uhmin*D_Km/math.sin(self.used_bolt.lbd*math.pi/180/2)/2
        MG_min = TAmin*1000 - self.F_M[0]*mu_uhmax*D_Km/math.sin(self.used_bolt.lbd*math.pi/180/2)/2
        self.tau = [MG_min/Wp, MG_max/Wp] # [min, max] torsional stress aft. tightening
        # max. normal stress after tightening [min, max]
        self.sig_n = [self.F_M[0]/self.used_bolt.As, self.F_M[1]/self.used_bolt.As]
        # von-Mises equivalent stress in bolt after tightening [min, max]
        self.sig_v = [math.sqrt(self.sig_n[0]**2 + 3*(self.tau[0])**2), \
                    math.sqrt(self.sig_n[1]**2 + 3*(self.tau[1])**2)]
        # degree of utilization (utilization of the minimum yield point)
        self.nue = [self.sig_v[0]/self.used_bolt_mat.sig_y, \
            self.sig_v[1]/self.used_bolt_mat.sig_y]
        #
        # calculate yield MOS under bolt head / first clamped part after tightening
        self.MOS_pres = self._mos_pres(self.F_M[1])
        #
        # perform calculation for all bolts / loadcases
        #
        sum_FPA = 0.0
        sum_FQ = 0.0
        for bi in self.inp_file.bolt_loads:
            ffit = self.inp_file.fos_fit # fitting-factor
            # bi : ['Bolt-ID', FN, FQ1, FQ2] --> bolt forces for each bolt 'bi'
            FA = bi[1]*ffit # axial bolt force
            FQ = math.sqrt((bi[2]*ffit)**2+(bi[3]*ffit)**2) # shear bolt force
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
            # local gapping margin (always with minimal service preload)
            MOS_gap = self.F_V[0]/(self.inp_file.fos_gap*FPA)-1
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
        output_str += "| {0:^91} |\n".format("ECSS-E-HB-32-23A, 16.04.2010 ANALYSIS RESULTS")
        output_str += "{0:=^95}\n".format('=')
        output_str += "| {0:<50} {1:^20.1f} {2:^20}|\n".format(\
            "Tightening torque with prevailing torque [Nm]:", self.inp_file.tight_torque, "")
        output_str += "| {0:<50} {1:^20.1f} {2:^20}|\n".format(\
            "Prevailing torque [Nm]:", self.M_p, "")
        output_str += "| {0:<50} {1:^20.1f} {2:^20}|\n".format(\
            "Tightening torque w/o prevailing torque [Nm]:", \
                self.inp_file.tight_torque-self.M_p, "")
        output_str += "|{0:-^93}|\n".format('-') # empty line within section
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
