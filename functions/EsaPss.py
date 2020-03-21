from .InputFileParser import InputFileParser
from .MaterialManager import MaterialManager
from .BoltManager import BoltManager
import math
"""
Bolt analysis according to ESA PSS-03-208 Issue 1, December 1989
Guidelines for threaded fasteners, european space agency

Concentric axially loaded joints
"""
class EsaPss:
    def __init__(self, inp_file : InputFileParser, materials : MaterialManager, bolts : BoltManager):
        self.inp_file = inp_file
        self.materials = materials
        self.bolts = bolts
        # used variables for analysis
        self.used_bolt = bolts.bolts[self.inp_file.bolt_size] # used bolt
        self.used_bolt_mat = self.materials.materials[self.inp_file.bolt_material]
        self.used_washer = ""
        self.used_washer_material = ""
        if self.inp_file.use_shim != "no":
            self.used_washer = bolts.washers[self.inp_file.use_shim[1]] # "no" or washer-id
            self.used_washer_material = self.materials.materials[self.inp_file.use_shim[0]]
        else:
            print("No shim used.")
        # calculated variables
        self.lk = 0.0
        self.DA = 0.0
        self.Asub = 0.0
        self.Dsub = 0.0
        self.cB = 0.0
        self.cP = 0.0
        self.phi_K = 0.0
        self.phi_n = 0.0
        self.nmbr_interf = 0
        self.emb_micron = 0.0
        # calculate clamped-part stiffness
        self._calc_joint_stiffness()
        # calculate embedding losses of joint
        self._calculate_embedding()

    # joint stiffness
    def _calc_joint_stiffness(self):
        # calc clamping length of all clamped parts
        for _, c in self.inp_file.clamped_parts.items():
            self.lk += c[1] # add thickness of clamped parts to lk
        # incl. washer if defined
        if self.used_washer.name.lower() != "no":
            self.lk += self.used_washer.h
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
            print("Calculate Asub acc. to case (ii)")
            # if *SUBST_DA = no use rule of thumb for DA estimation, p.6-11
            if self.inp_file.subst_da != "no":
                self.DA = float(self.inp_file.subst_da)
                print("Substitutional diameter DA set: {0:.2f}".format(self.DA))
            else:
                self.DA = self.used_bolt.dh*(2.+3.)/2. # mean value betw. range 2-3 used, p.6-11
                print("Mean substitutional diameter DA set (rule of thumb): {0:.2f}".format(self.DA))
            # calc subst. area for clamped parts
            self.Asub = math.pi/4*( self.used_bolt.dh**2-self.inp_file.through_hole_diameter**2 ) +\
                math.pi/8*( self.DA/self.used_bolt.dh-1 ) *\
                ( self.used_bolt.dh*self.lk/5+(self.lk**2)/100 )
        elif self.lk/self.used_bolt.d > 2.0:
            print("Calculate Asub acc. to case (iii)")
            self.Asub = math.pi/4*((self.used_bolt.dh+self.lk/10)**2 - \
                self.inp_file.through_hole_diameter**2)
        else:
            print("Case i applicable - change DA!!")
        # calc Dsub out of Asub
        self.Dsub = math.sqrt(4*self.Asub/math.pi + self.inp_file.through_hole_diameter**2)

        # Asub (SHM)
        #Asub = math.pi/4*(self.used_bolt.dh**2-self.inp_file.through_hole_diameter**2+math.pi/8*\
        #    (self.used_washer.dmaj/self.used_bolt.dh-1)*(self.used_bolt.dh*self.lk/5+\
        #        self.lk**2/100)) # with wront parentheses 
        #Asub = math.pi/4*( self.used_bolt.dh**2-self.inp_file.through_hole_diameter**2 ) +\
        #    math.pi/8*( self.used_washer.dmaj/self.used_bolt.dh-1 ) *\
        #        ( self.used_bolt.dh*self.lk/5+self.lk**2/100 ) # with corrected parentheses

        # calculate stiffness of clamped parts - cP
        if self.inp_file.use_shim != "no":
            self.cP += 1./(self.Asub*self.used_washer_material.E/self.used_washer.h)
        for _, c in self.inp_file.clamped_parts.items():
            self.cP += 1./(self.Asub*self.materials.materials[c[0]].E/c[1])
        self.cP = 1./self.cP # clamped part stiffness' in series

        # load-factor
        self.phi_K = self.cB/(self.cB+self.cP) # load factor - load under bolt head
        self.phi_n = self.inp_file.loading_plane_factor*self.phi_K # load factor - load at n*lk

    def _calculate_embedding(self):
        # calculate number of interfaces, incl. threads (#cl_parts + 1 + 1xthread)
        self.nmbr_interf = len(self.inp_file.clamped_parts) + 2
        if self.inp_file.use_shim != "no":
            self.nmbr_interf += 1
        # Table 18.4, p.18-7
        lkd = self.lk/self.used_bolt.d
        if self.nmbr_interf==2 or self.nmbr_interf==3:
            print("Embedding: 2 to 3 interfaces")
            if lkd < 1.0:
                self.emb_micron = self._embedding_2_to_3(1.0)
            elif lkd > 11.0:
                self.emb_micron = self._embedding_2_to_3(11.0)
            else:
                self.emb_micron = self._embedding_2_to_3(lkd)
        elif self.nmbr_interf==4 or self.nmbr_interf==5:
            print("Embedding: 4 to 5 interfaces")
            if lkd < 1.0:
                self.emb_micron = self._embedding_4_to_5(1.0)
            elif lkd > 11.0:
                self.emb_micron = self._embedding_4_to_5(11.0)
            else:
                self.emb_micron = self._embedding_4_to_5(lkd)
        elif self.nmbr_interf==6 or self.nmbr_interf==7:
            print("Embedding: 6 to 7 interfaces")
            if lkd < 1.0:
                self.emb_micron = self._embedding_6_to_7(1.0)
            elif lkd > 11.0:
                self.emb_micron = self._embedding_6_to_7(11.0)
            else:
                self.emb_micron = self._embedding_6_to_7(lkd)
        else:
            print("Number of interfaces out of tabled range")
        # calculate complete embedding in micron
        self.emb_micron *= self.nmbr_interf

    # fitted embedding Table 18.4, p.18-7
    def _embedding_2_to_3(self, lkd):
        return -0.0133*lkd**2+0.3*lkd+0.8333
    def _embedding_4_to_5(self, lkd):
        return -0.0067*lkd**2+0.15*lkd+0.6667
    def _embedding_6_to_7(self, lkd):
        return -0.0053*lkd**2+0.12*lkd+0.4333

    # print analysis results
    def print_results(self):
        print("Clamped length lk:         {0:.2f}".format(self.lk))
        print("Subst. outside dia. DA:    {0:.2f}".format(self.DA))
        print("Subst. area of CP Asub:    {0:.2f}".format(self.Asub))
        print("Subst. dia. of CP Dsub:    {0:.2f}".format(self.Dsub))
        print("Bolt stiffness cB:         {0:.4g}".format(self.cB))
        print("Clamped part stiffness cP: {0:.4g}".format(self.cP))
        print("Load factor Phi_K :        {0:.4f}".format(self.phi_K))
        print("Load factor Phi_n :        {0:.4f}".format(self.phi_n))
        print("Number of interfaces:      {0:d}".format(self.nmbr_interf))
        print("Embedding [micron]:        {0:.2f}".format(self.emb_micron))
