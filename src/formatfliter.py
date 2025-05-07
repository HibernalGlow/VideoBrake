import os
import concurrent.futures
import time
from pathlib import Path
import sys
import click
import pyperclip
from prompt_toolkit import prompt
from prompt_toolkit.shortcuts import radiolist_dialog
from prompt_toolkit.formatted_text import HTML

def normalize_path(path):
    # 处理复制粘贴的路径，移除引号，处理转义字符
    path = path.strip('" \'')  # 移除首尾的引号和空格
    return os.path.normpath(path)  # 标准化路径分隔符

def process_single_file(file_path, add_nov=True):
    try:
        # 获取原始文件的时间戳
        stat = os.stat(file_path)
        atime = stat.st_atime  # 访问时间
        mtime = stat.st_mtime  # 修改时间
        
        # 根据操作类型重命名文件
        new_path = file_path + '.nov' if add_nov else file_path[:-4]
        os.rename(file_path, new_path)
        
        # 恢复时间戳
        os.utime(new_path, (atime, mtime))
        return True, file_path
    except Exception as e:
        return False, f'错误 {file_path}: {e}'

def find_video_files(directory):
    # 支持的视频格式
    video_extensions = ('.mp4', '.avi', '.mkv', '.wmv', '.mov', '.flv', '.webm', '.m4v','.ts','.mts')
    hb_prefix = '[#hb]'

    print("正在扫描文件...")
    nov_files = []
    normal_files = []
    hb_files = []

    # 使用os.walk快速遍历目录
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            file_lower = file.lower()

            if file_lower.endswith('.nov'):
                # 检查.nov文件的原始扩展名是否为视频格式
                base_name = file[:-4]
                if any(base_name.lower().endswith(ext) for ext in video_extensions):
                    nov_files.append(file_path)
            elif file.startswith(hb_prefix):
                 # 检查带 [#hb] 前缀的文件是否为视频格式 (检查去除前缀后的部分)
                base_name_with_ext = file[len(hb_prefix):]
                if any(base_name_with_ext.lower().endswith(ext) for ext in video_extensions):
                    hb_files.append(file_path)
            else:
                # 检查普通文件是否为视频格式
                if any(file_lower.endswith(ext) for ext in video_extensions):
                    normal_files.append(file_path)

    return nov_files, normal_files, hb_files

def check_and_save_duplicates(directory, nov_files, normal_files, hb_files):
    """检查[#hb]文件对应的无前缀文件，并保存无前缀文件路径"""
    if not hb_files:
        print("\n没有找到带 [#hb] 前缀的视频文件，无需检查。")
        return # 没有带[#hb]前缀的文件，无需检查

    hb_prefix = '[#hb]'
    duplicate_non_hb_files = []
    non_hb_lookup = {} # {(directory, base_name_without_ext): full_path}

    # 建立无前缀文件的查找字典
    for f in normal_files:
        p = Path(f)
        key = (str(p.parent), p.stem)
        non_hb_lookup[key] = f
    for f in nov_files:
        p = Path(f)
        original_name_path = Path(p.stem) # 获取 .nov 前的文件名（含原始扩展名）
        key = (str(p.parent), original_name_path.stem) # 获取不含扩展名的基础名
        # 存储的是添加 .nov 前的原始路径
        non_hb_lookup[key] = f[:-4]

    # 查找匹配项
    for hb_file in hb_files:
        hb_path = Path(hb_file)
        hb_dir = str(hb_path.parent)
        hb_name = hb_path.name
        # 去掉[#hb]前缀，获取基础名（不含扩展名）
        base_name_with_ext = hb_name[len(hb_prefix):]
        base_name_without_ext = Path(base_name_with_ext).stem
        lookup_key = (hb_dir, base_name_without_ext)

        if lookup_key in non_hb_lookup:
            duplicate_non_hb_files.append(non_hb_lookup[lookup_key])

    # 保存结果
    if duplicate_non_hb_files:
        output_filename = 'duplicate_videos.txt'
        output_path = os.path.join(directory, output_filename) # 保存在处理目录的根目录
        try:
            # 去重并排序
            unique_duplicates = sorted(list(set(duplicate_non_hb_files)))
            with open(output_path, 'w', encoding='utf-8') as f:
                for file_path in unique_duplicates:
                    f.write(file_path + '\n')
            print(f"\n发现 {len(unique_duplicates)} 个对应的无前缀文件，列表已保存到: {output_path}")
        except Exception as e:
            print(f"\n错误：无法写入重复文件列表到 {output_path}: {e}")
    else:
        print("\n未发现 [#hb] 文件对应的无前缀重复文件。")


