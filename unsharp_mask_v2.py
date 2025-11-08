from PyQt6 import QtWidgets, QtCore
import sirilpy as s
from sirilpy import SirilError
import tempfile, os, sys


class UnsharpMaskGUI(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Unsharp Mask v2")
        self.resize(300, 130)

        # Siril 接続
        self.siril = s.SirilInterface()
        try:
            self.siril.connect()
        except s.SirilConnectionError:
            QtWidgets.QMessageBox.critical(self, "エラー", "Siril に接続できません。Siril を起動してください。")
            sys.exit(1)

        # --- ウィジェット構成 ---
        layout = QtWidgets.QVBoxLayout(self)

        grid = QtWidgets.QGridLayout()
        layout.addLayout(grid)

        # Amount
        self.amount_label = QtWidgets.QLabel("Amount:")
        self.amount_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.amount_slider.setRange(0, 50)  # 0.0〜5.0 (0.1刻み)
        self.amount_spin = QtWidgets.QDoubleSpinBox()
        self.amount_spin.setRange(0.0, 5.0)
        self.amount_spin.setSingleStep(0.1)
        self.amount_spin.setDecimals(1)
        self.amount_spin.setValue(0.5)

        # Radius
        self.radius_label = QtWidgets.QLabel("Radius:")
        self.radius_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.radius_slider.setRange(1, 200)  # 0.1〜20.0 (0.1刻み)
        self.radius_spin = QtWidgets.QDoubleSpinBox()
        self.radius_spin.setRange(0.1, 20.0)
        self.radius_spin.setSingleStep(0.1)
        self.radius_spin.setDecimals(1)
        self.radius_spin.setValue(0.5)

        grid.addWidget(self.amount_label, 0, 0)
        grid.addWidget(self.amount_slider, 0, 1)
        grid.addWidget(self.amount_spin, 0, 2)

        grid.addWidget(self.radius_label, 1, 0)
        grid.addWidget(self.radius_slider, 1, 1)
        grid.addWidget(self.radius_spin, 1, 2)

        # Buttons
        btn_layout = QtWidgets.QHBoxLayout()
        layout.addLayout(btn_layout)
        self.apply_btn = QtWidgets.QPushButton("適用")
        self.cancel_btn = QtWidgets.QPushButton("キャンセル")
        btn_layout.addWidget(self.apply_btn)
        btn_layout.addWidget(self.cancel_btn)

        # 状態
        self.preview_timer = QtCore.QTimer(self)
        self.preview_timer.setSingleShot(True)
        self.preview_timer.timeout.connect(self.preview)
        self.preview_file = None
        self.original_file = None

        # --- イベント接続 ---
        self.amount_slider.valueChanged.connect(self.sync_amount_from_slider)
        self.radius_slider.valueChanged.connect(self.sync_radius_from_slider)
        self.amount_spin.valueChanged.connect(self.sync_amount_from_spin)
        self.radius_spin.valueChanged.connect(self.sync_radius_from_spin)
        self.apply_btn.clicked.connect(self.apply)
        self.cancel_btn.clicked.connect(self.cancel)

        # --- Siril 側初期状態の保存 ---
        with self.siril.image_lock():
            if not self.siril.is_image_loaded():
                QtWidgets.QMessageBox.warning(self, "警告", "画像をロードしてください。")
                sys.exit(0)
            self.original_file = tempfile.mktemp(suffix=".fit")
            self.siril.cmd("save", self.original_file)
            self.siril.log(f"Original saved as {self.original_file}")

        # ✅ 初期値同期（ここが修正箇所）
        self.amount_slider.blockSignals(True)
        self.amount_slider.setValue(int(self.amount_spin.value() * 10))
        self.amount_slider.blockSignals(False)

        self.radius_slider.blockSignals(True)
        self.radius_slider.setValue(int(self.radius_spin.value() * 10))
        self.radius_slider.blockSignals(False)

        # 閉じるイベント
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose, True)

    # -------------------
    # スライダー・入力同期処理
    # -------------------
    def sync_amount_from_slider(self, value):
        val = round(value / 10.0, 1)
        self.amount_spin.blockSignals(True)
        self.amount_spin.setValue(val)
        self.amount_spin.blockSignals(False)
        self.schedule_preview()

    def sync_radius_from_slider(self, value):
        val = round(value / 10.0, 1)
        self.radius_spin.blockSignals(True)
        self.radius_spin.setValue(val)
        self.radius_spin.blockSignals(False)
        self.schedule_preview()

    def sync_amount_from_spin(self, value):
        val = round(float(value), 1)
        self.amount_slider.blockSignals(True)
        self.amount_slider.setValue(int(val * 10))
        self.amount_slider.blockSignals(False)
        self.schedule_preview()

    def sync_radius_from_spin(self, value):
        val = round(float(value), 1)
        self.radius_slider.blockSignals(True)
        self.radius_slider.setValue(int(val * 10))
        self.radius_slider.blockSignals(False)
        self.schedule_preview()

    # -------------------
    # プレビュー関連
    # -------------------
    def schedule_preview(self):
        """300ms デバウンスでプレビュー"""
        self.preview_timer.start(400)

    def preview(self):
        """Siril 上でプレビュー実行"""
        try:
            with self.siril.image_lock():
                self.siril.cmd("load", self.original_file)
                amount = round(self.amount_spin.value(), 1)
                radius = round(self.radius_spin.value(), 1)
                self.siril.cmd("unsharp", str(amount), str(radius))
                if not self.preview_file:
                    self.preview_file = tempfile.mktemp(suffix=".fit")
                self.siril.cmd("save", self.preview_file)
                self.siril.log(f"Preview updated ({amount}, {radius})")
        except SirilError as e:
            QtWidgets.QMessageBox.warning(self, "エラー", f"プレビュー中にエラーが発生しました:\n{e}")

    # -------------------
    # ボタン操作
    # -------------------
    def apply(self):
        """プレビューを確定"""
        try:
            with self.siril.image_lock():
                if self.preview_file and os.path.exists(self.preview_file):
                    self.siril.cmd("load", self.preview_file)
                    self.siril.log("Unsharp mask applied permanently.")
        except SirilError as e:
            QtWidgets.QMessageBox.warning(self, "エラー", f"適用時にエラーが発生しました:\n{e}")
        self.cleanup_and_close()

    def cancel(self):
        """元画像に戻して終了"""
        try:
            with self.siril.image_lock():
                if self.original_file and os.path.exists(self.original_file):
                    self.siril.cmd("load", self.original_file)
                    self.siril.log("Preview cancelled, restored original image.")
        except SirilError:
            pass
        self.cleanup_and_close()

    # -------------------
    # クリーンアップ
    # -------------------
    def cleanup_and_close(self):
        for f in [self.original_file, self.preview_file]:
            if f and os.path.exists(f):
                try:
                    os.remove(f)
                except Exception:
                    pass
        self.close()


def main():
    app = QtWidgets.QApplication(sys.argv)
    win = UnsharpMaskGUI()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
