import re
import csv
import sys
import os
import matplotlib.pyplot as plt
import numpy as np

# 检查是否提供了命令行参数
if len(sys.argv) != 2:
    print("Usage: python x.py <input_file.mdout>")
    sys.exit(1)

# 获取文件名
input_file = sys.argv[1]

# 打开并读取 .mdout 文件
with open(input_file, 'r') as file:
    data = file.readlines()

# 正则表达式匹配 NSTEP, TEMP(K), Etot, EKtot, EPtot, VDWAALS, EELEC, VOLUME, Density
nstep_pattern = r"NSTEP =\s+(\d+)"
temp_pattern = r"TEMP\(K\)\s+=\s+([\d.]+)"
etot_pattern = r"Etot\s+=\s+([\d.-]+)"
ektot_pattern = r"EKtot\s+=\s+([\d.-]+)"
eptot_pattern = r"EPtot\s+=\s+([\d.-]+)"
vdwaals_pattern = r"VDWAALS\s+=\s+([\d.-]+)"
eelec_pattern = r"EELEC\s+=\s+([\d.-]+)"
volume_pattern = r"VOLUME\s+=\s+([\d.-]+)"
density_pattern = r"Density\s+=\s+([\d.-]+)"

# 用于存储提取的值
results = {
    "NSTEP": [],
    "TEMP(K)": [],
    "Etot": [],
    "EKtot": [],
    "EPtot": [],
    "VDWAALS": [],
    "EELEC": [],
    "VOLUME": [],
    "Density": []
}

# 逐行读取数据并提取信息
for line in data:
    # 提取 NSTEP
    nstep_match = re.search(nstep_pattern, line)
    if nstep_match:
        results["NSTEP"].append(int(nstep_match.group(1)))
    
    # 提取 TEMP(K)
    temp_match = re.search(temp_pattern, line)
    if temp_match:
        results["TEMP(K)"].append(float(temp_match.group(1)))
    
    # 提取 Etot
    etot_match = re.search(etot_pattern, line)
    if etot_match:
        results["Etot"].append(float(etot_match.group(1)))

    # 提取 EKtot
    ektot_match = re.search(ektot_pattern, line)
    if ektot_match:
        results["EKtot"].append(float(ektot_match.group(1)))
    
    # 提取 EPtot
    eptot_match = re.search(eptot_pattern, line)
    if eptot_match:
        results["EPtot"].append(float(eptot_match.group(1)))

    # 提取 VDWAALS
    vdwaals_match = re.search(vdwaals_pattern, line)
    if vdwaals_match:
        results["VDWAALS"].append(float(vdwaals_match.group(1)))
    
    # 提取 EELEC
    eelec_match = re.search(eelec_pattern, line)
    if eelec_match:
        results["EELEC"].append(float(eelec_match.group(1)))
    
    # 提取 VOLUME
    volume_match = re.search(volume_pattern, line)
    if volume_match:
        results["VOLUME"].append(float(volume_match.group(1)))
    
    # 提取 Density
    density_match = re.search(density_pattern, line)
    if density_match:
        results["Density"].append(float(density_match.group(1)))

# 设置输出文件名
output_file = 'extracted_data.csv'

# 将结果保存为 CSV 文件
with open(output_file, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    # 写入表头
    writer.writerow(results.keys())
    # 写入数据
    writer.writerows(zip(*results.values()))

print(f"数据已提取并保存为 {output_file}")

# 创建 ./analysis 目录以保存图像
output_dir = './analysis'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# 定义平滑函数
def smooth(data, window_size):
    """计算滑动窗口平均值，边界处理避免极端值"""
    if window_size < 1:
        return data

    # 使用 np.convolve 计算滑动平均
    smoothed = np.convolve(data, np.ones(window_size) / window_size, mode='same')

    # 处理边界，确保不出现极端值
    half_window = window_size // 2
    smoothed[:half_window] = data[:half_window]  # 复制前半段
    smoothed[-half_window:] = data[-half_window:]  # 复制后半段
    
    return smoothed

# 定义一个函数绘制图像并绘制平滑曲线
def plot_and_save(x_data, y_data, y_label, filename, window_size=5):
    plt.figure()

    # 原始数据的绘制
    plt.plot(x_data, y_data, marker='o', label='Original Data', color='blue')

    # 平滑处理
    y_smooth = smooth(y_data, window_size)

    # 绘制平滑后的曲线
    plt.plot(x_data, y_smooth, label='Smoothed Curve', color='red')

    # 设置图例和标签
    plt.xlabel('NSTEP')
    plt.ylabel(y_label)
    plt.title(f'{y_label} vs NSTEP')
    plt.legend()
    plt.grid(True)

    # 保存图像
    plt.savefig(os.path.join(output_dir, filename))
    plt.close()

# 绘制每个变量并保存为 PNG
plot_and_save(results["NSTEP"], results["TEMP(K)"], 'TEMP(K)', 'temp.png')
plot_and_save(results["NSTEP"], results["Etot"], 'Etot', 'etot.png')
plot_and_save(results["NSTEP"], results["EKtot"], 'EKtot', 'ektot.png')
plot_and_save(results["NSTEP"], results["EPtot"], 'EPtot', 'eptot.png')
plot_and_save(results["NSTEP"], results["VDWAALS"], 'VDWAALS', 'vdwaals.png')
plot_and_save(results["NSTEP"], results["EELEC"], 'EELEC', 'eelec.png')
plot_and_save(results["NSTEP"], results["VOLUME"], 'VOLUME', 'volume.png')
plot_and_save(results["NSTEP"], results["Density"], 'Density', 'density.png')

print(f"图像已保存到 {output_dir} 目录")
