#!/usr/bin/env python
import os
from PIL import Image
import argparse
from concurrent.futures import ThreadPoolExecutor


def convert_image(input_path, output_dir, format, quality=85):
    """
    将单个图片从一种格式转换为另一种格式，包括WebP

    :param input_path: 输入图片的路径
    :param output_dir: 输出目录
    :param format: 目标格式 (例如 'PNG', 'JPEG', 'GIF', 'BMP', 'WEBP')
    :param quality: 输出图片质量 (对JPEG和WebP有效)
    """
    try:
        with Image.open(input_path) as img:
            # 处理 RGBA 模式
            if img.mode == 'RGBA' and format.upper() in ['JPEG', 'WEBP']:
                img = img.convert('RGB')

            # 生成输出文件路径
            file_name = os.path.splitext(os.path.basename(input_path))[0]
            output_path = os.path.join(output_dir, f"{file_name}.{format.lower()}")

            # 保存为新格式
            if format.upper() == 'WEBP':
                img.save(output_path, format, quality=quality, method=6)
            else:
                img.save(output_path, format, quality=quality)
        print(f"已成功转换: {input_path} -> {output_path}")
    except Exception as e:
        print(f"转换 {input_path} 时出错: {e}")


def batch_convert(input_dir, output_dir, format, quality=85):
    """
    批量转换指定目录下的所有图片

    :param input_dir: 输入目录
    :param output_dir: 输出目录
    :param format: 目标格式
    :param quality: 输出图片质量 (对JPEG和WebP有效)
    """
    os.makedirs(output_dir, exist_ok=True)

    # 获取所有图片文件，包括WebP
    image_files = [f for f in os.listdir(input_dir) if
                   f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'))]

    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(convert_image, os.path.join(input_dir, f), output_dir, format, quality) for f in
                   image_files]
        for future in futures:
            future.result()


def main():
    parser = argparse.ArgumentParser(description="批量图片格式转换工具 (支持WebP)")
    parser.add_argument("input", help="输入文件或目录路径")
    parser.add_argument("format", help="目标格式 (例如 PNG, JPEG, GIF, BMP, WEBP)")
    parser.add_argument("-o", "--output", help="输出目录 (默认为当前目录下的 'converted' 文件夹)", default="converted")
    parser.add_argument("-q", "--quality", type=int, help="JPEG和WebP质量 (1-100, 默认85)", default=85)
    args = parser.parse_args()

    format = args.format.upper()

    if os.path.isfile(args.input):
        output_dir = os.path.dirname(args.output)
        os.makedirs(output_dir, exist_ok=True)
        convert_image(args.input, output_dir, format, args.quality)
    elif os.path.isdir(args.input):
        batch_convert(args.input, args.output, format, args.quality)
    else:
        print("错误：输入路径无效")


if __name__ == "__main__":
    main()
