from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
"""
Material-Info-Window
"""
class MatInfoWindow(QWidget):
    def __init__(self, materials=None):
        super(MatInfoWindow, self).__init__()
        #
        # material database
        self.materals = materials
        # set window title
        self.setWindowTitle("Material Data Info")
        # set layout and add widgets
        layout = QVBoxLayout()
        label = QLabel("BAT Material Database: {0:^}".format(str(self.materals.mat_file)))
        mat_table = QTableWidget()
        layout.addWidget(label)
        layout.addWidget(mat_table)
        self.setLayout(layout)
        self.resize(800, 500) # resize window
        #
        # fill and format material table
        mat_table.setColumnCount(7) # init material-info-table
        mat_table.setHorizontalHeaderLabels(\
            ["Material-ID", "Young's\nModulus\n[MPa]", "Ultimate\nStrength\n[MPa]", "Yield\nStrength\n[MPa]",\
             "CTE\n\n[1/K]", "Ultimate\nShear Strength\n[MPa]", "Yield\nShear Strength\n[MPa]"])
        mat_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        # fill table
        for i, value in enumerate(self.materals.materials.values()):
            mat_table.insertRow(i)
            mat_table.setItem(i, 0, QTableWidgetItem(value.name))
            mat_table.setItem(i, 1, QTableWidgetItem("{0:.0f}".format(value.E)))
            mat_table.setItem(i, 2, QTableWidgetItem("{0:.1f}".format(value.sig_u)))
            mat_table.setItem(i, 3, QTableWidgetItem("{0:.1f}".format(value.sig_y)))
            mat_table.setItem(i, 4, QTableWidgetItem("{0:.3e}".format(value.alpha)))
            mat_table.setItem(i, 5, QTableWidgetItem("{0:.1f}".format(value.tau_u)))
            mat_table.setItem(i, 6, QTableWidgetItem("{0:.1f}".format(value.tau_y)))
        # not editable
        mat_table.setEditTriggers(QTableWidget.NoEditTriggers)
        # close window button
        Quit = QPushButton('Close', self) #button object
        Quit.setGeometry(10, 10, 60, 35) # Set the position and size of the button
        Quit.setStyleSheet("font-weight: bold") # Set the style and color of the button
        Quit.clicked.connect(self.close) # Close the window after clicking the button
        layout.addWidget(Quit)