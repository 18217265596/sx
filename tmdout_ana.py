import re
import csv
import sys
import os
import matplotlib.pyplot as plt

def main():
    # 检查命令行参数，至少要有一个输入文件
    if len(sys.argv) < 2:
        print("用法: python rmsd.py <输入文件1> [<输入文件2> ...]")
        sys.exit(1)

    input_files = sys.argv[1:]

    # 初始化列表来存储所有文件的TIME(PS)和RMSD的值
    time_list = []
    rmsd_list = []

    # 初始化时间偏移量
    time_offset = 0.0

    for input_file in input_files:
        # 检查文件是否存在
        if not os.path.isfile(input_file):
            print(f"文件 {input_file} 不存在，跳过该文件。")
            continue

        # 读取当前文件的内容
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        current_time = None

        # 临时列表存储当前文件的时间和RMSD值
        temp_time_list = []
        temp_rmsd_list = []

        # 遍历每一行，提取所需的数据
        for line in lines:
            # 提取 TIME(PS) 的值
            time_match = re.search(r'TIME\(PS\)\s*=\s*([\d\.]+)', line)
            if time_match:
                current_time = float(time_match.group(1))
            # 提取 Current RMSD from reference 的值
            rmsd_match = re.search(r'Current RMSD from reference:\s*([\d\.]+)', line)
            if rmsd_match and current_time is not None:
                current_rmsd = float(rmsd_match.group(1))
                # 将值添加到临时列表中
                temp_time_list.append(current_time)
                temp_rmsd_list.append(current_rmsd)
                # 重置 current_time 以准备下一个数据块
                current_time = None

        # 如果当前文件有数据，则进行时间累加处理
        if temp_time_list:
            # 调整当前文件的时间值，使其累加
            adjusted_time_list = [time + time_offset for time in temp_time_list]
            # 更新总的时间偏移量
            time_offset = adjusted_time_list[-1]
            # 将调整后的时间和RMSD值添加到总列表中
            time_list.extend(adjusted_time_list)
            rmsd_list.extend(temp_rmsd_list)
        else:
            print(f"文件 {input_file} 中未找到有效的数据。")

    # 检查是否有数据
    if not time_list or not rmsd_list:
        print("未提取到任何数据。")
        sys.exit(1)

    # 将数据写入 CSV 文件（没有头文件）
    with open('output.csv', 'w', newline='', encoding='utf-8') as csvfile:
        csvwriter = csv.writer(csvfile)
        for time, rmsd in zip(time_list, rmsd_list):
            csvwriter.writerow([time, rmsd])

    # 确保 ./rmsd 目录存在
    if not os.path.exists('./rmsd'):
        os.makedirs('./rmsd')

    # 绘制并保存图像（不显示）
    plt.plot(time_list, rmsd_list)
    plt.xlabel('Time (PS)')
    plt.ylabel('Current RMSD from reference')
    plt.title('RMSD vs Time')
    plt.savefig('./rmsd/plot.png')
    # 不调用 plt.show()

if __name__ == '__main__':
    main()
