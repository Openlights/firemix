from PySide import QtCore, QtGui

from ui.ui_dlg_setup_networking import Ui_DlgSetupNetworking


class DlgSetupNetworking(QtGui.QDialog, Ui_DlgSetupNetworking):

    def __init__(self, parent=None):
        super(DlgSetupNetworking, self).__init__(parent)
        self.playlist = parent._app.playlist
        self.setupUi(self)
        self.app = parent._app

        self.btn_add_client.clicked.connect(self.add_client_row)
        self.btn_del_client.clicked.connect(self.del_client_row)
        self.tbl_clients.itemChanged.connect(self.validate_client_table_item)

        self.port_validator = QtGui.QIntValidator(1, 65535, self)
        ip_regex = QtCore.QRegExp(r"(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)")
        self.ip_validator = QtGui.QRegExpValidator(ip_regex, self)

        self.populate_clients_table()

    def validate(self):
        for row in range(self.tbl_clients.rowCount()):
            for col in range(self.tbl_clients.columnCount()):
                if not self.validate_client_table_item(self.tbl_clients.item(row, col)):
                    print self.tbl_clients.item(row, col).text(), "failed validation"
                    return False
        return True

    def validate_client_table_item(self, item):
        if item is None:
            return True
        valid = None
        if item.column() == 0:  # IP address
            valid, _, _ = self.ip_validator.validate(item.text(), 0)
        elif item.column() == 1:  # Port
            valid, _, _ = self.port_validator.validate(item.text(), 0)
        else:
            return True

        if valid == QtGui.QValidator.Invalid:
            item.setBackground(QtGui.QColor(255, 200, 200))
        elif valid == QtGui.QValidator.Intermediate:
            item.setBackground(QtGui.QColor(255, 255, 200))
        else:
            item.setBackground(QtGui.QColor(255, 255, 255))

        return (valid == QtGui.QValidator.Acceptable)

    def accept(self):
        if self.validate():
            QtGui.QDialog.accept(self)

    def populate_clients_table(self):
        clients = self.app.settings['networking']['clients']
        self.tbl_clients.setRowCount(len(clients))
        for i, client in enumerate(clients):
            item_ip = QtGui.QTableWidgetItem(client["ip"])
            item_port = QtGui.QTableWidgetItem(str(client["port"]))
            item_enabled = QtGui.QCheckBox()
            if client["enabled"]:
                item_enabled.setCheckState(QtCore.Qt.Checked)
            self.tbl_clients.setItem(i, 0, item_ip)
            self.tbl_clients.setItem(i, 1, item_port)
            self.tbl_clients.setCellWidget(i, 2, item_enabled)
        self.tbl_clients.horizontalHeader().setResizeMode(0, QtGui.QHeaderView.Stretch)

    def add_client_row(self):
        pass

    def del_client_row(self):
        pass