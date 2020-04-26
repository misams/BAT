#! /usr/bin/env python
#  -*- coding: utf-8 -*-
#
# Works ONLY with Python 3.0+
#
# Support module generated by PAGE version 5.0.3
#  in conjunction with Tcl version 8.6
#    Apr 25, 2020 10:31:34 AM CEST  platform: Linux

import sys
import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog
import tkinter.ttk as ttk
from src.functions.InputFileParser import InputFileParser

def set_Tk_var():
    global combo_clamp_mat
    combo_clamp_mat = tk.StringVar()
    global combo_shim
    combo_shim = tk.StringVar()
    global combo_shim_mat
    combo_shim_mat = tk.StringVar()
    global cheVal_DA
    cheVal_DA = tk.IntVar()
    global cheVal_use_shim
    cheVal_use_shim = tk.IntVar()
    global spinbox_nmbr_shear_planes
    spinbox_nmbr_shear_planes = tk.StringVar()
    global use_shim
    use_shim = tk.IntVar()
    global combo_bolt
    combo_bolt = tk.StringVar()
    global combo_bolt_mat
    combo_bolt_mat = tk.StringVar()
    global joint_mos_type
    joint_mos_type = tk.IntVar()
    global locking_device
    locking_device = tk.IntVar()
    global method_sel
    method_sel = tk.IntVar()
    global selectedButton
    selectedButton = tk.IntVar()
    global combobox
    combobox = tk.StringVar()

def init(top, gui, *args, **kwargs):
    global w, top_level, root, materials, bolts
    w = gui
    top_level = top
    root = top
    # args[0]: materials
    materials = args[0]
    # args[1]: bolts
    bolts = args[1]
    # init gui with the default settings
    init_config()

# set the gui with the default settings
def init_config():
    w.Radiobutton_Esapss.select()
    w.Radiobutton_ECSS.configure(state = "disabled")
    w.Radiobutton_VDI2230.configure(state = "disabled")
    w.Radiobutton_Jt_min.select()
    w.Radiobutton_Jt_mean.configure(state="disabled")
    w.Radiobutton_Lock_No.select()
    w.Entry_Prevailing_Torque.configure(state = "disabled")
    w.Entry_Loading_Plane_Factor.insert(0, "0.5")
    # fill bolts combo-box
    bolt_combo = []
    for key in bolts.bolts:
        bolt_combo.append(key)
    w.TCombobox_Bolt["value"] = bolt_combo
    # fill bolt-material combo-box
    mat_combo = []
    for key in materials.materials:
        mat_combo.append(key)
    w.TCombobox_Bolt_Material["value"] = mat_combo
    w.TCombobox_cp_mat["value"] = mat_combo
    w.TCombobox_shim_mat["value"] = mat_combo
    # set default FOS values
    w.Entry_fos_y.insert(0, "1.1")
    w.Entry_fos_u.insert(0, "1.25")
    w.Entry_fos_slip.insert(0, "1.1")
    w.Entry_fos_gap.insert(0, "1.0")
    # clamped parts
    spinbox_nmbr_shear_planes.set(1)
    w.Checkbutton_use_shim.select()
    # fill shim combo-box
    shim_combo = []
    for key in bolts.washers:
        shim_combo.append(key)
    w.TCombobox_shim["value"] = shim_combo
    # deactivate up and down button
    w.Button_cp_down.configure(state="disabled")
    w.Button_cp_up.configure(state="disabled")


# method selection radio-buttons
# not implemented yet
def radio_ecss(p1): pass
def radio_esapss(p1): pass
def radio_vdi2230(p1): pass

# locking device radio-buttons
def locking_device_no(p1):
    w.Entry_Prevailing_Torque.configure(state = "disabled")
def locking_device_yes(p1):
    w.Entry_Prevailing_Torque.configure(state = "normal")

# exit BAT via File-Exit
def quit_menu():
    print("BAT GUI closed...ciau!")
    root.quit()

# Info
def info_menu():
    messagebox.showinfo("BAT GUI Info",\
        "BAT GUI designed with Tkinter\nand PAGE version 5.0.3\n\n" +\
        "Works only with Python 3.0+\n\nGUI v0.1 by Michael Sams")

# erase all entry fields - reset
# execute before reading input file
def erase_all_entries():
    w.Entry_project_name.delete(0, tk.END)
    w.Entry_cof_clamp.delete(0, tk.END)
    w.Entry_Cof_Head_Max.delete(0, tk.END)
    w.Entry_Cof_Head_Min.delete(0, tk.END)
    w.Entry_Cof_Thread_Max.delete(0, tk.END)
    w.Entry_Cof_Thread_Min.delete(0, tk.END)
    w.Entry_cp_thk.delete(0, tk.END)
    w.Entry_fos_gap.delete(0, tk.END)
    w.Entry_fos_slip.delete(0, tk.END)
    w.Entry_fos_u.delete(0, tk.END)
    w.Entry_fos_y.delete(0, tk.END)
    w.Entry_Loading_Plane_Factor.delete(0, tk.END)
    w.Entry_Prevailing_Torque.delete(0, tk.END)
    w.Entry_subst_da.delete(0, tk.END)
    w.Entry_throughhole_diameter.delete(0, tk.END)
    w.Entry_Tight_Torque.delete(0, tk.END)
    w.Entry_Torque_Tol.delete(0, tk.END)
    w.Listbox_clamped_parts.delete(0, tk.END)

# *.inp file open and GUI filling
def open_inp_menu():
    inp_path = filedialog.askopenfilename(filetypes=[("BAT Input Files", "*.inp")])
    if inp_path:
        # erase all entry fields
        erase_all_entries()
        # open and process input file
        inp_file_opened = InputFileParser(inp_path)
        # fill GUI
        if inp_file_opened.method == "ESAPSS":
            w.Radiobutton_Esapss.select()
        else:
            print("Method NOT implemented yet...")
        w.Entry_project_name.insert(0, inp_file_opened.project_name)
        # *BOLT_DEFINITION
        if inp_file_opened.joint_mos_type == "min":
            w.Radiobutton_Jt_min.select()
        else:
            print("MEAN *JOINT_MOS_TYPE NOT implemented yet...")
        for i, key in enumerate(bolts.bolts):
            if key == inp_file_opened.bolt:
                w.TCombobox_Bolt.current(i) 
        for i, key in enumerate(materials.materials):
            if key == inp_file_opened.bolt_material:
                w.TCombobox_Bolt_Material.current(i)
        # [mu_head_max, mu_thread_max, mu_head_min, mu_thread_min]
        w.Entry_Cof_Head_Max.insert(0, inp_file_opened.cof_bolt[0])
        w.Entry_Cof_Thread_Max.insert(0, inp_file_opened.cof_bolt[1])
        w.Entry_Cof_Head_Min.insert(0, inp_file_opened.cof_bolt[2])
        w.Entry_Cof_Thread_Min.insert(0, inp_file_opened.cof_bolt[3])
        w.Entry_Tight_Torque.insert(0, inp_file_opened.tight_torque)
        w.Entry_Torque_Tol.insert(0, inp_file_opened.torque_tol_tight_device)
        if inp_file_opened.locking_mechanism == "yes":
            w.Radiobutton_Lock_Yes.select()
            w.Entry_Prevailing_Torque.configure(state = "normal")
            w.Entry_Prevailing_Torque.insert(0, inp_file_opened.prevailing_torque)
        else:
            w.Radiobutton_Lock_No.select()
            w.Entry_Prevailing_Torque.configure(state = "disabled")
        w.Entry_Loading_Plane_Factor.delete(0, tk.END)
        w.Entry_Loading_Plane_Factor.insert(0, inp_file_opened.loading_plane_factor)
        # *CLAMPED_PARTS_DEFINITION
        w.Entry_cof_clamp.insert(0, inp_file_opened.cof_clamp)
        spinbox_nmbr_shear_planes.set(inp_file_opened.nmbr_shear_planes)
        w.Entry_throughhole_diameter.insert(0, inp_file_opened.through_hole_diameter)
        if inp_file_opened.subst_da == "no":
            w.Checkbutton_DA.select()
            w.Entry_subst_da.configure(state="disabled")
        else:
            w.Checkbutton_DA.deselect()
            w.Entry_subst_da.configure(state="normal")
            w.Entry_subst_da.insert(0, inp_file_opened.subst_da)
        # add shim
        if inp_file_opened.use_shim != "no":
            for i, key in enumerate(bolts.washers):
                if key == inp_file_opened.use_shim[1]:
                    w.TCombobox_shim.current(i) 
            for i, key in enumerate(materials.materials):
                if key == inp_file_opened.use_shim[0]:
                    w.TCombobox_shim_mat.current(i)
            # add shim to clamped parts listbox
            shim_text = "Shim / CP(0): {0:<20} thk. = {1:>10.2f} mm".format(\
                inp_file_opened.use_shim[1], bolts.washers[inp_file_opened.use_shim[1]].h)
            w.Listbox_clamped_parts.insert(0, shim_text)
        # add clamped parts
        for i, cp in inp_file_opened.clamped_parts.items():
            cp_text = "       CP({0:d}): {1:<20} thk. = {2:>10.2f} mm".format(i, cp[0], cp[1])
            w.Listbox_clamped_parts.insert(i, cp_text)

        # set Factors of Safety
        w.Entry_fos_y.insert(0, inp_file_opened.fos_y)
        w.Entry_fos_u.insert(0, inp_file_opened.fos_u)
        w.Entry_fos_slip.insert(0, inp_file_opened.fos_slip)
        w.Entry_fos_gap.insert(0, inp_file_opened.fos_gap)

    else:
        # fpath is empty string
        print("No BAT input file opened.")

