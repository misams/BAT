import sys
import os.path
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
from pathlib import Path
import src.functions.InputFileParser as fp
import src.functions.MaterialManager as mat
import src.functions.BoltManager as bm
import src.Ecss as ecss

def tests():
    # database-dir: "../BAT/BAT/db"
    p = os.path.join(Path(__file__).parents[1],'db')
    # read and process material-database files
    materials = mat.MaterialManager(p+"/materials.mat")

    # handle bolt db files - read all available bolts and washers
    bolts = bm.BoltManager(p)

    # calc ECSS-E-HB-32-23A
    ecss_test_inp = os.path.dirname( __file__ )+"/ECSS_WorkEx_714.inp"
    inp_file = fp.InputFileParser(ecss_test_inp, bolts)
    ana_ecss = ecss.Ecss(inp_file, materials, bolts, "TEST")
    # print test results
    print("#\n# BAT ECSS Working Example §7.14 TEST-RESULTS\n#")
    print("fastener compliance:      {0:.3e} mm/N".format(ana_ecss.delta_b))        
    print("clamped parts compliance: {0:.3e} mm/N".format(ana_ecss.delta_c))
    print("force ratio PHI:          {0:.3f} mm/N".format(ana_ecss.Phi))
    print("Torque incl. Mp:          {0:.2f} mm/N".format(ana_ecss.inp_file.tight_torque))
    print("Torque wrench scatter: +/-{0:.2f} mm/N".format(ana_ecss.inp_file.torque_tol_tight_device))
    print("Prevailing torque Mp:     {0:.2f} mm/N".format(ana_ecss.inp_file.prevailing_torque))
    print("F_M_min:                  {0:.1f} mm/N".format(ana_ecss.F_M[0]))
    print("F_M_max:                  {0:.1f} mm/N".format(ana_ecss.F_M[1]))
    print("F_V_max:                  {0:.1f} mm/N".format(ana_ecss.F_V[1]))
    print(ana_ecss.A_sub)

    #ana_ecss.print_results()

if __name__ == '__main__':
    tests()