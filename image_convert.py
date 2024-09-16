from __future__ import annotations

import argparse
import logging
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Iterator, Callable

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
        try:
            return cls(s.lower())
        except ValueError:
            if s.lower() == 'jpg':
                return cls.JPEG
            raise ValueError(f"Unsupported format: {s}")

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

def rgba_to_rgb(img: Image.Image) -> Image.Image:
    return img.convert('RGB') if img.mode == 'RGBA' else img

def get_files(path: Path, recursive: bool, extensions: set[str]) -> Iterator[Path]:
    if path.is_file():
        yield path
    else:
        glob_pattern = '**/*' if recursive else '*'
        yield from (f for f in path.glob(glob_pattern) if f.is_file() and f.suffix.lower() in extensions)

class ImageConverter:
    IMAGE_EXTENSIONS = {f'.{fmt.value}' for fmt in ImageFormat}

    def __init__(self, format: ImageFormat, quality: int = 85, recursive: bool = False, maintain_structure: bool = False):
        self.format = format
        self.recursive = recursive
        self.maintain_structure = maintain_structure
        self.quality = quality
        self.logger = logging.getLogger('ImageConverter')
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        self.stats = ConversionStats()
        self.process_image = rgba_to_rgb if format in {ImageFormat.JPEG, ImageFormat.JPG, ImageFormat.WEBP} else lambda x: x

    def convert_image(self, input_path: Path, output_dir: Path) -> ConversionResult:
        try:
            with Image.open(input_path) as img:
                img = self.process_image(img)
                output_path = self._get_output_path(input_path, output_dir)
                save_kwargs = {'quality': self.quality} if self.format in {ImageFormat.JPEG, ImageFormat.JPG, ImageFormat.WEBP} else {}
                if self.format == ImageFormat.WEBP:
                    save_kwargs['method'] = 6
                img.save(output_path, self.format.value.upper(), **save_kwargs)
            return ConversionResult(input_path, output_path, True)
        except Exception as e:
            return ConversionResult(input_path, None, False, str(e))

    def _get_output_path(self, input_path: Path, output_dir: Path) -> Path:
        relative_path = input_path.relative_to(self.input_dir) if self.maintain_structure else input_path.name
        full_output_dir = output_dir / relative_path.parent if self.maintain_structure else output_dir
        full_output_dir.mkdir(parents=True, exist_ok=True)
        return full_output_dir / f"{input_path.stem}.{self.format.value}"

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
        self.input_dir = input_path if input_path.is_dir() else input_path.parent
        output_path.mkdir(parents=True, exist_ok=True)

        files = list(get_files(input_path, self.recursive, self.IMAGE_EXTENSIONS))
        self.stats.total = len(files)

        with ThreadPoolExecutor(max_workers=multiprocessing.cpu_count() * 2) as executor:
            futures = [executor.submit(self.convert_image, f, output_path) for f in files]
            for future in as_completed(futures):
                self._handle_result(future.result())

        self.logger.info(self.stats.summary())

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
