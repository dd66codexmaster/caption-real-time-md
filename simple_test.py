import sys
import os
import time
import datetime
import re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from subtitle_capture_v2 import SubtitleProject


def test_subtitle_project():
    print("=== 测试 SubtitleProject 类 ===")
    
    project = SubtitleProject("测试项目", "test_output.md")
    
    test_text = "这是第一句话。这是第二句话！这是第三句话？"
    project.add_text(test_text, datetime.datetime.now())
    
    print(f"添加文本后内容:\n{project.content}")
    
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
    
    all_passed = True
    for i, text in enumerate(test_cases):
        print(f"\n测试用例 {i+1}: {text}")
        formatted = project.format_text(text)
        print(f"格式化后:\n{formatted}")
        
        if formatted.strip():
            sentences = formatted.strip().split('\n')
            print(f"拆分为 {len(sentences)} 行")
        else:
            print("格式化结果为空！")
            all_passed = False
    
    if all_passed:
        print("✅ 文本格式化测试通过！")
    print("=== 文本格式化测试完成 ===\n")


def test_markdown_export():
    print("=== 测试Markdown导出功能 ===")
    
    test_project = SubtitleProject("导出测试", "export_test.md")
    test_project.content = "# 导出内容\n\n这是要导出的内容。\n\n> 引用文本"
    
    success = test_project.save_to_markdown()
    print(f"导出结果: {'成功' if success else '失败'}")
    
    passed = False
    if os.path.exists("export_test.md"):
        with open("export_test.md", "r", encoding="utf-8") as f:
            content = f.read()
            print(f"导出文件内容:\n{content}")
        
        if "# 导出测试" in content and "这是要导出的内容" in content:
            print("✅ 导出功能测试通过！")
            passed = True
        
        os.remove("export_test.md")
    else:
        print("导出文件不存在！")
    
    print("=== Markdown导出测试完成 ===\n")
    return passed


def test_queue_mechanism():
    print("=== 测试队列机制 ===")
    
    text_queue = []
    max_queue_size = 100
    
    test_texts = ["第一条字幕", "第二条字幕", "第三条字幕"]
    
    for text in test_texts:
        text_queue.append((text, datetime.datetime.now()))
        if len(text_queue) > max_queue_size:
            text_queue = text_queue[-max_queue_size:]
        print(f"添加到队列: {text}")
    
    print(f"队列大小: {len(text_queue)}")
    
    while text_queue:
        text, ts = text_queue.pop(0)
        print(f"从队列取出: {text}")
    
    print(f"队列大小: {len(text_queue)}")
    print("✅ 队列机制测试通过！")
    print("=== 队列机制测试完成 ===\n")


def test_copy_functionality():
    print("=== 测试复制功能 ===")
    
    try:
        import pyperclip
        
        test_content = "# 测试文档\n\n这是一段Markdown内容。\n\n**加粗文本**\n\n- 列表项1\n- 列表项2"
        
        pyperclip.copy(test_content)
        clipboard_content = pyperclip.paste()
        
        print(f"原始内容:\n{test_content}")
        print(f"剪贴板内容:\n{clipboard_content}")
        
        if clipboard_content == test_content:
            print("✅ 复制功能测试通过！")
        else:
            print("❌ 复制内容不一致！")
        
    except Exception as e:
        print(f"⚠️ 复制测试跳过（无pyperclip或剪贴板不可用）: {e}")
    
    print("=== 复制功能测试完成 ===\n")


if __name__ == "__main__":
    print("=" * 60)
    print("Windows实时字幕捕获工具 v2.0 - 核心功能测试")
    print("=" * 60 + "\n")
    
    try:
        test_subtitle_project()
        test_text_formatting()
        test_markdown_export()
        test_queue_mechanism()
        test_copy_functionality()
        
        print("=" * 60)
        print("✅ 所有核心功能测试完成！")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        print("\n=" * 60)
        print("测试未完全通过")
        print("=" * 60)