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
                # check for commands
                line = fid.readline()
