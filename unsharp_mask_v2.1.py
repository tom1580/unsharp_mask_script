#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unsharp Mask GUI Script for Siril
This script provides a GUI interface for the unsharp mask command.
"""

import sys
import time
import sirilpy as s
from sirilpy import SirilConnectionError, SirilError
try:
    from sirilpy.exceptions import ProcessingThreadBusyError, ImageDialogOpenError
except ImportError:
    # 古いバージョンでは例外が別の場所にある可能性がある
    ProcessingThreadBusyError = SirilError
    ImageDialogOpenError = SirilError

s.ensure_installed("PyQt6")
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                              QHBoxLayout, QLabel, QSlider, QLineEdit, QPushButton,
                              QMessageBox)
from PyQt6.QtCore import Qt, QTimer


class UnsharpMaskGUI(QMainWindow):
    """Unsharp Mask GUI for Siril"""
    
    def __init__(self):
        super().__init__()
        
        # Initialize Siril connection
        self.siril = s.SirilInterface()
        
        try:
            self.siril.connect()
            self.siril.log("Unsharp Mask GUI: 接続成功")
        except SirilConnectionError as e:
            QMessageBox.critical(None, "接続エラー", f"Sirilへの接続に失敗しました: {e}")
            sys.exit(1)
        
        # Check if an image is loaded
        if not self.siril.is_image_loaded():
            self.siril.error_messagebox("画像が読み込まれていません。")
            sys.exit(1)
        
        # Check Siril version (unsharp command has been available since early versions)
        try:
            self.siril.cmd("requires", "1.4.0")
        except s.CommandError:
            self.siril.error_messagebox("このスクリプトにはSiril 1.4.0以降が必要です。")
            sys.exit(1)
        
        # Initialize variables
        self.original_image_data = None
        self.preview_update_timer = QTimer()
        self.preview_update_timer.setSingleShot(True)
        self.preview_update_timer.timeout.connect(self.update_preview)
        self.is_updating = False
        
        # Load and save original image
        self.load_original_image()
        
        # Create GUI
        self.create_gui()
    
    def load_original_image(self):
        """元画像を取得して保存"""
        try:
            with self.siril.image_lock():
                fit = self.siril.get_image()
                if fit is None or fit.data is None:
                    self.siril.error_messagebox("画像データの取得に失敗しました。")
                    sys.exit(1)
                
                # 元画像のデータをコピーして保存
                self.original_image_data = fit.data.copy()
                self.siril.log("元画像を保存しました")
        except Exception as e:
            self.siril.error_messagebox(f"画像の読み込みエラー: {e}")
            sys.exit(1)
    
    def create_gui(self):
        """GUIを作成"""
        self.setWindowTitle("Unsharp Mask v2.1")
        self.setGeometry(900, 100, 350, 120)
        
        # メインウィジェット
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # メインレイアウト
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Sigmaパラメータ
        sigma_layout = QHBoxLayout()
        sigma_label = QLabel("Sigma:")
        sigma_label.setMinimumWidth(50)
        sigma_layout.addWidget(sigma_label)
        
        self.sigma_slider = QSlider(Qt.Orientation.Horizontal)
        self.sigma_slider.setMinimum(1)  # 0.1 * 10
        self.sigma_slider.setMaximum(100)  # 10.0 * 10
        self.sigma_slider.setValue(10)  # 1.0 * 10
        self.sigma_slider.valueChanged.connect(self.on_sigma_slider_changed)
        sigma_layout.addWidget(self.sigma_slider)
        
        self.sigma_entry = QLineEdit()
        self.sigma_entry.setText("1.0")
        self.sigma_entry.setMaximumWidth(80)
        self.sigma_entry.setMinimumWidth(80)
        self.sigma_entry.textChanged.connect(self.on_sigma_entry_changed)
        sigma_layout.addWidget(self.sigma_entry)
        
        main_layout.addLayout(sigma_layout)
        
        # Multiパラメータ
        multi_layout = QHBoxLayout()
        multi_label = QLabel("Multi:")
        multi_label.setMinimumWidth(50)
        multi_layout.addWidget(multi_label)
        
        self.multi_slider = QSlider(Qt.Orientation.Horizontal)
        self.multi_slider.setMinimum(0)  # 0.0 * 10
        self.multi_slider.setMaximum(50)  # 5.0 * 10
        self.multi_slider.setValue(10)  # 1.0 * 10
        self.multi_slider.valueChanged.connect(self.on_multi_slider_changed)
        multi_layout.addWidget(self.multi_slider)
        
        self.multi_entry = QLineEdit()
        self.multi_entry.setText("1.0")
        self.multi_entry.setMaximumWidth(80)
        self.multi_entry.setMinimumWidth(80)
        self.multi_entry.textChanged.connect(self.on_multi_entry_changed)
        multi_layout.addWidget(self.multi_entry)
        
        main_layout.addLayout(multi_layout)
        
        # ボタンレイアウト
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.reset_button = QPushButton("リセット")
        self.reset_button.clicked.connect(self.reset_image)
        button_layout.addWidget(self.reset_button)
        
        self.apply_button = QPushButton("確定")
        self.apply_button.clicked.connect(self.apply_changes)
        button_layout.addWidget(self.apply_button)
        
        main_layout.addLayout(button_layout)
        main_layout.addStretch()
    
    def on_sigma_slider_changed(self, value):
        """Sigmaスライドバーの値が変更されたとき"""
        val = value / 10.0
        # 入力枠を更新（シグナルを一時的にブロックして無限ループを防ぐ）
        self.sigma_entry.blockSignals(True)
        self.sigma_entry.setText(f"{val:.2f}")
        self.sigma_entry.blockSignals(False)
        self.schedule_preview_update()
    
    def on_sigma_entry_changed(self, text):
        """Sigma入力枠の値が変更されたとき"""
        try:
            val = float(text)
            if 0.1 <= val <= 10.0:
                # スライドバーを更新（シグナルを一時的にブロック）
                self.sigma_slider.blockSignals(True)
                self.sigma_slider.setValue(int(val * 10))
                self.sigma_slider.blockSignals(False)
                self.schedule_preview_update()
        except ValueError:
            # 無効な値は無視
            pass
    
    def on_multi_slider_changed(self, value):
        """Multiスライドバーの値が変更されたとき"""
        val = value / 10.0
        # 入力枠を更新（シグナルを一時的にブロック）
        self.multi_entry.blockSignals(True)
        self.multi_entry.setText(f"{val:.2f}")
        self.multi_entry.blockSignals(False)
        self.schedule_preview_update()
    
    def on_multi_entry_changed(self, text):
        """Multi入力枠の値が変更されたとき"""
        try:
            val = float(text)
            if 0.0 <= val <= 5.0:
                # スライドバーを更新（シグナルを一時的にブロック）
                self.multi_slider.blockSignals(True)
                self.multi_slider.setValue(int(val * 10))
                self.multi_slider.blockSignals(False)
                self.schedule_preview_update()
        except ValueError:
            # 無効な値は無視
            pass
    
    def schedule_preview_update(self):
        """プレビュー更新をスケジュール（デバウンス）"""
        # 処理中はスケジュールしない
        if self.is_updating:
            return
        # タイマーをリセット（300ms後に更新、デバウンス時間を少し長くして競合を回避）
        self.preview_update_timer.stop()
        self.preview_update_timer.start(300)
    
    def update_preview(self):
        """プレビューを更新（元画像から処理を適用）"""
        if self.is_updating:
            return
        
        try:
            sigma = float(self.sigma_entry.text())
            multi = float(self.multi_entry.text())
            
            # 範囲チェック
            if not (0.1 <= sigma <= 10.0) or not (0.0 <= multi <= 5.0):
                return
            
            self.is_updating = True
            
            # 画像ロックを最小限に保つため、データ復元とコマンド実行を分離
            # まず、元画像のデータを復元
            with self.siril.image_lock():
                fit = self.siril.get_image()
                fit.data[:] = self.original_image_data.copy()
                self.siril.set_image_pixeldata(fit.data)
            
            # ロックを解放した後、GUIイベントを処理してSirilのGUIが画像にアクセスできるようにする
            QApplication.processEvents()
            
            # 少し待機して、SirilのGUIが画像の読み込みを完了できるようにする
            # これにより、cmd()実行中の競合を減らす
            time.sleep(0.05)  # 50ms待機
            
            # unsharpコマンドを実行（元画像に対して）
            # コマンド実行中は画像ロックが保持されていないため、SirilのGUIがアクセス可能
            # ただし、cmd()実行中に画像が変更されるため、タイミングによっては競合が発生する可能性がある
            try:
                self.siril.cmd("unsharp", str(sigma), str(multi))
            except (ProcessingThreadBusyError, ImageDialogOpenError) as e:
                # 処理スレッドがビジーまたはダイアログが開いている場合は、スキップ
                self.siril.log(f"プレビュー更新をスキップ: {e}")
                # ロックを取得して元画像に戻す
                try:
                    with self.siril.image_lock():
                        fit = self.siril.get_image()
                        fit.data[:] = self.original_image_data.copy()
                        self.siril.set_image_pixeldata(fit.data)
                except Exception:
                    pass
            except Exception as e:
                # その他のエラーが発生した場合は、ロックを取得して元画像に戻す
                try:
                    with self.siril.image_lock():
                        fit = self.siril.get_image()
                        fit.data[:] = self.original_image_data.copy()
                        self.siril.set_image_pixeldata(fit.data)
                except Exception:
                    pass
                self.siril.log(f"プレビュー更新エラー: {e}")
            
            self.is_updating = False
            
        except (ValueError, SirilError, Exception) as e:
            self.siril.log(f"プレビュー更新エラー: {e}")
            self.is_updating = False
    
    def reset_image(self):
        """元画像に戻す"""
        try:
            with self.siril.image_lock():
                fit = self.siril.get_image()
                fit.data[:] = self.original_image_data.copy()
                self.siril.set_image_pixeldata(fit.data)
            
            # パラメータをリセット
            self.sigma_slider.blockSignals(True)
            self.sigma_slider.setValue(10)  # 1.0 * 10
            self.sigma_slider.blockSignals(False)
            self.sigma_entry.blockSignals(True)
            self.sigma_entry.setText("1.0")
            self.sigma_entry.blockSignals(False)
            
            self.multi_slider.blockSignals(True)
            self.multi_slider.setValue(10)  # 1.0 * 10
            self.multi_slider.blockSignals(False)
            self.multi_entry.blockSignals(True)
            self.multi_entry.setText("1.0")
            self.multi_entry.blockSignals(False)
            
            self.siril.log("画像をリセットしました")
        except SirilError as e:
            self.siril.error_messagebox(f"リセットエラー: {e}")
        except Exception as e:
            self.siril.error_messagebox(f"リセットエラー: {e}")
    
    def apply_changes(self):
        """変更を確定"""
        try:
            sigma = float(self.sigma_entry.text())
            multi = float(self.multi_entry.text())
            
            # 範囲チェック
            if not (0.1 <= sigma <= 10.0):
                self.siril.error_messagebox(f"Sigmaの値が範囲外です (0.1-10.0): {sigma}")
                return
            if not (0.0 <= multi <= 5.0):
                self.siril.error_messagebox(f"Multiの値が範囲外です (0.0-5.0): {multi}")
                return
            
            # undo状態を保存（変更を適用する前に）
            # 注意: undo_save_stateはimage_lock内で実行する必要がある
            with self.siril.image_lock():
                self.siril.undo_save_state(f"Unsharp Mask: sigma={sigma:.2f}, multi={multi:.2f}")
                
                # 元画像から処理を適用（確定）
                fit = self.siril.get_image()
                fit.data[:] = self.original_image_data.copy()
                self.siril.set_image_pixeldata(fit.data)
            
            # ロックを解放してからコマンドを実行（cmd()はロック内で実行してはいけない）
            # GUIイベントを処理してSirilのGUIが画像にアクセスできるようにする
            QApplication.processEvents()
            time.sleep(0.05)  # 50ms待機
            
            # unsharpコマンドを実行（ロック外で実行）
            try:
                self.siril.cmd("unsharp", str(sigma), str(multi))
            except (ProcessingThreadBusyError, ImageDialogOpenError) as e:
                # 処理スレッドがビジーまたはダイアログが開いている場合は、エラーを表示
                self.siril.error_messagebox(f"処理を実行できませんでした: {e}")
                return
            
            # 元画像を更新（確定した画像を新しい元画像とする）
            with self.siril.image_lock():
                fit = self.siril.get_image()
                self.original_image_data = fit.data.copy()
            
            self.siril.log(f"Unsharp Maskを適用しました (sigma={sigma:.2f}, multi={multi:.2f})")
            self.siril.info_messagebox("変更を確定しました")
        except ValueError as e:
            self.siril.error_messagebox(f"値の解析エラー: {e}")
        except SirilError as e:
            self.siril.error_messagebox(f"確定エラー: {e}")
        except Exception as e:
            self.siril.error_messagebox(f"確定エラー: {e}")


def main():
    """メインエントリーポイント"""
    app = QApplication(sys.argv)
    
    try:
        window = UnsharpMaskGUI()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
