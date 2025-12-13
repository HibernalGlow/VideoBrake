"""
AI 角色识别模块
使用 Gemini 1.5 Flash 识别 Coser 扮演的角色
"""

import google.generativeai as genai
from PIL import Image
import io
import json
from typing import List, Optional, Dict
import numpy as np
import cv2

from config import Config


class CharacterIdentifier:
    """角色识别器"""
    
    def __init__(self, api_key: str = None):
        """
        初始化识别器
        
        Args:
            api_key: Gemini API Key，如果不提供则从配置读取
        """
        self.api_key = api_key or Config.GEMINI_API_KEY
        
        if not self.api_key:
            raise ValueError("未提供 GEMINI_API_KEY")
        
        # 配置 Gemini
        genai.configure(api_key=self.api_key)
        
        # 初始化模型
        self.model = genai.GenerativeModel(
            model_name=Config.GEMINI_MODEL,
            generation_config={
                "temperature": 0.4,  # 降低随机性
                "top_p": 0.8,
                "top_k": 32,
                "max_output_tokens": 512,
            }
        )
        
        print(f"✓ AI 模型初始化完成: {Config.GEMINI_MODEL}")
    
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
        
        # 将帧转换为 PIL Image
        pil_images = []
        for frame in frames:
            # BGR -> RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb_frame)
            
            # 可选：压缩以节省上传时间
            if Config.UPLOAD_IMAGE_QUALITY < 100:
                buffer = io.BytesIO()
                pil_image.save(buffer, format='JPEG', quality=Config.UPLOAD_IMAGE_QUALITY)
                buffer.seek(0)
                pil_image = Image.open(buffer)
            
            pil_images.append(pil_image)
        
        # 构建提示词
        prompt = Config.AI_PROMPT_TEMPLATE
        
        # 发送请求
        try:
            # 构建内容列表（文本 + 多张图片）
            contents = [prompt] + pil_images
            
            response = self.model.generate_content(contents)
            
            # 解析响应
            result = self._parse_response(response.text)
            
            if result:
                print(f"  ✓ 识别成功: {result['character']} ({result['source']})")
            else:
                print("  ⚠ 解析响应失败")
            
            return result
            
        except Exception as e:
            print(f"  ❌ AI 识别失败: {e}")
            return None
    
    def _parse_response(self, response_text: str) -> Optional[Dict[str, str]]:
        """
        解析 AI 响应
        
        Args:
            response_text: AI 返回的文本
            
        Returns:
            解析后的字典，或 None
        """
        try:
            # 尝试直接解析 JSON
            # 清理可能的 markdown 代码块标记
            cleaned_text = response_text.strip()
            
            # 移除可能的 ```json 和 ``` 标记
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
        pil_images = []
        for path in image_paths:
            try:
                img = Image.open(path)
                pil_images.append(img)
            except Exception as e:
                print(f"  ⚠ 无法加载图片 {path}: {e}")
        
        if not pil_images:
            return None
        
        # 构建请求
        prompt = Config.AI_PROMPT_TEMPLATE
        contents = [prompt] + pil_images
        
        try:
            response = self.model.generate_content(contents)
            print(f"\n原始响应:\n{response.text}\n")
            return self._parse_response(response.text)
        except Exception as e:
            print(f"  ❌ 识别失败: {e}")
            return None


if __name__ == "__main__":
    # 测试代码
    import sys
    from pathlib import Path
    
    if not Config.validate():
        sys.exit(1)
    
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
    identifier = CharacterIdentifier()
    
    # 执行识别
    result = identifier.identify_test(valid_paths)
    
    if result:
        print("\n✓ 识别成功！")
        print(f"  角色: {result['character']}")
        print(f"  作品: {result['source']}")
    else:
        print("\n✗ 识别失败或未识别到角色")
