import os
import pandas as pd
from openpyxl import load_workbook

def merge_excelfiles(dir_path, save_path):
    # 读取目录下所有Excel文件
    file_list = [os.path.join(dir_path, f) for f in os.listdir(dir_path) if f.endswith(".xlsx")]
    # 读取第一个Excel文件或Sheet，作为合并后的表头
    wb = load_workbook(file_list[0], read_only=True)
    ws = wb.active
    headers = [cell.value for cell in next(ws.rows)]
    # 逐一读取Excel文件中的数据，并存入DataFrame中
    df_list = []
    for file in file_list:
        wb = load_workbook(file, data_only=True)
        for sheet_name in wb.sheetnames:
            data = wb[sheet_name].values
            df = pd.DataFrame(data, columns=headers)
            df_list.append(df)
    # 将DataFrame列表合并，并保存为新的Excel文件
    merge_data = pd.concat(df_list, axis=0)
    merge_data.to_excel(save_path, index=False)

dir_path = "C:/Users/86150/Desktop/后端开发"  # 设置Excel所在目录
save_path = "merged_后端开发.xlsx"  # 设置合并后保存的新文件路径
merge_excelfiles(dir_path, save_path)  # 合并Excel文件