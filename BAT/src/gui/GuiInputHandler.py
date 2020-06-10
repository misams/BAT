from src.functions.InputFileParser import InputFileParser
from datetime import datetime

class GuiInputHandler:
    def __init__(self):
        # project values
        self.project_name = ""
        self.method = ""
        # bolts-definition-block
        self.joint_mos_type = "" # use min or mean preload for slippage MOS calculation
        self.bolt = "" # e.g. S_M4x0.5 - socket M4 fine thread
        self.bolt_material = ""
        self.cof_bolt = None # optional [mu_head_max, mu_thread_max, mu_head_min, mu_thread_min]
        self.tight_torque = 0.0 # also use "STD"
        self.torque_tol_tight_device = 0.0 # optional
        self.locking_mechanism = "" # e.g. Helicoil
        self.prevailing_torque = 0.0 # only used if *LOCKING_MECHANISM = yes
        self.loading_plane_factor = 0.0
        # clamped-parts-definition-block
        self.cof_clamp = 0.0 # min. coefficient of friction between clamped parts
        self.nmbr_shear_planes = 0
        self.use_shim = None
        self.through_hole_diameter = 0.0
        self.subst_da = ""
        self.clamped_parts = {}
        # FOS-definition-block
        self.fos_y = 0.0
        self.fos_u = 0.0
        self.fos_slip = 0.0
        self.fos_gap = 0.0
        # bolt-loads
        self.bolt_loads = [] # 2d-array
        # temperature input
        self.delta_t = 0.0
        self.temp_use_vdi_method = ""
        self.temp_bolt_material = "" # for VDI method
        self.temp_use_shim = None # for VDI method
        self.temp_clamped_parts = {} # for VDI method

    # compare GuiInputHandler and InputFileParser (without VDI thermal method)
    def compareInput(self, inp_file : InputFileParser):
        compare_items = [] # append each value which has been changed
        if self.project_name != inp_file.project_name:
            compare_items.append("*PROJECT_NAME")
        if self.method != inp_file.method:
            compare_items.append("*METHOD")
        if self.joint_mos_type != inp_file.joint_mos_type:
            compare_items.append("*JOINT_MOS_TYPE")
        if self.bolt != inp_file.bolt:
            compare_items.append("*BOLT")
        if self.bolt_material != inp_file.bolt_material:
            compare_items.append("*BOLT_MATERIAL")
        if self.cof_clamp != inp_file.cof_clamp:
            compare_items.append("*COF_CLAMP")
        if self.cof_bolt != inp_file.cof_bolt:
            compare_items.append("*COF_BOLT")
        if self.tight_torque != inp_file.tight_torque:
            compare_items.append("*TIGHT_TORQUE")
        if self.torque_tol_tight_device != inp_file.torque_tol_tight_device:
            compare_items.append("*TORQUE_TOL_TIGHT_DEVICE")
        if self.locking_mechanism != inp_file.locking_mechanism:
            compare_items.append("*LOCKING_MECHANISM")
        if self.prevailing_torque != inp_file.prevailing_torque and self.locking_mechanism=="yes":
            compare_items.append("*PREVAILING_TORQUE")
        if self.loading_plane_factor != inp_file.loading_plane_factor:
            compare_items.append("*LOADING_PLANE_FACTOR")
        if self.nmbr_shear_planes != inp_file.nmbr_shear_planes:
            compare_items.append("*NMBR_SHEAR_PLANES")
        if self.use_shim != inp_file.use_shim:
            compare_items.append("*USE_SHIM")
        if self.through_hole_diameter != inp_file.through_hole_diameter:
            compare_items.append("*THROUGH_HOLE_DIAMETER")
        if self.subst_da != inp_file.subst_da:
            compare_items.append("*SUBST_DA")
        if self.clamped_parts != inp_file.clamped_parts:
            compare_items.append("*CLAMPED_PARTS(i)")
            print(self.clamped_parts, inp_file.clamped_parts)
        if self.fos_y != inp_file.fos_y:
            compare_items.append("*FOS_Y")
        if self.fos_u != inp_file.fos_u:
            compare_items.append("*FOS_U")
        if self.fos_slip != inp_file.fos_slip:
            compare_items.append("*FOS_SLIP")
        if self.fos_gap != inp_file.fos_gap:
            compare_items.append("*FOS_GAP")
        if self.bolt_loads != inp_file.bolt_loads:
            compare_items.append("BOLT-LOADS")
        if self.delta_t != inp_file.delta_t:
            compare_items.append("*DELTA_T")
        # return compare_items
        return compare_items

    # save input file with GUI inputs
    def saveInputFile(self, inp_file_name):
        # write input file
        with open(inp_file_name, 'w') as fid:
            output_str = "" # use output_str for fid.write()
            # define header
            output_str += "{0:#^40}\n".format('#')
            output_str += "#{0:^38}#\n".format(' ')
            output_str += "# BAT Input File{0:^23}#\n".format(' ')
            output_str += "#{0:^38}#\n".format(' ')
            timestamp = str(datetime.now().strftime("%d-%m-%Y %H:%M:%S"))
            output_str += "# Created: {0:^}         #\n".format(timestamp)
            output_str += "# Unit System: mm, N, Nm               #\n"
            output_str += "#{0:^38}#\n".format(' ')
            output_str += "{0:#^40}\n\n".format('#')
            # project entries
            output_str += "*PROJECT_NAME = {0:^}\n".format(self.project_name)
            output_str += "*METHOD = {0:^} # {comment:^}\n\n".format(self.method, \
                comment="ECSS or VDI2230 (not implemented)")
            # definition of used bolts
            output_str += "# Definition of used bolt\n"
            output_str += "*BOLT_DEFINITION\n"
            output_str += "    *JOINT_MOS_TYPE = {0:^} # {comment:^}\n".format(self.joint_mos_type, \
                comment="min (STD) or mean: use min or mean preload for slippage MOS calculation")
            output_str += "    *BOLT = {0:^} # {comment:^}\n".format(self.bolt, \
                comment="or e.g. S_M8x1 for fine thread")
            output_str += "    *BOLT_MATERIAL = {0:^}\n".format(self.bolt_material)
            cof_bolt_str = str(self.cof_bolt).replace('(','[').replace(')',']')
            output_str += "    *COF_BOLT = {0:^} # {comment:^}\n".format(cof_bolt_str, \
                comment="[mu_head_max, mu_thread_max, mu_head_min, mu_thread_min]")
            output_str += "    *TIGHT_TORQUE = {0:.2f}\n".format(self.tight_torque)
            output_str += "    *TORQUE_TOL_TIGHT_DEVICE = {0:.2f} # {comment:^}\n".format(self.torque_tol_tight_device, \
                comment="torque wrench tolerance")
            output_str += "    *LOCKING_MECHANISM = {0:^} # {comment:^}\n".format(self.locking_mechanism, \
                comment="\"yes\" or \"no\", e.g. yes for Helicoil")
            output_str += "    *PREVAILING_TORQUE = {0:.2f} # {comment:^}\n".format(self.prevailing_torque, \
                comment="only used if *LOCKING_MECHANISM = yes")
            output_str += "    *LOADING_PLANE_FACTOR = {0:.3f}\n".format(self.loading_plane_factor)
            output_str += "*BOLT_DEFINITION_END\n\n"
            # definition of clamped parts
            output_str += "# Definition of clamped parts\n"
            output_str += "*CLAMPED_PARTS_DEFINITION\n"
            output_str += "    *COF_CLAMP = {0:.2f} # {comment:^}\n".format(self.cof_clamp, \
                comment="min. coefficient of friction between clamped parts")
            output_str += "    *NMBR_SHEAR_PLANES = {0:d}\n".format(self.nmbr_shear_planes)
            if self.use_shim == "no":
                shim_str = "no"
            else:
                shim_str = "[{0:^}, {1:^}]".format(self.use_shim[0], self.use_shim[1])
            output_str += "    *USE_SHIM = {0:^} # {comment:^}\n".format(shim_str, \
                comment="e.g. [Shim-Material, Shim-Type] out of database or use \"no\"")
            output_str += "    *THROUGH_HOLE_DIAMETER = {0:.2f} # {comment:^}\n".format(self.through_hole_diameter, \
                comment="D_B, drilled hole diameter in clamped parts")
            output_str += "    *SUBST_DA = {0:^} # {comment:^}\n".format(self.subst_da, \
                comment="\"no\" or define substitutional outside diameter of of the basic solid at the interface")
            output_str += "    # define n-clamped parts; use ascending index and start at (1)\n"
            for key, value in self.clamped_parts.items():
                if key != 0: # ignore shim
                    output_str += "    *CLAMPED_PART({0:d}) = [{1:^}, {2:.2f}]\n".format(key, value[0], value[1])
            output_str += "*CLAMPED_PARTS_DEFINITION_END\n\n"
            # definition of factors of safety
            output_str += "# Definition of factors of safety\n"
            output_str += "*FOS_DEFINITION\n"
            output_str += "    *FOS_Y = {0:.2f} # {comment:^}\n".format(self.fos_y, \
                comment="yield")
            output_str += "    *FOS_U = {0:.2f} # {comment:^}\n".format(self.fos_u, \
                comment="ultimate")
            output_str += "    *FOS_SLIP = {0:.2f} # {comment:^}\n".format(self.fos_slip, \
                comment="slippage")
            output_str += "    *FOS_GAP = {0:.2f} # {comment:^}\n".format(self.fos_gap, \
                comment="gapping")
            output_str += "*FOS_DEFINITION_END\n\n"
            # definition of bolt loads
            output_str += "# Definition of bolt loads\n"
            output_str += "# load/bolt-ID (max. 12 char.), axial-force, lateral-force-1, lateral-force-2 (optional)\n"
            output_str += "*BOLT_LOAD_DEFINITION\n"
            for bl in self.bolt_loads:
                output_str += "{0:^} {1:.2f} {2:.2f} {3:.2f}\n".format(bl[0], bl[1], bl[2], bl[3])
            output_str += "*BOLT_LOAD_DEFINITION_END\n\n"
            # definition of temperature environment
            output_str += "# Definition of temperature environment\n"
            output_str += "# temperature difference defined in K or deg-C\n"
            output_str += "# reference temperature == assembly temperature\n"
            output_str += "*TEMP_DEFINITION\n"
            output_str += "    *DELTA_T = {0:.2f} # {comment:^}\n".format(self.delta_t, \
                comment="+K/degC means higher temperature at service")
            # NOTE: VDI method not implemented in GUI; writes dummy block
            output_str += "*TEMP_DEFINITION\n"
            # write GUI input to BAT input file
            fid.write(output_str)

    # print function of input file
    # DEBUGGING function
    def print(self):
        print("*PROJECT_NAME:               {0:^}".format(self.project_name))
        print("*METHOD:                     {0:^}".format(self.method))
        print("*JOINT_MOS_TYPE:             {0:^}".format(self.joint_mos_type))
        print("*BOLT:                       {0:^}".format(self.bolt))
        print("*BOLT_MATERIAL:              {0:^}".format(self.bolt_material))
        print("*COF_CLAMP:                  {0:^}".format(str(self.cof_clamp)))
        print("*COF_BOLT:                   {0:^}".format(str(self.cof_bolt)))
        print("*TIGHT_TORQUE:               {0:^}".format(str(self.tight_torque)))
        print("*TORQUE_TOL_TIGHT_DEVICE:    {0:^}".format(str(self.torque_tol_tight_device)))
        print("*LOCKING_MECHANISM:          {0:^}".format(self.locking_mechanism))
        print("*PREVAILING_TORQUE:          {0:^}".format(str(self.prevailing_torque)))
        print("*LOADING_PLANE_FACTOR:       {0:^}".format(str(self.loading_plane_factor)))
        print("*NMBR_SHEAR_PLANES:          {0:^}".format(str(self.nmbr_shear_planes)))
        print("*USE_SHIM:                   {0:^}".format(str(self.use_shim)))
        print("*THROUGH_HOLE_DIAMETER:      {0:^}".format(str(self.through_hole_diameter)))
        print("*SUBST_DA:                   {0:^}".format(self.subst_da))
        print("*CLAMPED_PARTS(i):           {0:^}".format(str(self.clamped_parts)))
        print("*FOS_Y:                      {0:^}".format(str(self.fos_y)))
        print("*FOS_U:                      {0:^}".format(str(self.fos_u)))
        print("*FOS_SLIP:                   {0:^}".format(str(self.fos_slip)))
        print("*FOS_GAP:                    {0:^}".format(str(self.fos_gap)))
        print("BOLT-LOADS:                  {0:^}".format(str(self.bolt_loads)))
        print("*DELTA_T:                    {0:^}".format(str(self.delta_t)))
        print("#\n# VDI method for thermal preload loss with E\n#")
        print("*TEMP_USE_VDI_METHOD:        {0:^}".format(self.temp_use_vdi_method))
        print("*TEMP_BOLT_MATERIAL:         {0:^}".format(str(self.temp_bolt_material)))
        print("*TEMP_USE_SHIM:              {0:^}".format(str(self.temp_use_shim)))
        print("*TEMP_CLAMPED_PARTS(i):      {0:^}".format(str(self.temp_clamped_parts)))
        print()
