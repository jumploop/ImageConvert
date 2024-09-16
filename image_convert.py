from __future__ import annotations

import argparse
import logging
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, Optional

import multiprocessing
from PIL import Image

class ImageFormat(Enum):
    PNG = 'png'
    JPEG = 'jpeg'
    JPG = 'jpg'
    GIF = 'gif'
    BMP = 'bmp'
    WEBP = 'webp'
    TIFF = 'tiff'
    ICO = 'ico'
    PPM = 'ppm'
    HEIC = 'heic'

    @classmethod
    def from_string(cls, s: str) -> ImageFormat:
        return cls.JPEG if s.lower() == 'jpg' else cls(s.lower())

@dataclass(frozen=True)
class ConversionResult:
    input_path: Path
    output_path: Optional[Path]
    success: bool
    error_message: str = ''

@dataclass
class ConversionStats:
    total: int = 0
    success: int = 0
    failed: int = 0
    start_time: float = field(default_factory=time.time)

    def update(self, result: ConversionResult) -> None:
        self.success += result.success
        self.failed += not result.success

    def summary(self) -> str:
        duration = time.time() - self.start_time
        return (f"转换完成。摘要:\n"
                f"总文件数: {self.total}\n"
                f"成功转换: {self.success}\n"
                f"转换失败: {self.failed}\n"
                f"总耗时: {duration:.2f} 秒")

class ImageConverter:
    IMAGE_EXTENSIONS = {f'.{fmt.value}' for fmt in ImageFormat}

    def __init__(self, format: ImageFormat, quality: int = 85, recursive: bool = False, maintain_structure: bool = False):
        self.format = format
        self.recursive = recursive
        self.maintain_structure = maintain_structure
        self.quality = quality
        self.logger = self._setup_logger()
        self.stats = ConversionStats()
        self.save_params = self._get_save_params()

    @staticmethod
    def _setup_logger() -> logging.Logger:
        logger = logging.getLogger('ImageConverter')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
        return logger

    def _get_save_params(self) -> Dict[str, int]:
        params = {'quality': self.quality} if self.format in {ImageFormat.JPEG, ImageFormat.JPG, ImageFormat.WEBP} else {}
        if self.format == ImageFormat.WEBP:
            params['method'] = 6
        return params

    def convert_image(self, input_path: Path, output_path: Path) -> ConversionResult:
        try:
            with Image.open(input_path) as img:
                if img.mode == 'RGBA' and self.format in {ImageFormat.JPEG, ImageFormat.JPG}:
                    img = img.convert('RGB')
                img.save(output_path, self.format.value.upper(), **self.save_params)
            return ConversionResult(input_path, output_path, True)
        except Exception as e:
            return ConversionResult(input_path, None, False, str(e))

    def _handle_result(self, result: ConversionResult) -> None:
        self.stats.update(result)
        log_func = self.logger.info if result.success else self.logger.warning
        message = f"{'已成功转换' if result.success else '转换失败'}: {result.input_path}"
        if result.output_path:
            message += f" -> {result.output_path}"
        if result.error_message:
            message += f". 错误: {result.error_message}"
        log_func(message)

    def run(self, input_path: Path, output_path: Path) -> None:
        self.input_path = input_path
        output_path.mkdir(parents=True, exist_ok=True)
        files = self._get_files()
        self.stats.total = len(files)

        with ThreadPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
            futures = [executor.submit(self.convert_image, f, self._get_output_path(f, output_path)) for f in files]
            for future in as_completed(futures):
                self._handle_result(future.result())

        self.logger.info(self.stats.summary())

    def _get_files(self) -> list[Path]:
        if self.input_path.is_file():
            return [self.input_path]
        pattern = '**/*' if self.recursive else '*'
        return [f for f in self.input_path.glob(pattern) if f.is_file() and f.suffix.lower() in self.IMAGE_EXTENSIONS]

    def _get_output_path(self, input_path: Path, base_output_path: Path) -> Path:
        if not self.maintain_structure:
            return base_output_path / f"{input_path.stem}.{self.format.value}"
        relative_path = input_path.relative_to(self.input_path)
        output_dir = base_output_path / relative_path.parent
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir / f"{input_path.stem}.{self.format.value}"

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="批量图片格式转换工具 (支持多种图片格式和递归处理)")
    parser.add_argument("-i", "--input", type=Path, help="输入文件或目录路径")
    parser.add_argument("-f", "--format", type=ImageFormat.from_string, help="目标格式 (PNG, JPEG, JPG, GIF, BMP, WEBP, TIFF, ICO, PPM, HEIC)")
    parser.add_argument("-o", "--output", type=Path, default=Path("converted"), help="输出目录 (默认为当前目录下的 'converted' 文件夹)")
    parser.add_argument("-q", "--quality", type=int, choices=range(1, 101), metavar="[1-100]", default=85, help="JPEG/JPG和WebP质量 (1-100, 默认85)")
    parser.add_argument("-r", "--recursive", action="store_true", help="递归处理子目录")
    parser.add_argument("-m", "--maintain-structure", action="store_true", help="保持原目录结构")
    return parser.parse_args()

def main() -> None:
    args = parse_args()
    try:
        converter = ImageConverter(args.format, args.quality, args.recursive, args.maintain_structure)
        converter.run(args.input.resolve(), args.output.resolve())
    except Exception as e:
        print(f"发生未知错误: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
