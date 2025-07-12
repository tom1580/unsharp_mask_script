import sirilpy as s
import tkinter as tk
from tkinter import ttk
from ttkthemes import ThemedTk
from sirilpy import tksiril

class UnsharpMaskGUI:
    def __init__(self, root):
        self.siril = s.SirilInterface()
        try:
            self.siril.connect()
        except s.SirilConnectionError as e:
            print(f"Sirilへの接続に失敗しました: {e}")
            self.siril.error_messagebox(f"Sirilに接続できませんでした。\nSirilが起動していることを確認してください。")
            root.destroy()
            return

        self.root = root
        self.root.title("unsharp mask")        
        self.root.wm_attributes("-topmost", True)
        
        # --- メインフレーム ---
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- パラメータ調整 ---
        param_frame = ttk.Frame(main_frame, padding="10")
        param_frame.pack(fill=tk.X)

        # 適用量 (Amount)
        ttk.Label(param_frame, text="適用量 (Amount):").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.amount_var = tk.DoubleVar(value=5.0)
        amount_scale = ttk.Scale(
            param_frame,
            from_=0.1,
            to=10.0,
            variable=self.amount_var,
            orient=tk.HORIZONTAL,
            # スライダーを動かすと値が丸められるようにコマンドを設定
            command=lambda v: self.amount_var.set(round(float(v), 1))
        )
        amount_scale.grid(row=0, column=1, sticky=tk.EW, padx=5)
        amount_entry = ttk.Entry(param_frame, textvariable=self.amount_var, width=6)
        amount_entry.grid(row=0, column=2)

        # 半径 (Radius) - これが周波数に相当
        ttk.Label(param_frame, text="半径 (Radius):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.radius_var = tk.DoubleVar(value=0.5)
        radius_scale = ttk.Scale(
            param_frame,
            from_=0.1,
            to=20.0,
            variable=self.radius_var,
            orient=tk.HORIZONTAL,
            # スライダーを動かすと値が丸められるようにコマンドを設定
            command=lambda v: self.radius_var.set(round(float(v), 1))
        )
        radius_scale.grid(row=1, column=1, sticky=tk.EW, padx=5)
        radius_entry = ttk.Entry(param_frame, textvariable=self.radius_var, width=6)
        radius_entry.grid(row=1, column=2)
        
        param_frame.columnconfigure(1, weight=1)

        # --- ボタン ---
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)

        apply_btn = ttk.Button(button_frame, text="適用", command=self.apply_filter)
        apply_btn.pack(side=tk.LEFT, padx=5)
        tksiril.create_tooltip(apply_btn, "現在の画像にアンシャープマスクを適用します。")
        
        close_btn = ttk.Button(button_frame, text="閉じる", command=self.close_dialog)
        close_btn.pack(side=tk.LEFT, padx=5)
        tksiril.create_tooltip(close_btn, "ダイアログを閉じます。")

    def apply_filter(self):
        """
        アンシャープマスクを適用する
        """
        try:
            if not self.siril.get_image():
                self.siril.error_messagebox("先に画像を読み込んでください。")
                return

            with self.siril.image_lock():
                self.siril.undo_save_state("アンシャープマスク")
                
                # 適用する直前に値を小数点第1位に丸める
                amount = round(self.amount_var.get(), 1)
                radius = round(self.radius_var.get(), 1)
                
                # unsharp_maskコマンドを実行
                self.siril.cmd(f"unsharp {amount} {radius}")
                self.siril.log(f"アンシャープマスクを適用しました (Amount: {amount}, Radius: {radius})。")

        except s.SirilError as e:
            self.siril.error_messagebox(f"エラーが発生しました: {str(e)}")

    def close_dialog(self):
        self.root.quit()
        self.root.destroy()

if __name__ == "__main__":
    root = ThemedTk(theme="arc")
    app = UnsharpMaskGUI(root)
    root.mainloop()
