from PySide import QtCore, QtGui

from ui.ui_dlg_settings import Ui_DlgSettings


class DlgSettings(QtGui.QDialog, Ui_DlgSettings):

    def __init__(self, parent=None):
        super(DlgSettings, self).__init__(parent)
        self.playlist = parent._app.playlist
        self.setupUi(self)
        self.app = parent._app

        # Setup tree view
        self.tree_settings.itemClicked.connect(self.on_tree_changed)
        self.settings_stack.setCurrentIndex(0)

        # Setup events for all panes
        self.btn_networking_add_client.clicked.connect(self.add_networking_client_row)
        self.btn_networking_del_client.clicked.connect(self.del_networking_client_row)
        self.tbl_networking_clients.itemChanged.connect(self.validate_networking_client_table_item)

        self.port_validator = QtGui.QIntValidator(1, 65535, self)
        ip_regex = QtCore.QRegExp(r"(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)")
        self.ip_validator = QtGui.QRegExpValidator(ip_regex, self)

        # Setup validation and acceptance methods for all panes
        self.validators = [self.validate_networking]
        self.acceptors = [self.accept_networking]

        # Initialize settings panes
        self.populate_networking_clients_table()

    def on_tree_changed(self):
        self.settings_stack.setCurrentIndex(self.tree_settings.currentIndex().row())

    def validate(self):
        valid = True
        for validator in self.validators:
            if not validator():
                valid = False
        return valid

    def validate_networking(self):
        for row in range(self.tbl_networking_clients.rowCount()):
            for col in range(self.tbl_networking_clients.columnCount()):
                if not self.validate_networking_client_table_item(self.tbl_networking_clients.item(row, col)):
                    return False
        return True

    def validate_networking_client_table_item(self, item):
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
            item.setBackground(QtGui.QColor(255, 190, 190))
        elif valid == QtGui.QValidator.Intermediate:
            item.setBackground(QtGui.QColor(255, 255, 190))
        else:
            item.setBackground(QtGui.QColor(255, 255, 255))

        return (valid == QtGui.QValidator.Acceptable)

    def accept(self):
        if self.validate():
            for acceptor in self.acceptors:
                acceptor()

            QtGui.QDialog.accept(self)
        else:
            QtGui.QMessageBox(QtGui.QMessageBox.Warning, "FireMix", "Please correct all highlighted entries!").exec_()

    def accept_networking(self):
        clients = []
        for i in range(self.tbl_networking_clients.rowCount()):
            ip = self.tbl_networking_clients.item(i, 0).text()
            port = int(self.tbl_networking_clients.item(i, 1).text())
            enabled = (self.tbl_networking_clients.cellWidget(i, 2).checkState() == QtCore.Qt.Checked)
            client = {"ip": ip, "port": port, "enabled": enabled}
            if client not in clients:
                clients.append(client)
        self.app.settings['networking']['clients'] = clients

    def populate_networking_clients_table(self):
        clients = self.app.settings['networking']['clients']
        self.tbl_networking_clients.setRowCount(len(clients))
        for i, client in enumerate(clients):
            item_ip = QtGui.QTableWidgetItem(client["ip"])
            item_port = QtGui.QTableWidgetItem(str(client["port"]))
            item_enabled = QtGui.QCheckBox()
            if client["enabled"]:
                item_enabled.setCheckState(QtCore.Qt.Checked)
            self.tbl_networking_clients.setItem(i, 0, item_ip)
            self.tbl_networking_clients.setItem(i, 1, item_port)
            self.tbl_networking_clients.setCellWidget(i, 2, item_enabled)
        self.tbl_networking_clients.horizontalHeader().setResizeMode(0, QtGui.QHeaderView.Stretch)

    def add_networking_client_row(self):
        row = self.tbl_networking_clients.rowCount()
        self.tbl_networking_clients.insertRow(row)
        self.tbl_networking_clients.setItem(row, 0, QtGui.QTableWidgetItem(""))
        self.tbl_networking_clients.setItem(row, 1, QtGui.QTableWidgetItem("3020"))
        self.tbl_networking_clients.setCellWidget(row, 2, QtGui.QCheckBox())

    def del_networking_client_row(self):
        self.tbl_networking_clients.removeRow(self.tbl_networking_clients.currentRow())
