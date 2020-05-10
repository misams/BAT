from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt

class LoadTableModel(QtCore.QAbstractTableModel):

    header_labels = ["Bolt ID /\nLoadcase", "FA\n[N]", "FQ-1\n[N]", "FQ-2\n[N]"]

    def __init__(self, data, parent=None):
        super(LoadTableModel, self).__init__(parent)
        self._data = self.convertDictToArray(data)

    def data(self, index, role):
        if role == Qt.DisplayRole:
            # See below for the nested-list data structure.
            # .row() indexes into the outer list,
            # .column() indexes into the sub-list
            return self._data[index.row()][index.column()]

    def rowCount(self, index):
        # The length of the outer list.
        return len(self._data)

    def columnCount(self, index):
        # The following takes the first sub-list, and returns
        # the length (only works if all rows are an equal length)
        return len(self._data[0])

    # convert bolt-load-dict to 2D-array
    def convertDictToArray(self, load_dict):
        bolt_load_array = []
        for key, value in load_dict.items():
            bolt_load_array.append([key, value[0], value[1], value[2]])
        return bolt_load_array

    # set column headers
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.header_labels[section]
        return QtCore.QAbstractTableModel.headerData(self, section, orientation, role)

    #def flags(self, index):
    #    return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable
