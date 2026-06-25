import sys
import os
import time
import threading
import datetime
import re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from subtitle_capture_v2 import SubtitleProject, MainWindow
import tkinter as tk


def test_subtitle_project():
    print("=== 测试 SubtitleProject 类 ===")
    
    project = SubtitleProject("测试项目", "test_output.md")
    
    test_text = "这是第一句话。这是第二句话！这是第三句话？"
    project.add_text(test_text, datetime.datetime.now())
    
    print(f"添加文本后内容:\n{project.content}")
    
    sentences = re.split(r'([。！？.!?])', test_text)
    print(f"分割后的句子: {sentences}")
    
    success = project.save_to_markdown()
    print(f"保存到Markdown: {'成功' if success else '失败'}")
    
    if os.path.exists("test_output.md"):
        with open("test_output.md", "r", encoding="utf-8") as f:
            content = f.read()
            print(f"文件内容:\n{content}")
        os.remove("test_output.md")
    
    print("=== SubtitleProject 测试完成 ===\n")


def test_text_formatting():
    print("=== 测试文本格式化功能 ===")
    
    project = SubtitleProject("格式测试", "format_test.md")
    
    test_cases = [
        "你好世界。这是一个测试！",
        "Hello world. This is a test!",
        "中文和English混合。测试句子！",
        "没有句号的文本",
        "一句。两句。三句。"
    ]
    
    for i, text in enumerate(test_cases):
        print(f"\n测试用例 {i+1}: {text}")
        formatted = project.format_text(text)
        print(f"格式化后:\n{formatted}")
    
    print("=== 文本格式化测试完成 ===\n")


def test_queue_mechanism():
    print("=== 测试队列机制 ===")
    
    root = tk.Tk()
    root.withdraw()
    
    app = MainWindow(root)
    
    for after_id in app.after_ids[:]:
        try:
            root.after_cancel(after_id)
            app.after_ids.remove(after_id)
        except:
            pass
    
    test_texts = ["第一条字幕", "第二条字幕", "第三条字幕"]
    
    for text in test_texts:
        app.on_text_captured(text, datetime.datetime.now())
        print(f"添加到队列: {text}")
    
    print(f"队列大小: {len(app.text_queue)}")
    
    for _ in range(len(app.text_queue)):
        if app.text_queue:
            text, ts = app.text_queue.pop(0)
            print(f"从队列取出: {text}")
    
    print(f"队列大小: {len(app.text_queue)}")
    
    root.destroy()
    print("=== 队列机制测试完成 ===\n")


def test_copy_functionality():
    print("=== 测试复制功能 ===")
    
    import pyperclip
    
    root = tk.Tk()
    root.withdraw()
    
    app = MainWindow(root)
    
    for after_id in app.after_ids[:]:
        try:
            root.after_cancel(after_id)
            app.after_ids.remove(after_id)
        except:
            pass
    
    test_project = SubtitleProject("复制测试", "copy_test.md")
    test_project.content = "# 测试文档\n\n这是一段Markdown内容。\n\n**加粗文本**\n\n- 列表项1\n- 列表项2"
    app.projects.append(test_project)
    app.current_project = test_project
    
    app.editor_text_box.insert(tk.END, test_project.content)
    
    app.copy_document_content()
    
    clipboard_content = pyperclip.paste()
    print(f"剪贴板内容:\n{clipboard_content}")
    
    assert clipboard_content == test_project.content, "复制内容不一致！"
    print("复制功能测试通过！")
    
    root.destroy()
    print("=== 复制功能测试完成 ===\n")


def test_auto_add_functionality():
    print("=== 测试自动添加功能 ===")
    
    root = tk.Tk()
    root.withdraw()
    
    app = MainWindow(root)
    
    for after_id in app.after_ids[:]:
        try:
            root.after_cancel(after_id)
            app.after_ids.remove(after_id)
        except:
            pass
    
    test_project = SubtitleProject("自动添加测试", "auto_test.md")
    app.projects.append(test_project)
    app.current_project = test_project
    app.auto_add_enabled = True
    
    initial_content = app.current_project.content
    print(f"初始内容: '{initial_content}'")
    
    test_subtitles = ["第一句字幕内容。", "第二句字幕内容！", "第三句字幕内容？"]
    
    for subtitle in test_subtitles:
        app.on_text_captured(subtitle, datetime.datetime.now())
        time.sleep(0.05)
    
    app.schedule_process_queue()
    root.update()
    
    final_content = app.current_project.content
    print(f"最终内容:\n{final_content}")
    
    assert len(final_content) > len(initial_content), "内容没有增加！"
    print("自动添加功能测试通过！")
    
    root.destroy()
    print("=== 自动添加功能测试完成 ===\n")


def test_markdown_export():
    print("=== 测试Markdown导出功能 ===")
    
    root = tk.Tk()
    root.withdraw()
    
    app = MainWindow(root)
    
    for after_id in app.after_ids[:]:
        try:
            root.after_cancel(after_id)
            app.after_ids.remove(after_id)
        except:
            pass
    
    test_project = SubtitleProject("导出测试", "export_test.md")
    test_project.content = "# 导出内容\n\n这是要导出的内容。\n\n> 引用文本"
    app.projects.append(test_project)
    app.current_project = test_project
    
    app.editor_text_box.insert(tk.END, test_project.content)
    
    success = test_project.save_to_markdown()
    print(f"导出结果: {'成功' if success else '失败'}")
    
    if os.path.exists("export_test.md"):
        with open("export_test.md", "r", encoding="utf-8") as f:
            content = f.read()
            print(f"导出文件内容:\n{content}")
        
        assert "# 导出测试" in content, "标题缺失！"
        assert "这是要导出的内容" in content, "内容缺失！"
        print("导出功能测试通过！")
        
        os.remove("export_test.md")
    else:
        print("导出文件不存在！")
    
    root.destroy()
    print("=== Markdown导出测试完成 ===\n")


if __name__ == "__main__":
    print("=" * 60)
    print("Windows实时字幕捕获工具 v2.0 - 功能测试")
    print("=" * 60 + "\n")
    
    try:
        test_subtitle_project()
        test_text_formatting()
        test_queue_mechanism()
        test_copy_functionality()
        test_auto_add_functionality()
        test_markdown_export()
        
        print("=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        print("\n=" * 60)
        print("测试未完全通过")
        print("=" * 60)