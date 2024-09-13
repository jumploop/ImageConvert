from pathlib import Path
from PIL import Image
import argparse
from concurrent.futures import ThreadPoolExecutor
from typing import List


class ImageConverter:
    def __init__(self, format: str, quality: int = 85, recursive: bool = False, maintain_structure: bool = False):
        self.format = format.upper()
        self.quality = quality
        self.recursive = recursive
        self.maintain_structure = maintain_structure

    def convert_image(self, input_path: Path, output_dir: Path) -> None:
        """
        将单个图片从一种格式转换为另一种格式，包括WebP
        """
        try:
            with Image.open(input_path) as img:
                if img.mode == 'RGBA' and self.format in ['JPEG', 'WEBP']:
                    img = img.convert('RGB')

                if self.maintain_structure:
                    rel_path = input_path.relative_to(self.input_dir)
                    full_output_dir = output_dir / rel_path.parent
                else:
                    full_output_dir = output_dir

                full_output_dir.mkdir(parents=True, exist_ok=True)
                output_path = full_output_dir / f"{input_path.stem}.{self.format.lower()}"

                save_kwargs = {'quality': self.quality}
                if self.format == 'WEBP':
                    save_kwargs['method'] = 6

                img.save(output_path, self.format, **save_kwargs)
            print(f"已成功转换: {input_path} -> {output_path}")
        except Exception as e:
            print(f"转换 {input_path} 时出错: {e}")

    def process_directory(self, input_dir: Path, output_dir: Path) -> None:
        """
        处理目录中的所有图片，可选择递归处理子目录
        """
        self.input_dir = input_dir  # 存储输入目录以供 convert_image 使用
        output_dir.mkdir(parents=True, exist_ok=True)

        pattern = '**/*' if self.recursive else '*'
        image_files = self.get_image_files(input_dir, pattern)

        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(self.convert_image, f, output_dir) for f in image_files]
            for future in futures:
                future.result()

    @staticmethod
    def get_image_files(directory: Path, pattern: str) -> List[Path]:
        """获取指定目录下的所有图片文件"""
        return [f for f in directory.glob(pattern) if
                f.is_file() and f.suffix.lower() in ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')]

    def run(self, input_path: Path, output_path: Path) -> None:
        """运行转换过程"""
        if input_path.is_file():
            output_dir = output_path.parent
            output_dir.mkdir(parents=True, exist_ok=True)
            self.convert_image(input_path, output_dir)
        elif input_path.is_dir():
            self.process_directory(input_path, output_path)
        else:
            print("错误：输入路径无效")


def main():
    parser = argparse.ArgumentParser(description="批量图片格式转换工具 (支持WebP和递归处理)")
    parser.add_argument("input", help="输入文件或目录路径")
    parser.add_argument("format", help="目标格式 (例如 PNG, JPEG, GIF, BMP, WEBP)")
    parser.add_argument("-o", "--output", help="输出目录 (默认为当前目录下的 'converted' 文件夹)", default="converted")
    parser.add_argument("-q", "--quality", type=int, help="JPEG和WebP质量 (1-100, 默认85)", default=85)
    parser.add_argument("-r", "--recursive", action="store_true", help="递归处理子目录")
    parser.add_argument("-m", "--maintain-structure", action="store_true", help="保持原目录结构")
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve()

    converter = ImageConverter(args.format, args.quality, args.recursive, args.maintain_structure)
    converter.run(input_path, output_path)


if __name__ == "__main__":
    main()
