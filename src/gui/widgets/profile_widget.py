"""
Profile management widget for the IR Remote Configuration Tool.

This widget handles profile creation, editing, and management operations.
It provides an interface for working with multiple remote profiles.
"""

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QComboBox,
    QTextEdit,
    QTableWidget,
    QLineEdit,
    QFormLayout,
)


class ProfileWidget(QWidget):
    """Widget for managing profiles"""

    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        profile_group = QGroupBox("Profile Management")
        profile_layout = QHBoxLayout()

        self.profile_combo = QComboBox()
        self.new_profile_btn = QPushButton("New Profile")
        self.delete_profile_btn = QPushButton("Delete Profile")
        self.save_profile_btn = QPushButton("Save Profile")

        profile_layout.addWidget(QLabel("Profile:"))
        profile_layout.addWidget(self.profile_combo)
        profile_layout.addWidget(self.new_profile_btn)
        profile_layout.addWidget(self.delete_profile_btn)
        profile_layout.addWidget(self.save_profile_btn)
        profile_group.setLayout(profile_layout)

        details_group = QGroupBox("Profile Details")
        details_layout = QFormLayout()

        self.profile_name_edit = QLineEdit()
        self.profile_description_edit = QTextEdit()
        self.profile_description_edit.setMaximumHeight(80)

        details_layout.addRow("Name:", self.profile_name_edit)
        details_layout.addRow("Description:", self.profile_description_edit)
        details_group.setLayout(details_layout)

        remotes_group = QGroupBox("Active Remotes")
        remotes_layout = QVBoxLayout()

        self.remotes_list = QTableWidget()
        self.remotes_list.setColumnCount(3)
        self.remotes_list.setHorizontalHeaderLabels(["Remote Name", "Brand", "Actions"])

        remotes_layout.addWidget(self.remotes_list)
        remotes_group.setLayout(remotes_layout)

        layout.addWidget(profile_group)
        layout.addWidget(details_group)
        layout.addWidget(remotes_group)

        self.setLayout(layout)
