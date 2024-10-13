import re
import csv
import sys

# 检查是否提供了命令行参数
if len(sys.argv) != 2:
    print("Usage: python x.py <input_file.mdout>")
    sys.exit(1)

# 获取文件名
input_file = sys.argv[1]

# 打开并读取 .mdout 文件
with open(input_file, 'r') as file:
    data = file.readlines()

# 正则表达式匹配 NSTEP, VDWAALS, EELEC
nstep_pattern = r"NSTEP =\s+(\d+)"
vdwaals_pattern = r"VDWAALS\s+=\s+([\d.-]+)"
eelec_pattern = r"EELEC\s+=\s+([\d.-]+)"

# 用于存储提取的值
results = []
current_nstep = None
current_vdwaals = None
current_eelec = None

# 逐行读取数据并提取信息
for line in data:
    # 提取 NSTEP
    nstep_match = re.search(nstep_pattern, line)
    if nstep_match:
        current_nstep = int(nstep_match.group(1))
    
    # 提取 VDWAALS
    vdwaals_match = re.search(vdwaals_pattern, line)
    if vdwaals_match:
        current_vdwaals = float(vdwaals_match.group(1))
    
    # 提取 EELEC
    eelec_match = re.search(eelec_pattern, line)
    if eelec_match:
        current_eelec = float(eelec_match.group(1))
    
    # 当我们找到了 NSTEP, VDWAALS 和 EELEC 都有时，将其保存
    if current_nstep is not None and current_vdwaals is not None and current_eelec is not None:
        results.append((current_nstep, current_vdwaals, current_eelec))
        current_nstep = None  # 清空，等待下一组数据
        current_vdwaals = None
        current_eelec = None

# 设置输出文件名
output_file = 'extracted_data.csv'

# 将结果保存为 CSV 文件
with open(output_file, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['NSTEP', 'VDWAALS', 'EELEC'])  # 写入表头
    writer.writerows(results)  # 写入数据

print(f"数据已提取并保存为 {output_file}")
