import sys
import json
from utils import resource_path
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QListWidget, QVBoxLayout, QHBoxLayout, QCompleter,
    QSpinBox, QGroupBox, QScrollArea,
    QTableWidget, QTableWidgetItem
)
from PyQt5.QtCore import Qt
from ryze import solve
from PyQt5.QtWidgets import QHeaderView
DEFAULT_BANNED_CHAMPIONS = [
    "Aatrox",
    "Aphelios",
    "Zoe",
    "Leona",
    "Diana",
    "Aurelion Sol"
]
DEFAULT_FORCED_CHAMPIONS = [
    "Ryze",
    "Ahri"
]

AUTO_IGNORE_TRAITS = {"Targon"}  # luôn ignore


class TFTTool(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TFT Flex Tool")
        self.setGeometry(200, 200, 1200, 550)

        self.champion_names = self.load_champions()
        self.traits = self.load_traits()

        self.init_ui()
        self.load_default_forced()
        self.load_default_banned()

    def load_default_banned(self):
        banned_list = self.list_banned["list"]

        for name in DEFAULT_BANNED_CHAMPIONS:
            if name in self.champion_names:
                banned_list.addItem(name)

    def load_default_forced(self):
        forced_list = self.list_forced["list"]

        for name in DEFAULT_FORCED_CHAMPIONS:
            if name in self.champion_names:
                forced_list.addItem(name)

    # ===== LOAD DATA =====
    def load_champions(self):
        with open(resource_path("data/champions.json"), encoding="utf-8") as f:
            raw = json.load(f)
        return sorted(c["name"] for c in raw)

    def load_traits(self):
        with open(resource_path("data/traits.json"), encoding="utf-8") as f:
            return json.load(f)

    # ===== UI =====
    def init_ui(self):
        main_layout = QHBoxLayout(self)

        # ===== LEFT: FORCED / BANNED =====
        left_layout = QHBoxLayout()

        self.list_forced = self.build_champion_box("Forced Champions")
        self.list_banned = self.build_champion_box("Banned Champions")

        left_layout.addLayout(self.list_forced["layout"])
        left_layout.addLayout(self.list_banned["layout"])

        # ===== MIDDLE: SETTINGS + EMBLEM =====
        middle_layout = QVBoxLayout()

        # SETTINGS
        settings_box = QGroupBox("Solver Settings")
        settings_layout = QVBoxLayout()

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Max Team Size"))
        self.spin_max_size = QSpinBox()
        self.spin_max_size.setRange(1, 12)
        self.spin_max_size.setValue(8)
        row1.addStretch()
        row1.addWidget(self.spin_max_size)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Time Limit (seconds)"))
        self.spin_time_limit = QSpinBox()
        self.spin_time_limit.setRange(1, 60)
        self.spin_time_limit.setValue(20)
        row2.addStretch()
        row2.addWidget(self.spin_time_limit)

        settings_layout.addLayout(row1)
        settings_layout.addLayout(row2)
        settings_box.setLayout(settings_layout)

        # EMBLEM EDITOR
        emblem_box = QGroupBox("Emblem Editor")
        emblem_layout = QVBoxLayout()

        self.emblem_spinboxes = {}

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        inner = QWidget()
        inner_layout = QVBoxLayout(inner)

        for trait in self.traits:
            row = QHBoxLayout()
            lbl = QLabel(trait)
            spin = QSpinBox()
            spin.setRange(0, 5)
            spin.setFixedWidth(60)

            self.emblem_spinboxes[trait] = spin

            row.addWidget(lbl)
            row.addStretch()
            row.addWidget(spin)
            inner_layout.addLayout(row)

        scroll.setWidget(inner)
        emblem_layout.addWidget(scroll)
        emblem_box.setLayout(emblem_layout)

        middle_layout.addWidget(settings_box)
        middle_layout.addWidget(emblem_box)

        # ===== RIGHT: RESULT TABLE =====
        right_layout = QVBoxLayout()

        btn_run = QPushButton("Run Solver")
        btn_run.clicked.connect(self.run_solver_real)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels([
            "Team",
            "Traits",
            "Team Size",
            "Time Limit"
        ])
        # ---- CẤU HÌNH HIỂN THỊ BẢNG (QUAN TRỌNG) ----
        self.table.setWordWrap(True)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)

        right_layout.addWidget(btn_run)
        right_layout.addWidget(self.table)

        # ===== MERGE =====
        main_layout.addLayout(left_layout, 3)
        main_layout.addLayout(middle_layout, 2)
        main_layout.addLayout(right_layout, 4)

    # ===== COMPONENTS =====
    def build_champion_box(self, title):
        layout = QVBoxLayout()
        layout.addWidget(QLabel(title))

        input_box = QLineEdit()
        input_box.setPlaceholderText("Gõ tên tướng...")
        layout.addWidget(input_box)

        btn = QPushButton("Add")
        layout.addWidget(btn)

        list_widget = QListWidget()
        layout.addWidget(list_widget)

        completer = QCompleter(self.champion_names)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        input_box.setCompleter(completer)

        btn.clicked.connect(lambda: self.add_item(input_box, list_widget))
        list_widget.itemDoubleClicked.connect(
            lambda item: list_widget.takeItem(list_widget.row(item))
        )

        return {
            "layout": layout,
            "input": input_box,
            "list": list_widget
        }

    # ===== HELPERS =====
    def add_item(self, input_box, list_widget):
        name = input_box.text().strip()
        if name and name not in self.get_items(list_widget):
            list_widget.addItem(name)
        input_box.clear()

    def get_items(self, list_widget):
        return [list_widget.item(i).text() for i in range(list_widget.count())]

    # ===== MOCK RESULT =====
    def run_solver_real(self):
        try:
            # Xóa bảng cũ
            self.table.setRowCount(0)

            # Lấy dữ liệu từ GUI
            forced = self.get_items(self.list_forced["list"])
            banned = self.get_items(self.list_banned["list"])
            emblems = {t: spin.value() for t, spin in self.emblem_spinboxes.items() if spin.value() > 0}

            print("=== GUI INPUT ===")
            print("Forced:", forced)
            print("Banned:", banned)
            print("Emblems:", emblems)
            print("Max team size:", self.spin_max_size.value())
            print("Time limit:", self.spin_time_limit.value())

            # Gọi solver
            result = solve(
                max_team=self.spin_max_size.value(),
                time_limit=self.spin_time_limit.value(),
                forced=forced,
                banned=banned,
                emblems=emblems
            )

            print("=== SOLVER RESULT ===")
            for idx, team_info in enumerate(result):
                # Kiểm tra team_info có key 'team' không
                team = team_info.get("team", [])
                # Lọc các object hợp lệ có attribute name
                team_names = [c.name for c in team if hasattr(c, "name")]

                print(f"Team {idx + 1}: {team_names}, score: {team_info.get('score', 0)}")

                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(", ".join(team_names)))
                self.table.setItem(row, 1, QTableWidgetItem(str(team_info.get("score", 0))))
                self.table.setItem(row, 2, QTableWidgetItem(str(len(team_names))))
                self.table.setItem(row, 3, QTableWidgetItem(f"{self.spin_time_limit.value()}s"))

            if not result:
                print("Solver returned empty result!")

        except Exception as e:
            print("ERROR in run_solver_real:", e)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = TFTTool()
    win.show()
    sys.exit(app.exec())
