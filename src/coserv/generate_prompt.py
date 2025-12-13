"""
生成Gemini识别指令
输出完整的prompt，让用户直接复制到Gemini CLI
"""

import json
from pathlib import Path


def generate_instructions(output_dir="output"):
    """生成识别指令"""
    output_path = Path(output_dir)
    pending_file = output_path / "pending.json"
    
    if not pending_file.exists():
        print(f"❌ 找不到 {pending_file}")
        return
    
    # 加载待识别清单
    with open(pending_file, 'r', encoding='utf-8') as f:
        pending_list = json.load(f)
    
    print("="*70)
    print("📋 Gemini 识别指令生成器")
    print("="*70)
    print(f"\n找到 {len(pending_list)} 个视频待识别\n")
    
    # 生成完整的识别prompt
    print("="*70)
    print("请将以下内容复制到 Gemini CLI 中：")
    print("="*70)
    print()
    
    # 基础说明
    base_prompt = """我需要你帮我批量识别Coser视频中的角色。

对于每个视频，我会给你提供几张截图，请你：
1. 识别出角色的名字和所属作品/游戏
2. 如果无法确定具体角色，返回 "未知"
3. 将识别结果写入对应文件夹的 result.json 文件

JSON格式要求（严格遵守）：
{
  "character": "角色名",
  "source": "作品名",
  "confidence": "high/medium/low"
}

开始识别：
"""
    
    print(base_prompt)
    print("-"*70)
    
    # 为每个视频生成指令
    for i, item in enumerate(pending_list, 1):
        video_name = item['video_name']
        frames_dir = output_path / item['frames_dir']
        result_file = frames_dir.parent / "result.json"
        
        print(f"\n## 视频 {i}/{len(pending_list)}: {video_name}")
        print(f"\n请查看这些截图并识别角色：")
        
        # 列出所有截图
        for frame in item['frames'][:3]:  # 只显示前3张
            frame_path = output_path / frame
            print(f"- {frame_path.absolute()}")
        
        print(f"\n识别后，请将结果保存到：")
        print(f"{result_file.absolute()}")
        print()
        print("-"*70)
    
    print("\n" + "="*70)
    print("📝 完成所有识别后，运行以下命令合并结果：")
    print("="*70)
    print(f"python merge_results.py")
    print()


if __name__ == "__main__":
    generate_instructions()
