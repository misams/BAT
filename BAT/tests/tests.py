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

    """
    TEST --> ECSS-E-HB-32-23A
    """
    # working example chapter 7.14
    ecss_test_inp = os.path.dirname( __file__ )+"/ECSS_WorkEx_714.inp"
    inp_file = fp.InputFileParser(ecss_test_inp, bolts)
    ana_ecss = ecss.Ecss(inp_file, materials, bolts, "TEST")
    # print test results
    print("#\n# BAT ECSS Working Example §7.14 TEST-RESULTS\n#")
    print("fastener compliance:      {0:.3e} mm/N".format(ana_ecss.delta_b))
    print("clamped parts compliance: {0:.3e} mm/N".format(ana_ecss.delta_c))
    print("force ratio PHI:          {0:.3f}".format(ana_ecss.Phi))
    print("Torque incl. Mp:          {0:.2f} Nm".format(ana_ecss.inp_file.tight_torque))
    print("Torque wrench scatter: +/-{0:^} Nm".format(ana_ecss.inp_file.torque_tol_tight_device))
    print("Prevailing torque Mp:     {0:.2f} / {1:.2f} Nm".format(\
        ana_ecss.inp_file.prevailing_torque[0], ana_ecss.inp_file.prevailing_torque[1]))
    print("F_M_min:                  {0:.1f} N".format(ana_ecss.F_M[0])) # 5717.85N FM_min p.106
    print("F_M_max:                  {0:.1f} N".format(ana_ecss.F_M[1])) # 12078.55N FM_max p.105
    print("F_V_max:                  {0:.1f} N".format(ana_ecss.F_V[1]))
    #
    # THERMAL PRELOAD LOSS
    #
    # method ECSS §6.3.5; equ.[6.3.27]
    # 
    a_L = 0.0
    for _, c in ana_ecss.inp_file.clamped_parts.items():
        a_L += ana_ecss.materials.materials[c[0]].alpha * c[1]
    a_L = (a_L - ana_ecss.used_bolt_mat.alpha * ana_ecss.l_K) / ana_ecss.l_K
    F_th_ecss1 = a_L * ana_ecss.inp_file.delta_t * ana_ecss.used_bolt_mat.E *\
        ana_ecss.used_bolt.A3 * (1-ana_ecss.Phi) # with Asm = A3 as defined in ECSS
    A_sm = ana_ecss.l_K/ana_ecss.delta_b/ana_ecss.used_bolt_mat.E 
    F_th_ecss2 = a_L * ana_ecss.inp_file.delta_t * ana_ecss.used_bolt_mat.E *\
        A_sm * (1-ana_ecss.Phi) # with Asm acc. to delta_b; equal to VDI
    print("F_th ECSS_A3:             {0:.2f} N".format(F_th_ecss1))
    print("F_th ECSS_Asm:            {0:.2f} N".format(F_th_ecss2))
    #
    # method VDI §5.4.2.3; equ.[118]
    F_th_VDI = ana_ecss.l_K*(ana_ecss.used_bolt_mat.alpha -\
        ana_ecss.materials.materials["AL7075ECSSTEST"].alpha)*ana_ecss.inp_file.delta_t /\
            (ana_ecss.delta_b+ana_ecss.delta_c)
    print("F_th VDI:                 {0:.2f} N".format(F_th_VDI))
    print("F_th SHM:                [{0:.2f}, {1:.2f}] N".format(ana_ecss.dF_V_th[0], ana_ecss.dF_V_th[1]))
    #
    # stress
    #
    print("Sig_n:                   [{0:.1f}, {1:.1f}] N".format(ana_ecss.sig_n[0], ana_ecss.sig_n[1]))
    print("Tau:                     [{0:.1f}, {1:.1f}] N".format(ana_ecss.tau[0], ana_ecss.tau[1]))
    print("Sig_v:                   [{0:.1f}, {1:.1f}] N".format(ana_ecss.sig_v[0], ana_ecss.sig_v[1]))
    print("MOS_slip_loc:             {0:.2f}".format(ana_ecss.bolt_results['Bolt-1'][4]))
    print("MOS_slip_global:          {0:.2f}".format(ana_ecss.MOS_glob_slip))

    #ana_ecss.print_results()

if __name__ == '__main__':
    tests()