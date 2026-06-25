import sys
import os
import time
import threading
import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pyperclip
import pywinauto
from pywinauto import Application

SUBTITLE_WINDOW_TITLES = ["实时辅助字幕", "Live Captions"]
STORAGE_DIR = os.path.join(os.path.expanduser("~"), "Documents", "SubtitleCapture")


class SubtitleCaptureEngine:
    def __init__(self):
        self.is_running = False
        self.last_text = ""
        self.capture_thread = None
        self.text_callback = None
        self.status_callback = None
        self.app = None

    def find_subtitle_window(self):
        for title in SUBTITLE_WINDOW_TITLES:
            try:
                app = Application(backend='uia')
                app.connect(title=title, timeout=1)
                return app
            except:
                continue
        return None

    def get_subtitle_text(self):
        try:
            if self.app is None:
                self.app = self.find_subtitle_window()
                if self.app is None:
                    return ""

            dlg = self.app.window(title_re='实时辅助字幕|Live Captions')
            
            try:
                text_element = dlg.child_window(auto_id='CaptionsTextBlock', control_type='Text')
                return text_element.window_text()
            except:
                pass

            try:
                pane_element = dlg.child_window(auto_id='CaptionsScrollViewer', control_type='Pane')
                return pane_element.window_text()
            except:
                pass

            try:
                static_elements = dlg.descendants(control_type='Text')
                if static_elements:
                    for elem in static_elements:
                        text = elem.window_text()
                        if text and len(text) > 10:
                            return text
            except:
                pass

            try:
                pane_elements = dlg.descendants(control_type='Pane')
                if pane_elements:
                    for elem in pane_elements:
                        text = elem.window_text()
                        if text and len(text) > 10:
                            return text
            except:
                pass

            return ""
        except Exception:
            self.app = None
            return ""

    def capture_loop(self):
        while self.is_running:
            try:
                current_text = self.get_subtitle_text()
                if current_text and current_text != self.last_text:
                    self.last_text = current_text
                    if self.text_callback:
                        self.text_callback(current_text, datetime.datetime.now())
                time.sleep(0.1)
            except Exception:
                time.sleep(0.5)

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        if self.status_callback:
            self.status_callback(True)
        self.capture_thread = threading.Thread(target=self.capture_loop, daemon=True)
        self.capture_thread.start()

    def stop(self):
        self.is_running = False
        if self.status_callback:
            self.status_callback(False)

    def is_subtitle_available(self):
        return self.find_subtitle_window() is not None


class SubtitleStorage:
    def __init__(self):
        os.makedirs(STORAGE_DIR, exist_ok=True)

    def save_text(self, text, timestamp):
        date_str = timestamp.strftime("%Y%m%d")
        file_path = os.path.join(STORAGE_DIR, f"subtitle_{date_str}.txt")
        
        entry = f"[{timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {text}\n"
        
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(entry)

    def load_history(self, date):
        entries = []
        date_str = date.strftime("%Y%m%d")
        file_path = os.path.join(STORAGE_DIR, f"subtitle_{date_str}.txt")
        
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("["):
                        bracket_end = line.find("]")
                        if bracket_end > 0:
                            timestamp_str = line[1:bracket_end]
                            text = line[bracket_end + 2:]
                            try:
                                timestamp = datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                                entries.append({"text": text, "timestamp": timestamp})
                            except:
                                pass
        
        return entries

    def get_available_dates(self):
        dates = []
        if os.path.exists(STORAGE_DIR):
            for filename in os.listdir(STORAGE_DIR):
                if filename.startswith("subtitle_") and filename.endswith(".txt"):
                    date_str = filename.replace("subtitle_", "").replace(".txt", "")
                    try:
                        date = datetime.datetime.strptime(date_str, "%Y%m%d").date()
                        dates.append(date)
                    except:
                        pass
        
        return sorted(set(dates), reverse=True)

    def clear_history(self, date):
        date_str = date.strftime("%Y%m%d")
        file_path = os.path.join(STORAGE_DIR, f"subtitle_{date_str}.txt")
        if os.path.exists(file_path):
            os.remove(file_path)

    def export_to_file(self, text, file_path):
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(text)

    def get_storage_path(self):
        return STORAGE_DIR


