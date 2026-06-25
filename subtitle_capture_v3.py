import sys
import os
import time
import threading
import datetime
import re
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import pyperclip
import pywinauto
from pywinauto import Application
import ttkbootstrap as ttkb
from ttkbootstrap.constants import *

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


class SubtitleProject:
    def __init__(self, name, file_path):
        self.name = name
        self.file_path = file_path
        self.content = ""
        self.last_update = None
        self.enabled = True

    def add_text(self, text, timestamp):
        formatted_text = self.format_text(text)
        self.content += formatted_text
        self.last_update = timestamp

    def format_text(self, text):
        sentences = re.split(r'([。！？.!?])', text)
        formatted_lines = []
        for i in range(0, len(sentences), 2):
            sentence = sentences[i].strip()
            if sentence:
                punctuation = sentences[i + 1] if i + 1 < len(sentences) else ""
                formatted_lines.append(f"{sentence}{punctuation}")
        return "\n".join(formatted_lines) + "\n\n"

    def save_to_markdown(self):
        try:
            dir_path = os.path.dirname(self.file_path)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path)
            
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            md_content = f"""# {self.name}

> 转写时间：{timestamp}

---

{self.content}
"""
            with open(self.file_path, "w", encoding="utf-8") as f:
                f.write(md_content)
            return True
        except Exception as e:
            print(f"保存失败: {e}")
            return False

    def save_content_directly(self, content):
        try:
            dir_path = os.path.dirname(self.file_path)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path)
            
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            md_content = f"""# {self.name}

> 转写时间：{timestamp}

---

{content}
"""
            with open(self.file_path, "w", encoding="utf-8") as f:
                f.write(md_content)
            self.last_update = datetime.datetime.now()
            return True
        except Exception as e:
            print(f"直接保存失败: {e}")
            return False