def process_videos(directory):
    # 快速搜索文件
    nov_files, normal_files, hb_files = find_video_files(directory)

    print(f"找到 {len(normal_files)} 个普通视频文件")
    print(f"找到 {len(nov_files)} 个.nov视频文件")
    print(f"找到 {len(hb_files)} 个 [#hb] 前缀视频文件")

    # 使用prompt_toolkit的radiolist_dialog实现可点击的选择界面
    choice = radiolist_dialog(
        title="选择操作",
        text="请用鼠标或方向键选择要执行的操作：",
        values=[
            ("1", "添加.nov后缀"),
            ("2", "恢复原始文件名"),
            ("3", "检查[#hb]重复项"), # 新增选项
            ("q", "退出程序")
        ],
        default="2" # 可以根据需要调整默认选项
    ).run()

    if choice == 'q' or choice is None:  # None表示用户按了Esc或关闭窗口
        print("操作已取消。")
        return

    # 根据选择执行操作
    if choice == '1':
        files_to_process = normal_files
        add_nov = True
        action_desc = "添加.nov后缀"
    elif choice == '2':
        files_to_process = nov_files
        add_nov = False
        action_desc = "恢复原始文件名"
    elif choice == '3':
        # 只执行检查重复项的操作
        print("\n开始检查 [#hb] 重复项...")
        check_and_save_duplicates(directory, nov_files, normal_files, hb_files)
        print("检查完成。")
        return # 检查完成后直接返回
    else:
        print("无效的选择。")
        return

    # --- 文件处理逻辑 (仅用于选项 1 和 2) ---
    total_files = len(files_to_process)
    if total_files == 0:
        print(f"\n没有找到需要执行 '{action_desc}' 操作的文件！")
        return

    # 使用线程池处理文件
    start_time = time.time()
    print(f"\n开始 {action_desc}，处理 {total_files} 个文件...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(32, os.cpu_count() * 4)) as executor:
        futures = [executor.submit(process_single_file, file, add_nov) for file in files_to_process]

        # 收集处理结果并显示进度
        success_count = 0
        completed = 0
        for future in concurrent.futures.as_completed(futures):
            success, result = future.result()
            completed += 1
            if completed % 10 == 0 or completed == total_files:  # 每10个文件更新一次进度
                print(f"\r进度: {completed}/{total_files} ({(completed/total_files*100):.1f}%)\t", end="")

            if success:
                success_count += 1
            else:
                print(f"\n{result}") # 换行打印错误信息

    end_time = time.time()
    print(f'\n\n{action_desc} 完成！')
    print(f'成功处理: {success_count}/{total_files} 个文件')
    print(f'总耗时: {end_time - start_time:.2f} 秒')


@click.command()
@click.option('-c', is_flag=True, help='从剪贴板读取路径')
def main(c):
    """视频文件格式批量处理工具"""
    if c:
        # 从剪贴板读取路径
        clipboard_content = pyperclip.paste()
        # 分割多行路径
        paths = [p.strip() for p in clipboard_content.splitlines() if p.strip()]
        if not paths:
            print("剪贴板中没有有效的路径！")
            return
    else:
        # 使用prompt_toolkit的prompt实现更好的输入体验
        default_path = r'E:\1EHV' # 可以修改为更常用的默认路径或留空
        input_path = prompt(
            HTML('<b>请输入要处理的路径: </b>'),
            default=default_path,
            mouse_support=True
        ).strip()
        if not input_path and default_path:
             input_path = default_path # 如果用户直接回车且有默认值，则使用默认值
        elif not input_path:
             print("请输入一个有效的路径。")
             return

        paths = [input_path]

    for path in paths:
        path = normalize_path(path)
        if not os.path.exists(path):
            print(f"路径不存在: {path}")
            continue
        if not os.path.isdir(path):
            print(f"提供的路径不是一个目录: {path}")
            continue

        print(f"\n处理目录: {path}")
        process_videos(path)

if __name__ == '__main__':
    main()