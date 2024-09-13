# ImageConvert

批量图片格式转换工具

## 版本介绍

- 批量处理：现在可以处理整个目录中的所有图片。
- 命令行参数：使用 argparse 添加了命令行参数支持，使程序更灵活。
- 并行处理：使用 ThreadPoolExecutor 进行并行处理，提高了批量转换的效率。
- 质量控制：为 JPEG/WebP 格式添加了质量参数。
- 灵活的输入/输出：可以处理单个文件或整个目录，并允许指定输出目录。
- WebP 压缩方法：使用 method=6 参数来获得更好的 WebP 压缩效果（这是最慢但效果最好的压缩方法）。
- 输入格式扩展：在批处理中包含了 .webp 文件，以便处理现有的 WebP 图片。
- 支持的图片格式： JPG，PNG, JPEG, GIF, BMP, WEBP

## 前提条件

操作系统：支持所有主要的操作系统（Windows、macOS、Linux）。

Python 依赖：
- 安装 Python 3.x（推荐 3.10 或更高版本）。
- 安装 Pillow 库（图像处理库）。

## 使用说明：

首先，确保已安装Pillow库。如果没有，可以使用以下命令安装：

```bash
pip install --upgrade pillow
```

1. 单文件转换：
```
python image_convert.py input_image.png JPEG -o output_directory -q 90
```

2. 目录批量转换：
```
python image_convert.py input_directory PNG -o output_directory
```

3. 使用默认设置：
```
python image_convert.py input_directory JPEG
```

4. 转换为 WebP：
```
python image_convert.py input_image.png WEBP -o output_directory -q 80
```

5. 从 WebP 转换：
```
python image_convert.py input_image.webp JPEG -o output_directory -q 90
```
