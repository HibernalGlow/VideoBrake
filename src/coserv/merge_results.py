"""
合并各文件夹的识别结果
读取每个视频文件夹下的 result.json，合并生成 results.json
"""

import json
from pathlib import Path


def merge_results(output_dir="output"):
    """合并识别结果"""
    output_path = Path(output_dir)
    pending_file = output_path / "pending.json"
    
    if not pending_file.exists():
        print(f"❌ 找不到 {pending_file}")
        return
    
    # 加载待识别清单
    with open(pending_file, 'r', encoding='utf-8') as f:
        pending_list = json.load(f)
    
    print("="*60)
    print("📦 合并识别结果")
    print("="*60)
    
    results = []
    identified_count = 0
    pending_count = 0
    
    for item in pending_list:
        video_name = item['video_name']
        video_path = item['video_path']
        frames_dir = item['frames_dir']
        
        # 检查是否有 result.json
        result_file = output_path / Path(frames_dir).parent / "result.json"
        
        if result_file.exists():
            # 读取识别结果
            try:
                with open(result_file, 'r', encoding='utf-8') as f:
                    character_info = json.load(f)
                
                # 验证格式
                if 'character' in character_info and 'source' in character_info:
                    print(f"✓ {video_name}: {character_info['character']} ({character_info['source']})")
                    
                    results.append({
                        "video_name": video_name,
                        "video_path": video_path,
                        "frames_dir": frames_dir,
                        "frames": item['frames'],
                        "frame_count": item['frame_count'],
                        "status": "identified",
                        "character_info": {
                            "character": character_info['character'],
                            "source": character_info['source']
                        },
                        "confidence": character_info.get('confidence', 'unknown')
                    })
                    identified_count += 1
                else:
                    print(f"⚠ {video_name}: result.json 格式错误")
                    results.append({
                        **item,
                        "status": "pending",
                        "character_info": None
                    })
                    pending_count += 1
            except Exception as e:
                print(f"❌ {video_name}: 读取失败 - {e}")
                results.append({
                    **item,
                    "status": "pending",
                    "character_info": None
                })
                pending_count += 1
        else:
            print(f"⏭ {video_name}: 未找到 result.json")
            results.append({
                **item,
                "status": "pending",
                "character_info": None
            })
            pending_count += 1
    
    # 保存合并结果
    results_file = output_path / "results.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print("\n" + "="*60)
    print("📊 合并统计")
    print("="*60)
    print(f"总视频数: {len(results)}")
    print(f"✓ 已识别: {identified_count}")
    print(f"⏭ 待识别: {pending_count}")
    print(f"\n✓ 结果已保存: {results_file}")
    print("="*60)
    
    print("\n📝 下一步：运行整理脚本")
    print(f"python organize.py \"{Path(item['video_path']).parent}\" --dry-run")


if __name__ == "__main__":
    merge_results()
