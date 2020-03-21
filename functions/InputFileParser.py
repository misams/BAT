import csv
from pathlib import Path

class InputFileParser:
    def __init__(self, input_file):
        # input file path
        self.input_file = Path(input_file)
        # input file values
        self.project_name = ""
        self.method = ""
        # bolts-definition-block
        self.joint_type= 0 # really neccessary??
        self.bolt_size = "" # e.g. M8f
        self.bolt_material = ""
        self.cof_clamp = 0.0 # min. coefficient of friction between clamped parts
        self.cof_bolt = None # optional [mu_head_max, mu_thread_max, mu_head_min, mu_thread_min]
        self.tight_torque = 0.0 # also use "STD"
        self.bolt_head_type = "" # or hexagon
        self.torque_tol_tight_device = 0.0 # optional
        self.locking_mechanism = "" # e.g. Helicoil
        self.prevailing_torque = 0.0 # only used if *LOCKING_MECHANISM = yes
        self.loading_plane_factor = 0.0
        # clamped-parts-definition-block
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
        self.bolt_loads = {}
        # read input file and process
        self._read_input_file()

    # read input file and process data
    def _read_input_file(self):
        print("Read and process input file:  {0:^}".format(str(self.input_file.absolute())))
        with open(self.input_file) as fid:
            line = fid.readline() # first line in file
            while line: # loop through input-file
                if line.lstrip()[0:13]=="*PROJECT_NAME":
                    self.project_name = self._proc_line(line)[1]
                elif line.lstrip()[0:7]=="*METHOD":
                    self.method = self._proc_line(line)[1]
                elif line.lstrip()[0:16]=="*BOLT_DEFINITION":
                    line = fid.readline()
                    # loop through bolt-definition block
                    while line.lstrip()[0:20]!="*BOLT_DEFINITION_END":
                        tmp_line = self._proc_line(line) # process inp-file line
                        if tmp_line[0]=="*JOINT_TYPE":
                            self.joint_type = int(tmp_line[1])
                        elif tmp_line[0]=="*BOLT_SIZE":
                            self.bolt_size = tmp_line[1]
                        elif tmp_line[0]=="*BOLT_MATERIAL":
                            self.bolt_material = tmp_line[1]
                        elif tmp_line[0]=="*COF_CLAMP":
                            self.cof_clamp = float(tmp_line[1])
                        elif tmp_line[0]=="*COF_BOLT":
                            # get (mu_head_max, mu_thread_max, mu_head_min, mu_thread_min)
                            tmp_cof_bolt_str = tmp_line[1].replace('[','').replace(']','').split(',')
                            if len(tmp_cof_bolt_str)==4:
                                self.cof_bolt = (float(tmp_cof_bolt_str[0]), float(tmp_cof_bolt_str[1]), \
                                    float(tmp_cof_bolt_str[2]), float(tmp_cof_bolt_str[3]))
                            else:
                                #TODO: error handling
                                print("ERROR: 4 input parameters (COF_BOLT) neccessary!")
                        elif tmp_line[0]=="*TIGHT_TORQUE":
                            self.tight_torque = float(tmp_line[1])
                        elif tmp_line[0]=="*BOLT_HEAD_TYPE":
                            self.bolt_head_type = tmp_line[1]
                        elif tmp_line[0]=="*TORQUE_TOL_TIGHT_DEVICE":
                            self.torque_tol_tight_device = float(tmp_line[1])
                        elif tmp_line[0]=="*LOCKING_MECHANISM":
                            self.locking_mechanism = tmp_line[1]
                        elif tmp_line[0]=="*PREVAILING_TORQUE":
                            self.prevailing_torque = float(tmp_line[1])
                        elif tmp_line[0]=="*LOADING_PLANE_FACTOR":
                            self.loading_plane_factor = float(tmp_line[1])
                        line = fid.readline()
                elif line.lstrip()[0:25]=="*CLAMPED_PARTS_DEFINITION":
                    line = fid.readline()
                    # loop through clamped-parts-definition block
                    while line.lstrip()[0:29]!="*CLAMPED_PARTS_DEFINITION_END":
                        tmp_line = self._proc_line(line) # process inp-file line
                        if tmp_line[0]=="*NMBR_SHEAR_PLANES":
                            self.nmbr_shear_planes = int(tmp_line[1])
                        elif tmp_line[0]=="*USE_SHIM":
                            if tmp_line[1] == "no":
                                self.use_shim = "no"
                            else:
                                # get (shim-material, shim-type) or no
                                tmp_shim_str = tmp_line[1].replace('[','').replace(']','').split(',')
                                self.use_shim = (tmp_shim_str[0].lstrip().rstrip(), \
                                    tmp_shim_str[1].lstrip().rstrip())
                        elif tmp_line[0]=="*THROUGH_HOLE_DIAMETER":
                            self.through_hole_diameter = float(tmp_line[1])
                        elif tmp_line[0]=="*SUBST_DA":
                            self.subst_da = tmp_line[1]
                        elif tmp_line[0][:-3]=="*CLAMPED_PART":
                            # get clamped-part number (inside brackets) and save n-CP to dict
                            cp_nmbr = int(tmp_line[0][tmp_line[0].find("(")+1:tmp_line[0].find(")")])
                            # get (clamped_part_material, thickness)
                            tmp_cp_str = tmp_line[1].replace('[','').replace(']','').split(',')
                            self.clamped_parts.update({cp_nmbr : (tmp_cp_str[0].strip(), float(tmp_cp_str[1]))})
                        line = fid.readline()
                elif line.lstrip()[0:15]=="*FOS_DEFINITION":
                    line = fid.readline()
                    # loop through FOS-definition block
                    while line.lstrip()[0:19]!="*FOS_DEFINITION_END":
                        tmp_line = self._proc_line(line) # process inp-file line
                        if tmp_line[0]=="*FOS_Y":
                            self.fos_y = float(tmp_line[1])
                        elif tmp_line[0]=="*FOS_U":
                            self.fos_u = float(tmp_line[1])
                        elif tmp_line[0]=="*FOS_SLIP":
                            self.fos_slip = float(tmp_line[1])
                        elif tmp_line[0]=="*FOS_GAP":
                            self.fos_gap = float(tmp_line[1])
                        line = fid.readline()
                elif line.lstrip()[0:21]=="*BOLT_LOAD_DEFINITION":
                    line = fid.readline()
                    # loop through bolt-load-definition block
                    while line.lstrip()[0:25]!="*BOLT_LOAD_DEFINITION_END":
                        # load-ID, axial-force, lateral-force-1, lateral-force-2 (optional)
                        tmp_line = line.split()
                        if len(tmp_line)==4: # optional lat-force-2 used
                            self.bolt_loads.update({tmp_line[0] : (float(tmp_line[1]), float(tmp_line[2]), float(tmp_line[3]))})
                        elif len(tmp_line)==3: # optional lat-force-2 NOT used
                            self.bolt_loads.update({tmp_line[0] : (float(tmp_line[1]), float(tmp_line[2]), 0.0)})
                        line = fid.readline()

                line = fid.readline()

    # process commented input file line
    def _proc_line(self, line):
        # delete preceding whitespaces; replace comment chr and split string
        tmp = line.lstrip().replace('#', '=').split('=')
        return [tmp[0].strip(), tmp[1].strip()]

    # print function of input file
    # DEBUGGING function
    def print(self):
        print("*PROJECT_NAME:               {0:^}".format(self.project_name))
        print("*METHOD:                     {0:^}".format(self.method))
        print("*JOINT_TYPE:                 {0:^}".format(str(self.joint_type)))
        print("*BOLT_SIZE:                  {0:^}".format(self.bolt_size))
        print("*BOLT_MATERIAL:              {0:^}".format(self.bolt_material))
        print("*COF_CLAMP:                  {0:^}".format(str(self.cof_clamp)))
        print("*COF_BOLT:                   {0:^}".format(str(self.cof_bolt)))
        print("*TIGHT_TORQUE:               {0:^}".format(str(self.tight_torque)))
        print("*BOLT_HEAD_TYPE:             {0:^}".format(self.bolt_head_type))
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
