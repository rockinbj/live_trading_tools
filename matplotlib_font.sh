#!/bin/bash


# 安装需要的包
dnf install fontconfig mkfontscale -y


# 创建用于中文字体的目录并进入该目录
mkdir -p /usr/share/fonts/zh_CN
cd /usr/share/fonts/zh_CN


# 下载并安装黑体字体
wget https://github.com/StellarCN/scp_zh/raw/master/fonts/SimHei.ttf
mkfontscale
mkfontdir
fc-cache -fv
fc-list :lang=zh # 查看已安装的中文字体


# 设置 matplotlib 缓存
echo "import matplotlib" >> mpl_font.py
echo "matplotlib.get_cachedir()" >> mpl_font.py
# 运行脚本
python3 mpl_font.py


# 删除 matplotlib 缓存
rm -rf ~/.cache/matplotlib

