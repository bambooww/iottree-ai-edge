这是一个为IOT-Tree项目中的AI节点【IOTTree Edge】提供边缘本地化的AI支持。
==

项目使用python实现，通过http方式对外提供识别参数设置，结果输出等。
项目基于yolo，mediapipe开源库实现。

# 1 主要支持：

## 1.1 手势识别

## 1.2

# 2 安装配置运行

## 2.1 下载项目

下载项目到本地目录，建议目录不要有空格和非ascii支付

## 2.2 python运行环境准备

建议使用miniconda建立python独立运行的环境。使用下述命令，确保环境安装和激活成功。

`
conda env create -f environment.yaml

conda activate iottree-edge
`

## 2.3 运行iottree-edge

`
python server.py
`

# 3 查看是否运行正常

使用浏览器访问 http://localhost:9091/gesture/