# handle auto-DA checkbox
def auto_da_checkbox(p1):
    if cheVal_DA.get() == 1:
        w.Entry_subst_da.configure(state = "normal")
    else:
        w.Entry_subst_da.configure(state = "disabled")

# handle use-shim checkbox
def use_shim_checkbox(p1):
    if cheVal_use_shim.get() == 0:
        w.TCombobox_shim.configure(state = "normal")
        w.TCombobox_shim_mat.configure(state = "normal")
    else:
        w.TCombobox_shim.configure(state = "disabled")
        w.TCombobox_shim_mat.configure(state = "disabled")

# add clamped-part button
def button_add_cp(p1):
    # read clamped-part definition 
    sel_cp_mat = w.TCombobox_cp_mat.get() # get CP material
    cp_thk = w.Entry_cp_thk.get() # get CP thickness
    # read shim definition
    sel_shim = w.TCombobox_shim.get()
    sel_shim_mat = w.TCombobox_shim_mat.get()
    try:
        # check if clamped-part material and thickness is defined
        if sel_cp_mat and cp_thk:
            # check if listbox is empty
            if not w.Listbox_clamped_parts.get(0, "end"):
                # TODO: shitty solution?!
                if cheVal_use_shim.get() == 1 and sel_shim and sel_shim_mat:
                    # add shim to clamped parts listbox
                    shim_text = "Shim / CP(0): {0:<20} thk. = {1:>10.2f} mm".format(\
                        sel_shim, bolts.washers[sel_shim].h)
                    w.Listbox_clamped_parts.insert(0, shim_text)
                last_cp_nmbr = 0
            # if not - use last listbox entry
            else:
                # get last listbox entry + id-nmbr
                w.Listbox_clamped_parts.selection_clear(0, "end")
                w.Listbox_clamped_parts.selection_set("end")
                last_cp = w.Listbox_clamped_parts.get(w.Listbox_clamped_parts.curselection())
                last_cp_nmbr = int(last_cp[last_cp.find("(")+1:last_cp.find(")")])
            # add defined clamp-part to end of listbox
            cp_text = "       CP({0:d}): {1:<20} thk. = {2:>10} mm".format(\
                last_cp_nmbr+1, sel_cp_mat, cp_thk)
            w.Listbox_clamped_parts.insert(last_cp_nmbr+1, cp_text)
        else:
            print("Error: No clamp-material and/or thickness defined.")
    except ValueError as e:
        print("Error: " + str(e))
        print("Define a number for clamp-part thickness (not a string)!")
    except tk.TclError as e:
        print("Error: " + str(e))

# delete listbox entry / clamped-part
def button_delete_cp(p1):
    # check if listbox is NOT empty and any selection is active
    if w.Listbox_clamped_parts.get(0, "end") and w.Listbox_clamped_parts.curselection():
        # current selection
        sel_cp = w.Listbox_clamped_parts.get(w.Listbox_clamped_parts.curselection())
        # check if shim is in list
        if "Shim" in sel_cp and cheVal_use_shim.get()==1:
            print("Shim cannot be deleted!")
        else:
            # get all clamped parts (complete list)
            all_cps = w.Listbox_clamped_parts.get(0, "end")
            # erase listbox
            w.Listbox_clamped_parts.delete(0, "end")
            # modified clamp-part list and delete selcted entry
            id_chg = 0 # id-changer
            for cp in all_cps:
                # use if CP(0) not selected
                if cp == sel_cp and "Shim" not in sel_cp:
                    id_chg = 1
                    continue
                # use if CP(0) selected and checkbox inactive
                elif cp == sel_cp and "Shim" in sel_cp:
                    continue
                # clamp-part id
                cp_nmbr = int(cp[cp.find("(")+1:cp.find(")")]) - id_chg
                cp_first = cp.split('(')[0]
                cp_last = cp.split(')')[1]
                cp_text = cp_first + '(' + str(cp_nmbr) + ')' + cp_last
                # add clamped-parts (w/o deleted entry) and modified id
                w.Listbox_clamped_parts.insert("end", cp_text)

# not implemented yet
def button_down_cp(p1): pass
def button_up_cp(p1): pass

def destroy_window():
    # Function which closes the window.
    global top_level
    top_level.destroy()
    top_level = None