class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Windows 实时字幕捕获工具")
        self.root.geometry("900x700")
        self.root.minsize(700, 500)
        
        self.capture_engine = SubtitleCaptureEngine()
        self.storage = SubtitleStorage()
        
        self.capture_engine.text_callback = self.on_text_captured
        self.capture_engine.status_callback = self.on_status_changed
        
        self.current_text = tk.StringVar()
        self.status_text = tk.StringVar(value="已就绪")
        self.is_capturing = False
        
        self.setup_ui()
        self.update_subtitle_status()
        self.load_history_for_date(datetime.date.today())

    def setup_ui(self):
        style = ttk.Style()
        style.configure("Title.TLabel", font=("Microsoft YaHei", 16, "bold"), foreground="#2c3e50")
        style.configure("Status.TLabel", font=("Microsoft YaHei", 10), foreground="#7f8c8d")
        style.configure("Header.TLabel", font=("Microsoft YaHei", 12, "bold"), foreground="#2c3e50")
        
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="📝 Windows 实时字幕捕获工具", style="Title.TLabel").pack(anchor=tk.W, pady=(0, 10))

        top_bar = ttk.Frame(main_frame)
        top_bar.pack(fill=tk.X, pady=(0, 10))

        self.start_btn = ttk.Button(top_bar, text="▶ 开始捕获", command=self.toggle_capture)
        self.start_btn.pack(side=tk.LEFT, padx=5)

        ttk.Button(top_bar, text="🔄 刷新状态", command=self.update_subtitle_status).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_bar, text="📂 打开存储文件夹", command=self.open_storage_folder).pack(side=tk.LEFT, padx=5)

        self.status_label = ttk.Label(top_bar, textvariable=self.status_text, style="Status.TLabel")
        self.status_label.pack(side=tk.RIGHT)

        current_frame = ttk.LabelFrame(main_frame, text="📌 当前字幕内容", padding=10)
        current_frame.pack(fill=tk.X, pady=(0, 10))

        self.current_text_box = tk.Text(current_frame, height=6, font=("Microsoft YaHei", 14), 
                                        wrap=tk.WORD, state=tk.DISABLED, bg="#fafafa", fg="#2c3e50")
        self.current_text_box.pack(fill=tk.X, pady=(0, 5))

        current_btn_frame = ttk.Frame(current_frame)
        current_btn_frame.pack(fill=tk.X)
        ttk.Button(current_btn_frame, text="📋 复制当前内容", command=self.copy_current_text).pack(side=tk.RIGHT)

        history_control_frame = ttk.Frame(main_frame)
        history_control_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(history_control_frame, text="📅 选择日期:", font=("Microsoft YaHei", 11)).pack(side=tk.LEFT, padx=5)

        self.date_var = tk.StringVar()
        self.date_picker = ttk.Combobox(history_control_frame, textvariable=self.date_var, width=12, state="readonly")
        self.date_picker.pack(side=tk.LEFT, padx=5)
        self.date_picker.bind("<<ComboboxSelected>>", self.on_date_selected)

        ttk.Button(history_control_frame, text="📋 复制全部历史", command=self.copy_all_history).pack(side=tk.RIGHT, padx=5)
        ttk.Button(history_control_frame, text="💾 导出历史记录", command=self.export_history).pack(side=tk.RIGHT, padx=5)
        ttk.Button(history_control_frame, text="🗑 清除历史记录", command=self.clear_history).pack(side=tk.RIGHT, padx=5)

        history_frame = ttk.LabelFrame(main_frame, text="📜 历史记录", padding=10)
        history_frame.pack(fill=tk.BOTH, expand=True)

        self.history_list = tk.Listbox(history_frame, font=("Microsoft YaHei", 12), bg="#ffffff", fg="#34495e",
                                       selectbackground="#ecf0f1", selectforeground="#2c3e50")
        self.history_list.pack(fill=tk.BOTH, expand=True)

        bottom_tip = ttk.Label(main_frame, text="💡 提示：使用Win+Ctrl+C快捷键开启Windows实时字幕功能", 
                               style="Status.TLabel")
        bottom_tip.pack(anchor=tk.CENTER, pady=(10, 0))

    def toggle_capture(self):
        if self.is_capturing:
            self.capture_engine.stop()
            self.is_capturing = False
            self.start_btn.config(text="▶ 开始捕获")
        else:
            if self.capture_engine.is_subtitle_available():
                self.capture_engine.start()
                self.is_capturing = True
                self.start_btn.config(text="⏹ 停止捕获")
            else:
                messagebox.showwarning("警告", "未检测到实时字幕窗口，请先开启Windows实时字幕功能")

    def update_subtitle_status(self):
        if self.capture_engine.is_subtitle_available():
            self.start_btn.config(state=tk.NORMAL)
            if not self.is_capturing:
                self.status_text.set("已就绪，点击开始捕获")
        else:
            self.start_btn.config(state=tk.DISABLED)
            self.status_text.set("未检测到实时字幕窗口，请先开启Windows实时字幕功能")
        self.update_date_list()

    def update_date_list(self):
        dates = self.storage.get_available_dates()
        date_strings = [d.strftime("%Y-%m-%d") for d in dates]
        if date_strings:
            self.date_picker["values"] = date_strings
            if not self.date_var.get():
                self.date_var.set(date_strings[0])
                self.load_history_for_date(dates[0])

    def on_text_captured(self, text, timestamp):
        self.current_text_box.config(state=tk.NORMAL)
        self.current_text_box.delete(1.0, tk.END)
        self.current_text_box.insert(tk.END, text)
        self.current_text_box.config(state=tk.DISABLED)
        self.current_text_box.see(tk.END)
        
        self.storage.save_text(text, timestamp)
        
        if timestamp.date().strftime("%Y-%m-%d") == self.date_var.get():
            self.load_history_for_date(timestamp.date())

    def on_status_changed(self, is_running):
        self.is_capturing = is_running
        if is_running:
            self.status_text.set("正在捕获实时字幕...")
        else:
            self.status_text.set("已停止捕获")

    def load_history_for_date(self, date):
        entries = self.storage.load_history(date)
        self.history_list.delete(0, tk.END)
        
        for entry in entries:
            timestamp_str = entry["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
            display_text = f"[{timestamp_str}] {entry['text']}"
            self.history_list.insert(tk.END, display_text)

    def on_date_selected(self, event):
        date_str = self.date_var.get()
        try:
            date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            self.load_history_for_date(date)
        except:
            pass

    def copy_current_text(self):
        text = self.current_text_box.get(1.0, tk.END).strip()
        if text:
            pyperclip.copy(text)
            self.status_text.set("已复制当前字幕内容")

    def copy_all_history(self):
        all_text = "\n".join([self.history_list.get(i) for i in range(self.history_list.size())])
        if all_text:
            pyperclip.copy(all_text)
            self.status_text.set("已复制所有历史记录")

    def export_history(self):
        all_text = "\n".join([self.history_list.get(i) for i in range(self.history_list.size())])
        if not all_text:
            messagebox.showinfo("提示", "没有可导出的历史记录")
            return
        
        date_str = self.date_var.get()
        default_filename = f"subtitle_history_{date_str.replace('-', '')}.txt"
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
            initialfile=default_filename
        )
        
        if file_path:
            self.storage.export_to_file(all_text, file_path)
            self.status_text.set(f"已导出到: {file_path}")

    def clear_history(self):
        if self.history_list.size() == 0:
            messagebox.showinfo("提示", "没有可清除的历史记录")
            return
        
        date_str = self.date_var.get()
        if messagebox.askyesno("确认删除", f"确定要清除 {date_str} 的历史记录吗？"):
            try:
                date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
                self.storage.clear_history(date)
                self.history_list.delete(0, tk.END)
                self.status_text.set("已清除历史记录")
                self.update_date_list()
            except:
                messagebox.showerror("错误", "清除历史记录失败")

    def open_storage_folder(self):
        os.startfile(self.storage.get_storage_path())

    def on_close(self):
        self.capture_engine.stop()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = MainWindow(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()