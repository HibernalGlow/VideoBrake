"""
AI 角色识别模块
使用 Gemini CLI 命令行工具识别 Coser 扮演的角色
"""

import subprocess
import json
import tempfile
import shutil
from pathlib import Path
from typing import List, Optional, Dict
import numpy as np
import cv2
from PIL import Image

from config import Config


class CharacterIdentifier:
    """角色识别器（使用 Gemini CLI）"""
    
    def __init__(self, cli_path: str = None):
        """
        初始化识别器
        
        Args:
            cli_path: gemini CLI 工具路径，如果不提供则从配置读取
        """
        self.cli_path = cli_path or Config.GEMINI_CLI_PATH
        
        # 验证 CLI 工具是否可用
        if not self._check_cli_available():
            raise RuntimeError(
                "Gemini CLI 工具不可用！\n"
                "请确保已安装 gemini CLI 并配置正确。\n"
                "安装方法: npm install -g @google/generative-ai-cli"
            )
        
        print(f"✓ Gemini CLI 初始化完成: {self.cli_path}")
    
    def _check_cli_available(self) -> bool:
        """检查 CLI 工具是否可用"""
        try:
            result = subprocess.run(
                [self.cli_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def identify_from_frames(
        self, 
        frames: List[np.ndarray]
    ) -> Optional[Dict[str, str]]:
        """
        从多个帧中识别角色
        
        Args:
            frames: 帧列表 (BGR 格式的 numpy 数组)
            
        Returns:
            识别结果字典，格式：
            {
                "character": "角色名",
                "source": "作品名"
            }
            如果识别失败返回 None
        """
        if not frames:
            print("  ⚠ 没有可用的帧进行识别")
            return None
        
        print(f"\n🤖 开始 AI 识别（使用 {len(frames)} 张图片）...")
        
        # 创建临时目录保存图片
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            image_paths = []
            
            # 保存所有帧为临时图片
            for i, frame in enumerate(frames):
                img_path = temp_path / f"frame_{i}.jpg"
                
                # 保存图片
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), Config.UPLOAD_IMAGE_QUALITY]
                cv2.imwrite(str(img_path), frame, encode_param)
                image_paths.append(str(img_path))
            
            # 调用 CLI 进行识别
            result = self._call_gemini_cli(image_paths)
            
            if result:
                print(f"  ✓ 识别成功: {result['character']} ({result['source']})")
            else:
                print("  ⚠ 识别失败")
            
            return result
    
    def _call_gemini_cli(self, image_paths: List[str]) -> Optional[Dict[str, str]]:
        """
        调用 Gemini CLI 进行识别
        
        Args:
            image_paths: 图片路径列表
            
        Returns:
            识别结果字典
        """
        try:
            # 构建命令
            cmd = [
                self.cli_path,
                "generate",
                "--model", Config.GEMINI_MODEL,
                "--prompt", Config.AI_PROMPT_TEMPLATE,
                "--output-format", "json",
            ]
            
            # 添加图片参数
            for img_path in image_paths:
                cmd.extend(["--image", img_path])
            
            # 如果配置了 API Key，添加到环境变量
            env = None
            if Config.GEMINI_API_KEY:
                import os
                env = os.environ.copy()
                env["GEMINI_API_KEY"] = Config.GEMINI_API_KEY
            
            # 执行命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=Config.CLI_TIMEOUT,
                env=env
            )
            
            if result.returncode != 0:
                print(f"  ❌ CLI 调用失败: {result.stderr}")
                return None
            
            # 解析输出
            return self._parse_response(result.stdout)
            
        except subprocess.TimeoutExpired:
            print("  ❌ CLI 调用超时")
            return None
        except Exception as e:
            print(f"  ❌ CLI 调用异常: {e}")
            return None
    
    def _parse_response(self, response_text: str) -> Optional[Dict[str, str]]:
        """
        解析 CLI 响应
        
        Args:
            response_text: CLI 返回的文本
            
        Returns:
            解析后的字典，或 None
        """
        try:
            # 清理输出
            cleaned_text = response_text.strip()
            
            # 移除可能的 markdown 代码块标记
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            elif cleaned_text.startswith("```"):
                cleaned_text = cleaned_text[3:]
            
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]
            
            cleaned_text = cleaned_text.strip()
            
            # 解析 JSON
            result = json.loads(cleaned_text)
            
            # 验证必需字段
            if "character" in result and "source" in result:
                # 过滤"未知"结果
                if result["character"] == "未知" or result["character"].lower() == "unknown":
                    return None
                
                return {
                    "character": result["character"],
                    "source": result["source"]
                }
            
            return None
            
        except json.JSONDecodeError:
            # JSON 解析失败，尝试文本解析
            print(f"  ⚠ JSON 解析失败，原始响应: {response_text[:200]}")
            return self._fallback_parse(response_text)
    
    def _fallback_parse(self, text: str) -> Optional[Dict[str, str]]:
        """
        备用解析方法（当 JSON 解析失败时）
        
        Args:
            text: 响应文本
            
        Returns:
            尝试从文本中提取角色信息
        """
        # 简单的关键词匹配
        lines = text.lower().split('\n')
        
        character = None
        source = None
        
        for line in lines:
            if 'character' in line or '角色' in line:
                # 尝试提取冒号后的内容
                parts = line.split(':', 1)
                if len(parts) == 2:
                    character = parts[1].strip().strip('"').strip("'")
            
            if 'source' in line or '作品' in line or '来源' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    source = parts[1].strip().strip('"').strip("'")
        
        if character and source:
            return {"character": character, "source": source}
        
        return None
    
    def identify_test(self, image_paths: List[str]) -> Optional[Dict[str, str]]:
        """
        测试方法：从图片文件路径识别
        
        Args:
            image_paths: 图片文件路径列表
            
        Returns:
            识别结果
        """
        # 验证图片存在
        valid_paths = []
        for path in image_paths:
            if Path(path).exists():
                valid_paths.append(path)
            else:
                print(f"  ⚠ 文件不存在: {path}")
        
        if not valid_paths:
            return None
        
        # 调用 CLI
        result = self._call_gemini_cli(valid_paths)
        
        if result:
            print(f"\n✓ 识别成功！")
            print(f"  角色: {result['character']}")
            print(f"  作品: {result['source']}")
        
        return result


if __name__ == "__main__":
    # 测试代码
    import sys
    from pathlib import Path
    
    if len(sys.argv) < 2:
        print("用法: python character_identifier.py <图片路径1> [图片路径2] ...")
        sys.exit(1)
    
    image_paths = sys.argv[1:]
    
    # 验证文件存在
    valid_paths = []
    for path in image_paths:
        if Path(path).exists():
            valid_paths.append(path)
        else:
            print(f"⚠ 文件不存在: {path}")
    
    if not valid_paths:
        print("❌ 没有有效的图片文件")
        sys.exit(1)
    
    # 创建识别器
    try:
        identifier = CharacterIdentifier()
    except RuntimeError as e:
        print(f"❌ {e}")
        sys.exit(1)
    
    # 执行识别
    result = identifier.identify_test(valid_paths)
    
    if not result:
        print("\n✗ 识别失败或未识别到角色")
