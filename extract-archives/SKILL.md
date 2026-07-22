---
name: extract-archives
category: productivity
description: Extract various archive formats (zip, tar, 7z, rar, gz, xz, bz2) with common options.
tags: [archive, extract, unzip, tar, compression]
---

# Extract Archives

## ZIP
```bash
unzip file.zip                        # 基本解压
unzip file.zip -d /target/dir         # 指定目录
unzip -l file.zip                     # 查看内容
unzip -o file.zip                     # 覆盖已存在
unzip -P password file.zip            # 密码
```

## TAR
```bash
tar -xf file.tar                      # .tar
tar -xzf file.tar.gz                  # .tar.gz / .tgz
tar -xjf file.tar.bz2                 # .tar.bz2
tar -xJf file.tar.xz                  # .tar.xz
tar -xf file.tar -C /target/dir       # 指定目录
tar -tf file.tar                      # 查看内容
tar -xpf file.tar                     # 保留权限
```

## 7Z (需 p7zip-full)
```bash
7z x file.7z                          # 解压
7z x file.7z -o/target/dir            # 指定目录
7z x -ppassword file.7z               # 密码
7z l file.7z                          # 查看内容
```

## RAR (需 unrar)
```bash
unrar x file.rar                      # 解压
unrar x file.rar /target/dir          # 指定目录
unrar x -ppassword file.rar           # 密码
unrar l file.rar                      # 查看内容
```

## GZ / XZ / BZ2
```bash
gunzip -k file.gz                     # GZ（保留原文件）
gunzip file.gz                        # GZ（删除原文件）
xz -d file.xz                         # XZ
xz -dk file.xz                        # XZ（保留原文件）
bunzip2 file.bz2                      # BZ2
bunzip2 -k file.bz2                   # BZ2（保留原文件）
```

## 批量
```bash
for f in *.zip; do unzip "$f" -d "${f%.zip}"; done
for f in *.tar.gz; do tar -xzf "$f"; done
```

## 中文乱码
```bash
sudo apt install unar
unar file.zip                         # 自动处理编码
unzip -O cp936 file.zip               # 指定编码
```

## 分卷
```bash
unrar x part1.rar                     # RAR 分卷
7z x file.7z.001                      # 7Z 分卷
```

## 安装
```bash
sudo apt install unzip p7zip-full unrar unar    # Ubuntu
sudo yum install unzip p7zip unrar              # CentOS
brew install p7zip unrar                        # macOS
```

## 验证
```bash
unzip file.zip && echo "Success"
unzip -t file.zip
tar -tzf file.tar.gz > /dev/null && echo "OK"
```