class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("🎬 Windows 实时字幕捕获工具 v3.0")
        self.root.geometry("1100x850")
        self.root.minsize(900, 650)
        
        self.capture_engine = SubtitleCaptureEngine()
        self.projects = []
        self.current_project = None
        
        self.capture_engine.text_callback = self.on_text_captured
        self.capture_engine.status_callback = self.on_status_changed
        
        self.status_text = tk.StringVar(value="✓ 已就绪")
        self.is_capturing = False
        self.text_queue = []
        self.auto_save_timer = None
        self.last_save_time = None
        
        os.makedirs(STORAGE_DIR, exist_ok=True)
        self.setup_ui()
        self.update_subtitle_status()
        self.process_text_queue()

    def setup_ui(self):
        style = ttk.Style()
        
        style.configure("Title.TLabel", font=("Microsoft YaHei", 18, "bold"), foreground="#2c3e50")
        style.configure("Status.TLabel", font=("Microsoft YaHei", 10), foreground="#7f8c8d")
        style.configure("Header.TLabel", font=("Microsoft YaHei", 13, "bold"), foreground="#2c3e50")
        style.configure("ProjectName.TLabel", font=("Microsoft YaHei", 12), foreground="#34495e")
        
        main_frame = ttk.Frame(self.root, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(title_frame, text="🎬 Windows 实时字幕捕获工具 v3.0", style="Title.TLabel").pack(anchor=tk.W)
        ttk.Label(title_frame, text="专业多项目实时字幕转写工具 | 支持实时保存", style="Status.TLabel").pack(anchor=tk.W, pady=(2, 0))

        top_bar = ttk.Frame(main_frame)
        top_bar.pack(fill=tk.X, pady=(0, 12))

        self.start_btn = ttkb.Button(top_bar, text="▶ 开始捕获", command=self.toggle_capture, 
                                      bootstyle="success", width=14)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 8))

        ttkb.Button(top_bar, text="➕ 新建项目", command=self.create_new_project, 
                     bootstyle="primary", width=14).pack(side=tk.LEFT, padx=4)
        ttkb.Button(top_bar, text="📁 选择项目", command=self.select_multiple_projects, 
                     bootstyle="info", width=14).pack(side=tk.LEFT, padx=4)
        ttkb.Button(top_bar, text="🔄 刷新状态", command=self.update_subtitle_status, 
                     bootstyle="warning", width=12).pack(side=tk.LEFT, padx=4)
        ttkb.Button(top_bar, text="📂 打开文件夹", command=self.open_storage_folder, 
                     bootstyle="secondary", width=12).pack(side=tk.LEFT, padx=4)

        status_frame = ttk.Frame(top_bar)
        status_frame.pack(side=tk.RIGHT)
        self.status_label = ttk.Label(status_frame, textvariable=self.status_text, style="Status.TLabel")
        self.status_label.pack(side=tk.RIGHT)
        
        self.status_indicator = ttk.Label(status_frame, text="●", font=("Arial", 12), foreground="#27ae60")
        self.status_indicator.pack(side=tk.RIGHT, padx=(0, 8))

        main_content = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        main_content.pack(fill=tk.BOTH, expand=True, pady=(0, 12))

        left_panel = ttk.Frame(main_content, width=280)
        
        project_list_frame = ttk.LabelFrame(left_panel, text="📋 项目列表", padding=10)
        project_list_frame.pack(fill=tk.BOTH, expand=True)

        self.project_list = tk.Listbox(project_list_frame, font=("Microsoft YaHei", 11), bg="#ffffff", fg="#34495e",
                                       selectbackground="#3498db", selectforeground="white",
                                       activestyle="none", bd=0, highlightthickness=0,
                                       selectborderwidth=0)
        self.project_list.pack(fill=tk.BOTH, expand=True, pady=(0, 8))
        self.project_list.bind("<<ListboxSelect>>", self.on_project_selected)

        project_btn_frame = ttk.Frame(project_list_frame)
        project_btn_frame.pack(fill=tk.X)
        
        ttkb.Button(project_btn_frame, text="✏️ 重命名", command=self.rename_project, 
                     bootstyle="warning", width=10).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))
        ttkb.Button(project_btn_frame, text="🗑 删除", command=self.delete_project, 
                     bootstyle="danger", width=10).pack(side=tk.LEFT, fill=tk.X, expand=True)

        main_content.add(left_panel, weight=1)

        right_panel = ttk.Frame(main_content)
        
        current_frame = ttk.LabelFrame(right_panel, text="📌 当前字幕内容", padding=12)
        current_frame.pack(fill=tk.X, pady=(0, 10))

        self.current_text_box = scrolledtext.ScrolledText(current_frame, height=6, font=("Microsoft YaHei", 14), 
                                                          wrap=tk.WORD, state=tk.DISABLED, bg="#f8f9fa", fg="#2c3e50",
                                                          bd=0, highlightthickness=1, highlightcolor="#e9ecef",
                                                          insertbackground="#3498db")
        self.current_text_box.pack(fill=tk.X, pady=(0, 8))

        current_btn_frame = ttk.Frame(current_frame)
        current_btn_frame.pack(fill=tk.X)
        ttkb.Button(current_btn_frame, text="📋 复制当前内容", command=self.copy_current_text, 
                     bootstyle="info", width=16).pack(side=tk.RIGHT, padx=(4, 0))
        ttkb.Button(current_btn_frame, text="📝 写入选中项目", command=self.write_to_project, 
                     bootstyle="primary", width=16).pack(side=tk.RIGHT)

        editor_frame = ttk.LabelFrame(right_panel, text="📝 项目编辑区", padding=12)
        editor_frame.pack(fill=tk.BOTH, expand=True)

        editor_toolbar = tk.Frame(editor_frame, bg="#f8f9fa")
        editor_toolbar.pack(fill=tk.X, pady=(0, 6))
        editor_toolbar.configure(relief=tk.RAISED, bd=1)
        
        tk.Label(editor_toolbar, text="编辑工具：", font=("Microsoft YaHei", 10), bg="#f8f9fa").pack(side=tk.LEFT, padx=(8, 4))
        
        self.toggle_transcribe_btn = ttkb.Button(editor_toolbar, text="⏸ 暂停转写", 
                                                  command=self.toggle_project_transcribe, 
                                                  bootstyle="warning", width=14)
        self.toggle_transcribe_btn.pack(side=tk.LEFT, padx=2)
        
        ttkb.Button(editor_toolbar, text="💾 保存项目", command=self.save_current_project, 
                     bootstyle="success", width=14).pack(side=tk.LEFT, padx=2)
        
        self.copy_btn = ttkb.Button(editor_toolbar, text="📋 复制全部内容", 
                                     command=self.copy_document_content, 
                                     bootstyle="info", width=16)
        self.copy_btn.pack(side=tk.LEFT, padx=2)
        
        self.auto_save_var = tk.BooleanVar(value=True)
        self.auto_save_check = ttk.Checkbutton(editor_toolbar, text="🔄 自动保存", 
                                               variable=self.auto_save_var,
                                               command=self.toggle_auto_save,
                                               style="Toolbutton")
        self.auto_save_check.pack(side=tk.RIGHT, padx=8)
        
        self.save_status_label = tk.Label(editor_toolbar, text="", font=("Microsoft YaHei", 9), 
                                           fg="#27ae60", bg="#f8f9fa")
        self.save_status_label.pack(side=tk.RIGHT, padx=(0, 8))

        self.editor_text_box = scrolledtext.ScrolledText(editor_frame, font=("Microsoft YaHei", 12), 
                                                        wrap=tk.WORD, bg="#ffffff", fg="#34495e",
                                                        bd=0, highlightthickness=1, highlightcolor="#e9ecef",
                                                        insertbackground="#3498db", undo=True)
        self.editor_text_box.pack(fill=tk.BOTH, expand=True)
        self.editor_text_box.bind("<<Modified>>", self.on_editor_modified)

        main_content.add(right_panel, weight=4)

        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X)
        
        ttk.Label(bottom_frame, text="💡 提示：使用 Win+Ctrl+C 快捷键开启 Windows 实时字幕功能 | 编辑内容自动保存到文件", 
                  style="Status.TLabel").pack(side=tk.LEFT)
        ttk.Label(bottom_frame, text="当前存储目录：" + STORAGE_DIR, 
                  style="Status.TLabel").pack(side=tk.RIGHT)

    def on_text_captured(self, text, timestamp):
        self.text_queue.append((text, timestamp))

    def process_text_queue(self):
        if self.text_queue:
            text, timestamp = self.text_queue.pop(0)
            
            self.current_text_box.config(state=tk.NORMAL)
            self.current_text_box.delete(1.0, tk.END)
            self.current_text_box.insert(tk.END, text)
            self.current_text_box.config(state=tk.DISABLED)
            self.current_text_box.see(tk.END)
            
            for project in self.projects:
                if project.enabled:
                    project.add_text(text, timestamp)
                    if self.current_project == project:
                        self.update_editor_text(project.content)
        
        self.root.after(50, self.process_text_queue)

    def update_editor_text(self, content):
        try:
            current_content = self.editor_text_box.get(1.0, tk.END)
            if current_content != content:
                self.editor_text_box.delete(1.0, tk.END)
                self.editor_text_box.insert(tk.END, content)
                self.editor_text_box.edit_reset()
                self.editor_text_box.see(tk.END)
        except:
            pass

    def on_editor_modified(self, event):
        if self.editor_text_box.edit_modified():
            self.editor_text_box.edit_modified(False)
            if self.current_project and self.auto_save_var.get():
                self.schedule_auto_save()

    def schedule_auto_save(self):
        if self.auto_save_timer:
            self.root.after_cancel(self.auto_save_timer)
        self.auto_save_timer = self.root.after(1000, self.auto_save_project)

    def auto_save_project(self):
        if self.current_project and self.auto_save_var.get():
            content = self.editor_text_box.get(1.0, tk.END)
            if content.strip():
                self.current_project.content = content
                if self.current_project.save_content_directly(content):
                    self.last_save_time = datetime.datetime.now()
                    time_str = self.last_save_time.strftime("%H:%M:%S")
                    self.save_status_label.config(text=f"✓ 已保存 {time_str}")
                    self.status_text.set(f"✓ 自动保存成功")
    
    def toggle_auto_save(self):
        if self.auto_save_var.get():
            self.save_status_label.config(text="✓ 自动保存已开启")
            self.status_text.set("✓ 自动保存已开启")
            if self.current_project:
                self.schedule_auto_save()
        else:
            self.save_status_label.config(text="⚠️ 自动保存已关闭")
            self.status_text.set("⚠️ 自动保存已关闭")

    def create_new_project(self):
        name = self.ask_string("新建项目", "请输入项目名称：")
        if name and name.strip():
            file_path = os.path.join(STORAGE_DIR, f"{name.strip()}.md")
            project = SubtitleProject(name.strip(), file_path)
            self.projects.append(project)
            self.update_project_list()
            self.project_list.selection_set(len(self.projects) - 1)
            self.current_project = project
            self.editor_text_box.delete(1.0, tk.END)
            self.editor_text_box.insert(tk.END, project.content)
            self.editor_text_box.edit_reset()
            self.update_toggle_button_state()
            self.status_text.set(f"✓ 已创建项目: {name}")

    def select_multiple_projects(self):
        files = filedialog.askopenfilenames(
            title="选择多个文件",
            filetypes=[("Markdown文件", "*.md"), ("文本文件", "*.txt"), ("所有文件", "*.*")],
            initialdir=STORAGE_DIR
        )
        
        if files:
            for file_path in files:
                name = os.path.splitext(os.path.basename(file_path))[0]
                project = SubtitleProject(name, file_path)
                
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        project.content = f.read()
                except:
                    pass
                
                self.projects.append(project)
                
            self.update_project_list()
            if self.projects:
                self.project_list.selection_set(0)
                self.current_project = self.projects[0]
                self.editor_text_box.delete(1.0, tk.END)
                self.editor_text_box.insert(tk.END, self.current_project.content)
                self.editor_text_box.edit_reset()
                self.update_toggle_button_state()
            self.status_text.set(f"✓ 已选择 {len(files)} 个项目")

    def update_project_list(self):
        self.project_list.delete(0, tk.END)
        for project in self.projects:
            status_icon = "▶" if project.enabled else "⏹"
            self.project_list.insert(tk.END, f"  {status_icon} {project.name}")

    def on_project_selected(self, event):
        selection = self.project_list.curselection()
        if selection:
            index = selection[0]
            self.current_project = self.projects[index]
            self.editor_text_box.delete(1.0, tk.END)
            self.editor_text_box.insert(tk.END, self.current_project.content)
            self.editor_text_box.edit_reset()
            self.update_toggle_button_state()

    def update_toggle_button_state(self):
        if self.current_project:
            if self.current_project.enabled:
                self.toggle_transcribe_btn.config(text="⏸ 暂停转写", bootstyle="warning")
                self.toggle_transcribe_btn.state(['!disabled'])
            else:
                self.toggle_transcribe_btn.config(text="▶ 恢复转写", bootstyle="success")
                self.toggle_transcribe_btn.state(['!disabled'])
        else:
            self.toggle_transcribe_btn.state(['disabled'])

    def toggle_project_transcribe(self):
        if self.current_project:
            self.current_project.enabled = not self.current_project.enabled
            self.update_project_list()
            
            if self.current_project.enabled:
                self.toggle_transcribe_btn.config(text="⏸ 暂停转写", bootstyle="warning")
                self.status_text.set(f"✓ 已恢复项目 '{self.current_project.name}' 的实时转写")
                messagebox.showinfo("提示", f"已恢复项目 '{self.current_project.name}' 的实时转写\n\n新的字幕内容将继续追加到文档末尾")
            else:
                self.current_project.content = self.editor_text_box.get(1.0, tk.END)
                self.current_project.save_to_markdown()
                self.toggle_transcribe_btn.config(text="▶ 恢复转写", bootstyle="success")
                self.status_text.set(f"✓ 已暂停项目 '{self.current_project.name}' 的转写，内容已保存")
                messagebox.showinfo("提示", f"已暂停项目 '{self.current_project.name}' 的实时转写\n\n当前内容已自动保存到文件")

    def rename_project(self):
        selection = self.project_list.curselection()
        if selection:
            index = selection[0]
            project = self.projects[index]
            new_name = self.ask_string("重命名项目", "请输入新名称：", project.name)
            if new_name and new_name.strip():
                project.name = new_name.strip()
                project.file_path = os.path.join(STORAGE_DIR, f"{project.name}.md")
                self.update_project_list()
                self.status_text.set(f"✓ 已重命名项目: {project.name}")

    def delete_project(self):
        selection = self.project_list.curselection()
        if selection:
            index = selection[0]
            project = self.projects[index]
            if messagebox.askyesno("确认删除", f"确定要删除项目 '{project.name}' 吗？"):
                self.projects.pop(index)
                if self.current_project == project:
                    self.current_project = None
                    self.editor_text_box.delete(1.0, tk.END)
                self.update_project_list()
                self.update_toggle_button_state()
                self.status_text.set("✓ 已删除项目")

    def write_to_project(self):
        text = self.current_text_box.get(1.0, tk.END).strip()
        if not text:
            messagebox.showinfo("提示", "没有可写入的内容")
            return
        
        if self.current_project:
            timestamp = datetime.datetime.now()
            self.current_project.add_text(text, timestamp)
            self.editor_text_box.delete(1.0, tk.END)
            self.editor_text_box.insert(tk.END, self.current_project.content)
            self.editor_text_box.edit_reset()
            self.status_text.set(f"✓ 已写入项目: {self.current_project.name}")
        else:
            messagebox.showwarning("警告", "请先选择一个项目")

    def save_current_project(self):
        if self.current_project:
            self.current_project.content = self.editor_text_box.get(1.0, tk.END)
            if self.current_project.save_to_markdown():
                self.last_save_time = datetime.datetime.now()
                time_str = self.last_save_time.strftime("%H:%M:%S")
                self.save_status_label.config(text=f"✓ 已保存 {time_str}")
                self.status_text.set(f"✓ 已保存项目: {self.current_project.name}")
            else:
                messagebox.showerror("错误", "保存失败")
        else:
            messagebox.showwarning("警告", "请先选择或创建一个项目")

    def copy_current_text(self):
        text = self.current_text_box.get(1.0, tk.END).strip()
        if text:
            pyperclip.copy(text)
            self.status_text.set("✓ 已复制当前字幕内容")

    def copy_document_content(self):
        if self.current_project:
            try:
                content = self.editor_text_box.get(1.0, tk.END)
                
                if content.strip():
                    pyperclip.copy(content)
                    
                    char_count = len(content)
                    line_count = content.count('\n') + 1
                    
                    self.status_text.set(f"✓ 复制成功：{char_count} 字符，{line_count} 行")
                    
                    messagebox.showinfo(
                        "✅ 复制成功", 
                        f"项目 '{self.current_project.name}' 的所有内容已成功复制到剪贴板！\n\n"
                        f"📝 内容统计：\n"
                        f"   • 字符数：{char_count} 个\n"
                        f"   • 行数：{line_count} 行\n\n"
                        f"💡 提示：现在可以粘贴到任意文本编辑器或聊天应用中"
                    )
                else:
                    self.status_text.set("⚠️ 文档内容为空")
                    messagebox.showinfo("提示", "当前项目文档内容为空，无可复制内容")
            except Exception as e:
                self.status_text.set("❌ 复制失败")
                messagebox.showerror(
                    "复制失败", 
                    f"无法复制内容到剪贴板：\n\n{str(e)}\n\n"
                    f"请检查系统剪贴板是否被其他程序占用"
                )
        else:
            self.status_text.set("⚠️ 请先选择项目")
            messagebox.showwarning("警告", "请先从左侧项目列表中选择一个项目")

    def toggle_capture(self):
        if self.is_capturing:
            self.capture_engine.stop()
            self.is_capturing = False
            self.start_btn.config(text="▶ 开始捕获", bootstyle="success")
            self.status_indicator.config(foreground="#27ae60")
        else:
            if self.capture_engine.is_subtitle_available():
                self.capture_engine.start()
                self.is_capturing = True
                self.start_btn.config(text="⏹ 停止捕获", bootstyle="danger")
                self.status_indicator.config(foreground="#e74c3c")
            else:
                messagebox.showwarning("警告", "未检测到实时字幕窗口，请先开启Windows实时字幕功能")

    def update_subtitle_status(self):
        if self.capture_engine.is_subtitle_available():
            self.start_btn.config(state=tk.NORMAL)
            if not self.is_capturing:
                self.status_text.set("✓ 已就绪，点击开始捕获")
        else:
            self.start_btn.config(state=tk.DISABLED)
            self.status_text.set("⚠️ 未检测到实时字幕窗口，请先开启Windows实时字幕功能")

    def on_status_changed(self, is_running):
        self.is_capturing = is_running
        if is_running:
            self.status_text.set("🔴 正在捕获实时字幕...")
        else:
            self.status_text.set("✓ 已停止捕获")

    def open_storage_folder(self):
        os.startfile(STORAGE_DIR)

    def on_close(self):
        if self.auto_save_timer:
            self.root.after_cancel(self.auto_save_timer)
        self.capture_engine.stop()
        if self.current_project:
            self.current_project.content = self.editor_text_box.get(1.0, tk.END)
            self.current_project.save_content_directly(self.current_project.content)
        self.root.destroy()

    def ask_string(self, title, prompt, initialvalue=""):
        result = [None]
        
        def on_ok():
            result[0] = entry.get()
            dialog.destroy()
        
        def on_cancel():
            dialog.destroy()
        
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("420x160")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        dialog.configure(bg="#f8f9fa")
        
        label = ttk.Label(dialog, text=prompt, font=("Microsoft YaHei", 12))
        label.pack(pady=12)
        
        entry = ttk.Entry(dialog, font=("Microsoft YaHei", 12), width=35)
        entry.pack(pady=5)
        entry.insert(0, initialvalue)
        entry.focus_set()
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=12)
        
        ok_btn = ttk.Button(btn_frame, text="确定", command=on_ok)
        ok_btn.pack(side=tk.LEFT, padx=12)
        
        cancel_btn = ttk.Button(btn_frame, text="取消", command=cancel)
        cancel_btn.pack(side=tk.LEFT, padx=12)
        
        entry.bind("<Return>", lambda e: on_ok())
        entry.bind("<Escape>", lambda e: on_cancel())
        
        dialog.wait_window()
        return result[0]


if __name__ == "__main__":
    root = ttkb.Window(themename="flatly")
    app = MainWindow(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()