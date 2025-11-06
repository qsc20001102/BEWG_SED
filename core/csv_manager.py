import csv
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class CSVManager:
    """
    负责 CSV 文件的读取、数据存储、拼接和输出
    """
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.csv_data = []

    def load_csv(self, filepath):
        """自动识别编码读取 CSV 文件"""
        try:
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                self.csv_data = list(reader)
        except UnicodeDecodeError:
            with open(filepath, 'r', encoding='gbk') as f:
                reader = csv.DictReader(f)
                self.csv_data = list(reader)

        if not self.csv_data:
            logger.warning(f"CSV 文件为空或格式错误：{filepath}")
        else:
            logger.info(f"成功加载 CSV：{filepath}，共 {len(self.csv_data)} 行")
        return self.csv_data

    def generate_output(self, template_data, user_inputs):
        """
        根据模板和 CSV 数据拼接生成新的 CSV 文件
        user_inputs 包含：start_id, ip, device_name, group_name, protocol, db_num
        """
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S") #获取当前时间
        output_filename = f"{user_inputs['device']}_{timestamp}.csv"    #输出文件名
        output_path = os.path.join(self.base_dir, 'output', output_filename)    #输出文件路径
        os.makedirs(os.path.dirname(output_path), exist_ok=True)    #确保输出目录存在
        #表头
        headers = [";IO#FS0序号", "所属通道", "驱动", "所属设备", "点类型",
                   "点名", "描述", "初始值", "单位编码", "引用(云)标签",
                   "提交", "标记", "值域", "权限", "采集周期",
                   "n[0]", "n[1]", "n[2]", "n[3]", "n[4]", "n[5]", "n[6]", "n[7]", "n[8]", "n[9]", "n[10]", "n[11]", 
                   "s[0]", "s[1]", "s[2]", "s[3]", "s[4]", "s[5]", "s[6]", "s[7]", "s[8]", "s[9]", "s[10]", "s[11]", 
                   "opc.vt", "opc.item", "opc.acc", "io.kind", "io.mode", "io.obj",
                   "io.path", "模拟量>>>取绝对值", "CTPT", "系数标记", "系数倍率",
                   "基数", "基础倍率", "阈值开关", "阈值", "量程变换", 
                   "裸数据上限","裸数据下限", "量程上限", "量程下限", "数字量>>>采集取反", 
                   "真值描述", "假值描述", "防抖周期"
        ]
        #固定数据
        fixeddata2 = ["","","","0","0","0","0","1000","3"]
        fixeddata3 = ["0","0","0","0","0","0","0","","","","","","","","","","","","","0","","","0","0","","","0","0","0","0","0","1","0"]
        #依据数据类型变化数据
        DataType_1 = ["0","1","1000000000","0","1000000000","0","0","合","分","0"]
        DataType_2 = ["0.001","0","100","0","1000","0","0","","","0"]

        rows = []
        count = 0
        for device_row in self.csv_data:
            code = device_row['设备代号']
            desc = device_row['设备描述']
            #拼接地址处理
            if user_inputs['device'] == "SIEMENS":
                base_offset = int(device_row['拼接地址'])
            else:
                base_offset = device_row['拼接地址']
            #每个设备遍历模板数据
            for tpl in template_data:
                TagName = f"{code}{tpl['name']}"    #点名拼接
                Description = f"{desc}{tpl['desc']}"    #描述拼接   
                #数据类型相关数据处理      
                if tpl['type'] =="1":
                    DataType = DataType_1
                elif tpl['type'] =="2":
                    DataType = DataType_2      
                else:
                    DataType = ["","","","","","","","","",""]
                #设备类型相关数据处理，主要是采集地址拼接
                if user_inputs['device'] == "SIEMENS":
                    n1 = int(base_offset) + int(tpl['addbyte'])
                    n2 = user_inputs['db_num']
                    if tpl['type'] == "2":
                        n3 ="0"
                        n4 = tpl['addbit']
                    else:
                        n3 = "7"
                        n4 = "0"
                elif user_inputs['device'] == "AB":
                    n1 = int(base_offset) + int(tpl['addbyte'])
                    n2 = user_inputs['db_num']
                    if tpl['type'] == "2":
                        n3 ="0"
                        n4 = tpl['addbit']
                    else:
                        n3 = "7"
                        n4 = tpl['addbit']
                else:
                    n3 = ""
                    n4 = ""

                #每行数据的变量部分
                row = [
                    "",
                    user_inputs['channel'],
                    user_inputs['drive'],
                    user_inputs['dev_name'],
                    tpl['type'],
                    TagName,
                    Description,
                    n1, 
                    n2,
                    n3,
                    n4,
                    
                ]     
                #每行数据的固定数据插入
                row[7:7]=fixeddata2
                row[21:21]=fixeddata3    
                row[55:55]=DataType             
                rows.append(row)
                count += 1
        #写入输出文件
        with open(output_path, 'w', newline='', encoding='ANSI') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)

        logger.info(f"成功生成点表文件：{output_path}（共 {len(rows)} 行）")
        output = f"成功生成点表文件：{output_path}（共 {len(rows)} 行）"
        
        return output
