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
        self.ana_method = "ESA PSS-03-208 Issue 1 ANALYSIS RESULTS"
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
        TAmin = self.inp_file.tight_torque - self.T_scatter
        TAmax = self.inp_file.tight_torque + self.T_scatter
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
        # analyze gapping limit (force where gapping occurs)
        FA_gap_limit = [self.F_V[0]/(1-self.Phi_n), self.F_V[1]/(1-self.Phi_n)] # [min, max]
        FSA_at_gap_limit = [FA_gap_limit[0]*self.Phi_n, FA_gap_limit[1]*self.Phi_n] # additional bolt force at gapping limit
        print("*** Gapping Summary ***")
        print("FA_gap_limit  [N]: {0:.1f} / {1:.1f}".format(FA_gap_limit[0], FA_gap_limit[1]))
        print("FSA_at_gap_limit [N]: {0:.1f} / {1:.1f}".format(FSA_at_gap_limit[0], FSA_at_gap_limit[1]))
        #
        # perform calculation for all bolts / loadcases
        sum_FPA = 0.0 # for global slippage margin
        sum_FQ1 = 0.0 # sum up each FQ component for
        sum_FQ2 = 0.0 # global slippage margin evaluation
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
            sum_FQ1 += bi[2]*ffit
            sum_FQ2 += bi[3]*ffit
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
            if FA <= 0.0:
                MOS_gap = math.inf # set to "inf" if no or negative axial force
            else:
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
            #
            # check if gapping is present (only check max-gap-limit --> always limiting factor)
            if FA > FA_gap_limit[1]:
                FSA_gap_corr = FSA_at_gap_limit[1]+(FA-FA_gap_limit[1]) # gapping
                print("{0:^} -> MOS_y_gapCorr_max used at {1:.1f}N".format(bi[0], \
                    self.F_V[1]+FSA_at_gap_limit[1]+(FA-FA_gap_limit[1])))
                gap_check = True
            else:
                FSA_gap_corr = FSA # NOT gapping
                gap_check = False
            #
            # yield bolt margin (with 50% tau relaxation; see VDI2230 ch. 5.5.2.1)
            MOS_y = bolt_sig_y/math.sqrt( ((self.F_V[1]+\
                FSA_gap_corr*self.inp_file.fos_y)/self.used_bolt.As)**2 +\
                    3*(0.5*self.tau[1])**2 )-1
            #
            # ultimate bolt margin (with 50% tau relaxation; see VDI2230 ch. 5.5.2.1)
            MOS_u = bolt_sig_u/math.sqrt( ((self.F_V[1]+\
                FSA_gap_corr*self.inp_file.fos_u)/self.used_bolt.As)**2 +\
                    3*(0.5*self.tau[1])**2 )-1
            #
            # yield margin for pressure under bolt head
            MOS_loc_pres = self._mos_pres(self.F_V[1]+FSA_gap_corr*self.inp_file.fos_y,\
                self.inp_file.temp_use_vdi_method)
            # save data for each bolt/loadcase to result dict
            # lc_name : [FA, FQ, FSA, FPA, MOS_loc_slip, MOS_gap, MOS_y, MOS_u, MOS_loc_pres]
            self.bolt_results.update({bi[0] : [FA, FQ, FSA, FPA, MOS_loc_slip, MOS_gap,\
                MOS_y, MOS_u, MOS_loc_pres, gap_check]})
        # calculate global slippage margin
        # total lateral joint force which can be transmitted via friction
        F_tot_lat = (sum_F_V_mean-sum_FPA)*self.inp_file.cof_clamp*self.inp_file.nmbr_shear_planes
        # global slippage margin
        sum_FQ = math.sqrt(sum_FQ1**2 + sum_FQ2**2)
        if sum_FQ != 0.0:
            self.MOS_glob_slip = F_tot_lat/(sum_FQ*self.inp_file.fos_slip)-1
        else:
            self.MOS_glob_slip = math.inf
        #
        # finally clean margins in self.bolt_results --> set >1000% to inf & <1000% to -inf
        self._clean_margins()