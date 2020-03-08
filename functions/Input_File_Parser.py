import csv

class Input_File_Parser:
    def __init__(self, input_file):
        # input file path
        self.input_file = input_file
        # input file values
        self.project_name = ""
        self.method = ""
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
        # read input file and process
        self.read_input_file()

    # read input file and process data
    def read_input_file(self):
        print("Read and process input file:\n")
        with open(self.input_file) as fid:
            line = fid.readline() # first line in file
            while line: # loop through input-file
                if line.lstrip()[0:13]=="*PROJECT_NAME":
                    self.project_name = self.__proc_line(line)[1]
                elif line.lstrip()[0:7]=="*METHOD":
                    self.method = self.__proc_line(line)[1]
                elif line.lstrip()[0:16]=="*BOLT_DEFINITION":
                    line = fid.readline()
                    # loop through bolt-definition block
                    while line.lstrip()[0:20]!="*BOLT_DEFINITION_END":
                        tmp_line = self.__proc_line(line) # process inp-file line
                        if tmp_line[0]=="*JOINT_TYPE":
                            self.joint_type = tmp_line[1]
                        elif tmp_line[0]=="*BOLT_SIZE":
                            self.bolt_size = tmp_line[1]
                        elif tmp_line[0]=="*BOLT_MATERIAL":
                            self.bolt_material = tmp_line[1]
                        elif tmp_line[0]=="*COF_CLAMP":
                            self.cof_clamp = tmp_line[1]
                        elif tmp_line[0]=="*COF_BOLT":
                            self.cof_bolt = tmp_line[1]

                        line = fid.readline()
                line = fid.readline()

    # process commented input file line
    def __proc_line(self, line):
        # delete preceding whitespaces; replace comment chr and split string
        tmp = line.lstrip().replace('#', '=').split('=')
        return [tmp[0].strip(), tmp[1].strip()]

    # redefine string-output for print()
    # DEBUGGING function
    def print(self):
        print("*PROJECT_NAME:   {0:^}".format(self.project_name))
        print("*METHOD:         {0:^}".format(self.method))
        print("*JOINT_TYPE:     {0:^}".format(self.joint_type))
        print("*BOLT_SIZE:      {0:^}".format(self.bolt_size))
        print("*BOLT_MATERIAL:  {0:^}".format(self.bolt_material))
        print("*COF_CLAMP:      {0:^}".format(self.cof_clamp))
        print("*COF_BOLT:       {0:^}".format(str(self.cof_bolt)))

