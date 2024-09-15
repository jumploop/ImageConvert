from __future__ import annotations

import argparse
import logging
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

from PIL import Image


class ImageFormat(Enum):
    PNG = 'PNG'
    JPEG = 'JPEG'
    GIF = 'GIF'
    BMP = 'BMP'
    WEBP = 'WEBP'


@dataclass
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
    IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
    WEBP_METHOD = 6

    def __init__(self, format: ImageFormat, quality: int = 85, recursive: bool = False,
                 maintain_structure: bool = False):
        self.format = format
        self.quality = quality
        self.recursive = recursive
        self.maintain_structure = maintain_structure
        self.logger = self._setup_logger()
        self.stats = ConversionStats()

    @staticmethod
    def _setup_logger() -> logging.Logger:
        logger = logging.getLogger('ImageConverter')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def convert_image(self, input_path: Path, output_dir: Path) -> ConversionResult:
        try:
            with Image.open(input_path) as img:
                if img.mode == 'RGBA' and self.format in {ImageFormat.JPEG, ImageFormat.WEBP}:
                    img = img.convert('RGB')

                full_output_dir = output_dir / input_path.relative_to(
                    self.input_dir).parent if self.maintain_structure else output_dir
                full_output_dir.mkdir(parents=True, exist_ok=True)
                output_path = full_output_dir / f"{input_path.stem}.{self.format.value.lower()}"

                save_kwargs: Dict[str, int] = {'quality': self.quality}
                if self.format == ImageFormat.WEBP:
                    save_kwargs['method'] = self.WEBP_METHOD

                img.save(output_path, self.format.value, **save_kwargs)
            return ConversionResult(input_path, output_path, True)
        except Exception as e:
            return ConversionResult(input_path, None, False, str(e))

    def process_files(self, files: List[Path], output_dir: Path) -> None:
        with ThreadPoolExecutor() as executor:
            futures = {executor.submit(self.convert_image, f, output_dir): f for f in files}
            for future in as_completed(futures):
                result = future.result()
                self.stats.update(result)
                self._log_result(result)

    def _log_result(self, result: ConversionResult) -> None:
        if result.success:
            self.logger.info(f"已成功转换: {result.input_path} -> {result.output_path}")
        else:
            self.logger.warning(f"转换失败: {result.input_path}. 错误: {result.error_message}")

    def get_image_files(self, directory: Path) -> List[Path]:
        glob_pattern: str = '**/*' if self.recursive else '*'
        return [f for f in directory.glob(glob_pattern) if f.is_file() and f.suffix.lower() in self.IMAGE_EXTENSIONS]

    def run(self, input_path: Path, output_path: Path) -> None:
        self.input_dir = input_path if input_path.is_dir() else input_path.parent
        output_path.mkdir(parents=True, exist_ok=True)

        files = [input_path] if input_path.is_file() else self.get_image_files(input_path)
        self.stats.total = len(files)

        self.process_files(files, output_path)
        self.logger.info(self.stats.summary())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="批量图片格式转换工具 (支持WebP和递归处理)")
    parser.add_argument("-i", "--input", type=Path, help="输入文件或目录路径")
    parser.add_argument("-f", "--format", type=lambda x: ImageFormat[x.upper()], help="目标格式 (PNG, JPEG, GIF, BMP, WEBP)")
    parser.add_argument("-o", "--output", type=Path, default=Path("converted"),
                        help="输出目录 (默认为当前目录下的 'converted' 文件夹)")
    parser.add_argument("-q", "--quality", type=int, choices=range(1, 101), metavar="[1-100]", default=85,
                        help="JPEG和WebP质量 (1-100, 默认85)")
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
