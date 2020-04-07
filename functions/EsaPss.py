from functions.InputFileParser import InputFileParser
from functions.MaterialManager import MaterialManager
from functions.BoltManager import BoltManager
from functions.exceptions import EmbeddingInterfacesError
from pathlib import Path
import math
import logging
from datetime import datetime
"""
Bolt analysis according to ESA PSS-03-208 Issue 1, December 1989
Guidelines for threaded fasteners, european space agency

Concentric axially loaded joints (slightly modified and adopted)
"""
class EsaPss:
    def __init__(self, inp_file : InputFileParser, materials : MaterialManager, bolts : BoltManager):
        # logging
        log_str = "ESA PSS-03-208 Issue 1 (December 1989) analysis executed."
        print(log_str)
        logging.info(log_str)
        # EsaPss inputs
        self.inp_file = inp_file
        self.materials = materials
        self.bolts = bolts
        # used variables for analysis
        self.used_bolt = bolts.bolts[self.inp_file.bolt_size] # used bolt
        self.used_bolt_mat = self.materials.materials[self.inp_file.bolt_material]
        # if washer used --> add washer to clamped parts
        if self.inp_file.use_shim != "no":
            self.inp_file.clamped_parts.update( \
                {0 : (self.inp_file.use_shim[0], self.bolts.washers[self.inp_file.use_shim[1]].h) })
            log_str = "Shim added to clamped materials --> {0:^}".format(str(self.inp_file.clamped_parts[0]))
            print(log_str)
            logging.info(log_str)
        else:
            log_str = "No shim used."
            print(log_str)
            logging.info(log_str)
        # calculated variables
        self.Tp = 0.0 # prevailing torque
        self.lk = 0.0 # clamped length
        self.DA = 0.0 # 
        self.Asub = 0.0 # substitution area of clamped parts
        self.Dsub = 0.0 # subst. diameter out of Asub
        self.cB = 0.0 # bolt stiffness
        self.cP = 0.0 # clamped part striffness
        self.phi_K = 0.0 # load factor
        self.phi_n = 0.0
        self.nmbr_interf = 0 # number of interfaces for embedding
        self.emb_micron = 0.0 # delta_l_Z of embedding
        self.FZ = 0.0 # preload loss due to embedding
        self.FT = None # preload loss due to CTE missmatch [FT_min, FT_max]
        self.FT_outp_str = "" # only used for VDI method
        self.nmbr_of_bolts = len(self.inp_file.bolt_loads)
        self.FPreMin = 0.0 # preload after tightening
        self.FPreMax = 0.0
        self.FPreMean = 0.0
        self.FPreMinServ = 0.0 # service preload (incl. embedding)
        self.FPreMaxServ = 0.0
        self.FPreMeanServ = 0.0
        self.alpha_A = 0.0 # preload scatter
        self.tau_min = 0.0 # 100% torsional stress aft. tightening
        self.tau_max = 0.0
        self.sig_n_min = 0.0 # normal stress aft. tightening
        self.sig_n_max = 0.0
        self.sig_v_min = 0.0 # von-Mises stress aft. tightening
        self.sig_v_max = 0.0
        self.nue_min = 0.0 # bolt utilization
        self.nue_max = 0.0
        self.bolt_results = {} # results per bolt / loadcase
        self.MOS_glob_slip = 0.0 # global slippage margin
        self.MOS_pres = 0.0 # yield check under bolt head 
        # calculate clamped-part stiffness
        self._calc_joint_stiffness()
        # calculate embedding and thermal losses of joint
        self._calc_embedding()
        self._calc_thermal_loss() # default: standard thermal method
        # calculate joint properties
        self._calc_joint_results()

    # joint stiffness for bolt and clamped parts
    def _calc_joint_stiffness(self):
        # calc clamping length of all clamped parts
        for _, c in self.inp_file.clamped_parts.items():
            self.lk += c[1] # add thickness of clamped parts to lk
        # add length for bolt head + nut for stiffness
        lB = self.lk + 0.8*self.used_bolt.d
        # stiffness of bolt - cB
        # calc stiffness of bolt, p.5-3; stiffer, average value (SHM)
        self.cB = (self.used_bolt_mat.E*(self.used_bolt.A1+\
            self.used_bolt.Ap)/2.0)/lB # stiffness cB bolt
        # bolt compliance p.5-15
        #TODO: check different cB values for result impact; cB SHM conservative??
        #self.cB = self.used_bolt_mat.E/( 0.4*self.used_bolt.d/self.used_bolt.A1 +\
        #    (self.lk+self.used_washer.h)/self.used_bolt.A3 + 0.4*self.used_bolt.d/self.used_bolt.A3)
        
        # Joint elastic compliance for joints with large areas of contact, p.6-7ff.
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
        #        self.lk**2/100)) # with wront parentheses 
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

    # calculate embedding preload loss
    def _calc_embedding(self):
        # calculate number of interfaces, incl. threads (#cl_parts + 1 + 1xthread)
        self.nmbr_interf = len(self.inp_file.clamped_parts) + 1
        # Table 18.4, p.18-7
        lkd = self.lk/self.used_bolt.d # ratio for embedding lookup
        # embedding table 18.4 fitted between ratios 1.0 < ldk < 11.0
        # above and below these values - limit values used
        if self.nmbr_interf==2 or self.nmbr_interf==3:
            logging.info("Embedding: 2 to 3 interfaces")
            if lkd < 1.0:
                self.emb_micron = self._embedding_2_to_3(1.0)
            elif lkd > 11.0:
                self.emb_micron = self._embedding_2_to_3(11.0)
            else:
                self.emb_micron = self._embedding_2_to_3(lkd)
        elif self.nmbr_interf==4 or self.nmbr_interf==5:
            logging.info("Embedding: 4 to 5 interfaces")
            if lkd < 1.0:
                self.emb_micron = self._embedding_4_to_5(1.0)
            elif lkd > 11.0:
                self.emb_micron = self._embedding_4_to_5(11.0)
            else:
                self.emb_micron = self._embedding_4_to_5(lkd)
        elif self.nmbr_interf >= 6:
            logging.info("Embedding: 6 to 7 interfaces")
            if lkd < 1.0:
                self.emb_micron = self._embedding_6_to_7(1.0)
            elif lkd > 11.0:
                self.emb_micron = self._embedding_6_to_7(11.0)
            else:
                self.emb_micron = self._embedding_6_to_7(lkd)
            # if nmbr_interf > 7 --> warning (result not correct)
            if self.nmbr_interf > 7:
                warn_str = "WARNING: Number of embedding interfaces > 7 "\
                    + "--> out of tables range. Embedding preload loss NOT corrrect!"
                print(warn_str)
                logging.warning(warn_str)
        else:
            # number of interfaces too large
            err_str = "Number of interfaces out of tabled range"
            logging.error(err_str)
            raise EmbeddingInterfacesError(err_str)
        # calculate complete embedding in micron = delta_l_Z
        self.emb_micron *= self.nmbr_interf
        # calculate preload loss due to embedding (micron to mm: 1/1000)
        # sigen-convention: minus (-) is loss in preload
        self.FZ = -self.emb_micron*self.phi_K*self.cP/1000

    # calculate thermal effects on preload (preload loss / increase)
    def _calc_thermal_loss(self):
        # thermal expansion of bolt
        d_l_B = self.used_bolt_mat.alpha * self.lk * self.inp_file.delta_t
        # add all clamped parts thermal expansions
        d_l_P = 0.0
        for _, c in self.inp_file.clamped_parts.items():
            d_l_P += self.materials.materials[c[0]].alpha * c[1] * self.inp_file.delta_t
        # preload loss in bolt: clamped parts - bolts
        d_l = d_l_P - d_l_B
        # preload loss due to thermal effects
        # sigen-convention: minus (-) is loss in preload
        FT_res = d_l * (self.cB*self.cP)/(self.cB+self.cP)
        self.FT = [FT_res, FT_res] # save FT for FPreMin & FPreMax

    # VDI method for thermal preload loss (Young's Modulus variation taken into account)
    # NOTE: not the most beautiful implementation...I know - but it works and you do not need it that often
    def calc_thermal_loss_VDI(self, F_VRT_min, F_VRT_max):
        log_str = "VDI thermal preload method used for analysis"
        print(log_str)
        logging.info(log_str)
        # if washer used --> add washer to clamped parts for ###
        if self.inp_file.temp_use_shim != "no":
            self.inp_file.temp_clamped_parts.update( \
                {0 : (self.inp_file.temp_use_shim[0], self.bolts.washers[self.inp_file.temp_use_shim[1]].h) })
        # calculate clamped part stiffness cPT at temperature T
        # --> used for Young's Modulus E_PT calculation only
        cPT = 0.0
        for _, c in self.inp_file.temp_clamped_parts.items():
            cPT += 1./(self.Asub*self.materials.materials[c[0]].E/c[1])
        cPT = 1./cPT # clamped part stiffness' in series
        # get material properties at correct temperatures
        E_SRT = self.used_bolt_mat.E # E of bolt at RT
        E_ST = self.materials.materials[self.inp_file.temp_bolt_material].E
        E_PRT = self.cP*self.lk/self.Asub # E_overall_mean of clamped parts at RT
        E_PT = cPT*self.lk/self.Asub
        alpha_SRT = self.used_bolt_mat.alpha
        alpha_ST = self.materials.materials[self.inp_file.temp_bolt_material].alpha
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
        # calculate preload loss with E taken into account
        # reduction of preload (alpha_ST and alpha_PT used acc. to VDI2230)
        # sign (-) is loss in preload
        dS = 1./self.cB # compliance of bolt
        dP = 1./self.cP # compliance of clamped parts
        denom = dS*E_SRT/E_ST + dP*E_PRT/E_PT # denominator
        d_F_th_min = F_VRT_min * (1 - (dS+dP)/denom) \
            + self.lk*(alpha_ST - alpha_PT)*self.inp_file.delta_t/denom
        d_F_th_max = F_VRT_max * (1 - (dS+dP)/denom) \
            + self.lk*(alpha_ST - alpha_PT)*self.inp_file.delta_t/denom
        # generate output string
        output_str = "" # use output_str for print() or print-to-file
        output_str += "{0:=^95}\n".format('=') # global splitter
        output_str += "| {0:^50}|{1:^20}|{2:^20}|\n".format("VDI 2230 Thermal Preload Method",\
            "Room-Temp (ref)", "defined Temp.")
        output_str += "{0:=^95}\n".format('=')
        output_str += "| {0:<50}|{1:^20.1f}|{2:^20.1f}|\n".format(\
            "Young's Modulus of bolt [MPa]:", E_SRT, E_ST)
        output_str += "| {0:<50}|{1:^20.1f}|{2:^20.1f}|\n".format(\
            "Young's Modulus of clamped parts [MPa]:", E_PRT, E_PT)
        output_str += "| {0:<50}|{1:^20.3e}|{2:^20.3e}|\n".format(\
            "CTE of bolt [1/K]:", alpha_SRT, alpha_ST)
        output_str += "| {0:<50}|{1:^20.3e}|{2:^20.3e}|\n".format(\
            "CTE of clamped parts [1/K]:", alpha_PRT, alpha_PT)
        output_str += "| {0:<50}|{1:^20.3e}|{2:^20}|\n".format(\
            "Stiffness of bolt [N/mm]:", self.cB, '-')
        output_str += "| {0:<50}|{1:^20.3e}|{2:^20}|\n".format(\
            "Stiffness of clamped parts [N/mm]:", self.cP, '-')
        output_str += "|-{0:-^50}+{1:-^20}+{2:-^20}|\n".format("-", "-", "-")
        output_str += "| {0:<64} {1:^27.2f}|\n".format(\
            "Clamped length lk [mm]:", self.lk)
        output_str += "| {0:<64} {1:^27.1f}|\n".format(\
            "Temperature difference delta_T [K]:", self.inp_file.delta_t)
        output_str += "|-{0:-^50}-{1:-^20}-{2:-^20}|\n".format("-", "-", "-")
        output_str += "| {0:<64} {1:>12.1f} / {2:<12.1f}|\n".format(\
            "Term-1 preload loss based on FVmin / FVmax [N]:",\
            F_VRT_min*(1-(dS+dP)/denom), F_VRT_max*(1-(dS+dP)/denom))
        output_str += "| {0:<64} {1:^27.1f}|\n".format(\
            "Term-2 Preload loss based on CTE [N]:",\
                self.lk*(alpha_ST-alpha_PT)*self.inp_file.delta_t/denom)
        output_str += "| {0:<64} {1:>12.1f} / {2:<12.1f}|\n".format(\
            "Preload loss due to thermal effects based on FVmin / FVmax [N]:",\
                d_F_th_min, d_F_th_max)
        output_str += "{0:=^95}\n".format('=') # global splitter
        # return tuple (d_F_th_min, d_F_th_max, output_str)
        return (d_F_th_min, d_F_th_max, output_str)

    # fitted embedding Table 18.4, p.18-7
    # valid quadratic fit between values: 1.0 < ldk < 11.0
    def _embedding_2_to_3(self, lkd):
        return -0.0133*lkd**2+0.3*lkd+0.8333
    def _embedding_4_to_5(self, lkd):
        return -0.0067*lkd**2+0.15*lkd+0.6667
    def _embedding_6_to_7(self, lkd):
        return -0.0053*lkd**2+0.12*lkd+0.4333

    # calculate joint results 
    def _calc_joint_results(self):
        # check if prevailing torque is defined (e.g. helicoils used)
        # prevailing torque if locking mechanism defined
        if self.inp_file.locking_mechanism == "yes":
            self.Tp = self.inp_file.prevailing_torque
        #NOTE: friction angle valid ONLY for 60deg threads!! (metric + unified threads)
        # COF_BOLT = [mu_head_max, mu_thread_max, mu_head_min, mu_thread_min] 
        mu_uhmax = self.inp_file.cof_bolt[0]
        mu_thmax = self.inp_file.cof_bolt[1]
        mu_uhmin = self.inp_file.cof_bolt[2]
        mu_thmin = self.inp_file.cof_bolt[3]
        rho_max = math.atan(mu_thmax/math.cos(30.*math.pi/180.))
        rho_min = math.atan(mu_thmin/math.cos(30.*math.pi/180.))
        # mean diameter of bolt head 
        Dkm = (self.inp_file.through_hole_diameter+self.used_bolt.dh) /2
        # min / max joint coefficient
        Kmax = ( self.used_bolt.d2/2*math.tan(self.used_bolt.slope+rho_max) +\
            mu_uhmax*Dkm/2 ) / self.used_bolt.d
        Kmin = ( self.used_bolt.d2/2*math.tan(self.used_bolt.slope+rho_min) +\
            mu_uhmin*Dkm/2 ) / self.used_bolt.d
        # calculate bolt preload for tightening torque
        TA = self.inp_file.tight_torque
        Tscatter = self.inp_file.torque_tol_tight_device
        TAmin = TA - Tscatter
        TAmax = TA + Tscatter
        # min / max init. preload after tightening (*1000 to get N)
        self.FPreMin = (TAmin-self.Tp)/(Kmax*self.used_bolt.d)*1000
        self.FPreMax = (TAmax-self.Tp)/(Kmin*self.used_bolt.d)*1000
        self.FPreMean = (self.FPreMax+self.FPreMin)/2
        # calculate tightening factor (preload scatter incl. friction and tight. dev. tolerance)
        self.alpha_A = self.FPreMax/self.FPreMin
        # check if VDI thermal method is used
        if self.inp_file.temp_use_vdi_method == "yes":
            temp_res = self.calc_thermal_loss_VDI(self.FPreMin, self.FPreMax)
            self.FT = [temp_res[0], temp_res[1]] # safe FT for FPreMin & FPreMax
            self.FT_outp_str = temp_res[2]
        # service preload with embedding and thermal loss
        self.FPreMinServ = self.FPreMin + self.FZ + self.FT[0]
        self.FPreMaxServ = self.FPreMax + self.FZ + self.FT[1]
        self.FPreMeanServ = (self.FPreMinServ+self.FPreMaxServ)/2
        # mean preload in the complete joint (incl. all bolts)
        sum_FPreMeanServ = self.nmbr_of_bolts*self.FPreMeanServ

        # Calculate stresses
        # max. torsional stress after tightening - see VDI2230 p.24
        Wp = (self.used_bolt.ds**3)*math.pi/16
        #NOTE: only applicable for metric threads
        MG_max = self.FPreMax*self.used_bolt.d2/2*(self.used_bolt.p/(self.used_bolt.d2*math.pi)+\
            1.155*mu_thmin)
        MG_min = self.FPreMin*self.used_bolt.d2/2*(self.used_bolt.p/(self.used_bolt.d2*math.pi)+\
            1.155*mu_thmax)
        self.tau_min = MG_min/Wp
        self.tau_max = MG_max/Wp # max. torsional stress aft. tightening
        # max. normal stress after tightening
        self.sig_n_min = self.FPreMin/self.used_bolt.As
        self.sig_n_max = self.FPreMax/self.used_bolt.As
        # von-Mises equivalent stress in bolt
        self.sig_v_min = math.sqrt(self.sig_n_min**2 + 3*(self.tau_min)**2)
        self.sig_v_max = math.sqrt(self.sig_n_max**2 + 3*(self.tau_max)**2)
        # degree of utilization (utilization of the minimum yield point)
        self.nue_min = self.sig_v_min/self.used_bolt_mat.sig_y
        self.nue_max = self.sig_v_max/self.used_bolt_mat.sig_y
        #
        # calculate yield MOS under bolt head / first clamped part after tightening
        self.MOS_pres = self._mos_pres(self.FPreMax)

        # perform calculation for all bolts / loadcases
        sum_FPA = 0.0
        sum_FQ = 0.0
        for lc_name, lc in self.inp_file.bolt_loads.items():
            FA = lc[0] # axial bolt force
            FQ = math.sqrt(lc[1]**2+lc[2]**2) # shear bolt force
            FPA = FA*(1-self.phi_n) # reduction in clamping force
            FSA = FA*self.phi_n # additional bolt force
            # required clamping force for friction grip
            FKreq = FQ/(self.inp_file.nmbr_shear_planes*self.inp_file.cof_clamp)
            ##FM_minslip = FKreq*self.inp_file.fos_slip+FPA*self.inp_file.fos_y+self.FZ
            ##FM_mingap = FPA*self.inp_file.fos_gap+self.FZ
            ##FM_min = max(FM_minslip,FM_mingap)
            ### required torque for mu_max (1/1000 to get Nm)
            ##Treq = (FM_min*(self.used_bolt.d2/2*math.tan(self.used_bolt.slope+rho_max)+\
            ##    mu_uhmax*Dkm/2)+self.Tp)/1000
            # calc sums for global slippage margin
            sum_FPA += FPA
            sum_FQ += FQ
            #
            # local slippage margin
            if FKreq==0:
                MOS_loc_slip = math.inf # set to "inf" if no shear load defined
            else:
                MOS_loc_slip = (self.FPreMinServ-FPA)/(FKreq*self.inp_file.fos_slip)-1
            # local gapping margin
            MOS_gap = self.FPreMinServ/(self.inp_file.fos_gap*FPA)-1
            # yield bolt margin
            MOS_y = self.used_bolt_mat.sig_y/math.sqrt( ((self.FPreMaxServ+\
                FSA*self.inp_file.fos_y)/self.used_bolt.As)**2 +\
                    3*(0.5*self.tau_max)**2 )-1
            # ultimate bolt margin
            MOS_u = self.used_bolt_mat.sig_u/math.sqrt( ((self.FPreMaxServ+\
                FSA*self.inp_file.fos_u)/self.used_bolt.As)**2 +\
                    3*(0.5*self.tau_max)**2 )-1
            # yield margin for pressure under bolt head
            MOS_loc_pres = self._mos_pres(self.FPreMaxServ+FSA*self.inp_file.fos_y)
            # save data for each bolt/loadcase to result dict
            # lc_name : [FA, FQ, FSA, FPA, MOS_loc_slip, MOS_gap, MOS_y, MOS_u, MOS_loc_pres]
            self.bolt_results.update({lc_name : [FA, FQ, FSA, FPA, MOS_loc_slip, MOS_gap,\
                MOS_y, MOS_u, MOS_loc_pres]})

        # calculate global slippage margin
        # total lateral joint force which can be transmitted via friction
        F_tot_lat = (sum_FPreMeanServ-sum_FPA)*self.inp_file.cof_clamp*self.inp_file.nmbr_shear_planes
        self.MOS_glob_slip = F_tot_lat/(sum_FQ*self.inp_file.fos_slip)-1

    # check yield MoS under bolt head and between washer and first clamped part
    def _mos_pres(self, F_axial):
        MOS_pres = 0.0 # return value
        # yield strength of first clamped part (under washer)
        sig_y_pres = self.materials.materials[self.inp_file.clamped_parts[1][0]].sig_y
        if self.inp_file.use_shim != "no": # with washer
            # minimal area under bolt head
            A_pres_1 = (self.used_bolt.dh**2)*math.pi/4 - \
                (self.bolts.washers[self.inp_file.use_shim[1]].dmin**2)*math.pi/4
            # yield strength of first washer (under bolt head)
            MOS_pres_1 = self.materials.materials[self.inp_file.use_shim[0]].sig_y / (F_axial/A_pres_1) - 1
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

    # print joint inputs
    def print_input(self):
        #TODO: provide print of input-parameters of joint analysis
        pass

    # get global analysis results string
    def _get_global_result_str(self):
        output_str = "" # use output_str for print() or print-to-file
        output_str += "{0:=^95}\n".format('=') # global splitter
        output_str += "| {0:^91} |\n".format("ESA PSS-03-208 Issue 1 ANALYSIS RESULTS")
        output_str += "{0:=^95}\n".format('=')
        output_str += "| {0:<50} {1:^20.1f} {2:^20}|\n".format(\
            "Tightening torque w/o prevailing torque [Nm]:", self.inp_file.tight_torque, "")
        output_str += "| {0:<50} {1:^20.1f} {2:^20}|\n".format(\
            "Prevailing torque [Nm]:", self.Tp, "")
        output_str += "| {0:<50} {1:^20.1f} {2:^20}|\n".format(\
            "Tightening torque with prevailing torque [Nm]:", \
                self.inp_file.tight_torque+self.Tp, "")
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
        output_str += "| {0:<50}|{1:^41.1f}|\n".format(\
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
    def print_results(self, output_file=None):
        # print results to terminal
        print() # print empty line
        print(self._get_global_result_str())
        if self.inp_file.temp_use_vdi_method == "yes":
            print(self.FT_outp_str)
        print(self._get_bolt_result_str())
        # print results to output_file
        if output_file != None:
            log_str = "Output file written: {0:^}".format(output_file)
            print(log_str)
            logging.info(log_str)
            # write output file
            with open(output_file, 'w') as fid:
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

