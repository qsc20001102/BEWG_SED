import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from core.template_manager import TemplateManager
from core.csv_manager import CSVManager
import logging

logger = logging.getLogger(__name__)

class MainUI:
    def __init__(self, root, base_dir):
        self.root = root
        self.root.title("BEWG SED 点表生成")   # 窗口标题
        self.root.geometry("1000x400")  # 窗口大小
        root.resizable(False, False)    # 禁止水平和垂直调整大小
        
        self.base_dir = base_dir
        self.template_manager = TemplateManager(base_dir)
        self.csv_manager = CSVManager(base_dir)
        # 初始化导入数据模板数据
        self.template_data = []
        self.csv_data = []

        self.build_ui()
        logging.info(f"工具运行根目录{base_dir}")

    def build_ui(self):
        # 第一行容器：模板区 + CSV区
        top_row = ttk.Frame(self.root)
        top_row.pack(side='top', fill='x', padx=5, pady=5)

        self.create_template_section(parent=top_row)
        self.create_csv_section(parent=top_row)

        # 第二行：参数区
        self.create_input_section()

        # 第三行：生成区
        self.create_generate_section()    

    # ---------------- 模板区 ----------------
    def create_template_section(self, parent):
        frame = ttk.LabelFrame(parent, text="配置文件选择", padding=5)
        frame.pack(side='left', padx=5, pady=5, anchor='nw')

        self.device_cb = self._add_combobox(frame, "设备类型：", row=0, col=0, listbox=self.template_manager.get_device_types(), inivar=-1)
        # 选择完成事件
        self.device_cb["combobox"].bind('<<ComboboxSelected>>', self.on_device_selected)
        
        self.template_cb = self._add_combobox(frame, "模板文件：", row=0, col=1, listbox=[], inivar=-1)
        #选择完成事件
        self.template_cb['combobox'].bind('<<ComboboxSelected>>', self.on_template_selected)
        # 模板显示表格
        self.template_table = ttk.Treeview(frame, columns=("name","desc","type","addbyte","addbit"), show="headings", height=5)
        col_defs = {
            "name": ("名称", 100),
            "desc": ("描述", 130),
            "type": ("类型", 100),
            "addbyte": ("偏移字节", 80),
            "addbit": ("偏移位", 80),
        }      
        for col, (text, width) in col_defs.items():
            self.template_table.heading(col, text=text)
            self.template_table.column(col, width=width, anchor="center")
        self.template_table.grid(row=1, column=0, columnspan=4, sticky='nsew', pady=(9,5))

    def on_device_selected(self, event=None):
        """设备类型选择完成事件"""
        # 获取目录下的所有模板文件
        device = self.device_cb['var'].get()
        self.template_cb['combobox']['values'] = self.template_manager.get_templates_by_device(device)


    def on_template_selected(self, event=None):
        """模板文件选择完成事件"""
        device = self.device_cb['var'].get()
        template = self.template_cb['var'].get()
        self.template_data = self.template_manager.load_template(device, template)
        self.refresh_template_table()

    def refresh_template_table(self):
        """刷新模板显示表格"""
        for row in self.template_table.get_children():
            self.template_table.delete(row)
        try:
            for item in self.template_data:
                self.template_table.insert('', 'end', values=(item['name'], item['desc'], item['type'], item['addbyte'], item['addbit']))
        except Exception as e:
            for row in self.template_table.get_children():
                self.template_table.delete(row)
            logger.error(f"加载模板异常{e}")
            messagebox.showwarning("加载出错", f"加载模板异常{e}", icon="error")

    # ---------------- CSV区 ----------------
    def create_csv_section(self, parent):
        frame = ttk.LabelFrame(parent, text="CSV 数据导入", padding=5)
        frame.pack(side='left', padx=5, pady=5, anchor='nw')

        btn = ttk.Button(frame, text="选择CSV文件", command=self.load_csv_file)
        btn.grid(row=0, column=0, sticky='w')

        self.csv_table = ttk.Treeview(frame, columns=("code","desc","offset"), show="headings", height=5)
        col_defs = {
            "code": ("设备代号", 150),
            "desc": ("设备名称", 180),
            "offset": ("拼接地址", 120),
        } 
        for col, (text, width) in col_defs.items():
            self.csv_table.heading(col, text=text)
            self.csv_table.column(col, width=width, anchor="center")
        self.csv_table.grid(row=1, column=0, columnspan=4, sticky='nsew', pady=5)

    def load_csv_file(self):
        filepath = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if not filepath:
            return
        self.csv_data = self.csv_manager.load_csv(filepath)
        self.refresh_csv_table()

    def refresh_csv_table(self):
        """刷新CSV显示表格"""
        for row in self.csv_table.get_children():
            self.csv_table.delete(row)
        try:
            for row in self.csv_data:
                self.csv_table.insert('', 'end', values=(row['设备代号'], row['设备描述'], row['拼接地址']))
        except Exception as e:
            for row in self.csv_table.get_children():
                self.csv_table.delete(row)
            logger.error(f"导入数据异常{e}")
            messagebox.showwarning("导入出错", f"导入数据异常{e}\n检查第一行列名是否正确", icon="error")

    # ---------------- 参数区 ----------------
    def create_input_section(self):
        frame = ttk.LabelFrame(self.root, text="参数输入", padding=10)
        frame.pack(side='top', fill='x', padx=10, pady=5)

        self.channel = self._add_input(frame, "所属通道", row=0, col=0, inivar="S127", entry_width=10) 
        self.dev_name = self._add_input(frame, "所属设备", row=0, col=1, inivar="PLC1", entry_width=10)
        self.drive_siemens = ["PLC_SIEMENS_S7_1200_TCP"]
        self.drive_ab = ["AB-ControlLogixTCP"]
        self.drive = self._add_combobox(frame, "驱动", row=0, col=2, listbox=self.drive_siemens, width=25)
        #self.drive["combobox"].bind('<<ComboboxSelected>>', self.on_link_selected)  # 选择完成事件   
        self.db_num = self._add_input(frame, "DB块号", row=0, col=3, inivar="3", entry_width=5)
        

    def _add_input(
            self, parent, label_text, 
            row, col=0, inivar="", 
            label_width=8, entry_width=20, colspan=1, sticky='w'
        ):
        """
        添加一个带文本标签和输入框的组合控件，并返回 (StringVar, Frame) 以便后续控制。
        - parent: 父容器
        - label: 标签文字
        - row, col: 放置在父容器的 grid 行列
        - inivar: 初始值
        - entry_width: 输入框宽度
        - colspan: 该组控件在父容器上跨越的列数
        - sticky: 对齐方式（默认左对齐）
        """
        group_frame = ttk.Frame(parent)
        group_frame.grid(row=row, column=col, columnspan=colspan, sticky=sticky, padx=5, pady=3)

        # 标签
        label = ttk.Label(group_frame, text=label_text + "：", width=label_width, anchor='w').grid(row=0, column=0, sticky='w', padx=(0, 5))

        # 输入框
        var = tk.StringVar(value=inivar)
        entry = ttk.Entry(group_frame, textvariable=var, width=entry_width)
        entry.grid(row=0, column=1, sticky='w')

        return {
            "frame": group_frame,
            "label": label,
            "entry": entry,
            "var": var
        }

    def _add_combobox(
        self, parent, label_text, row, col=0,
        listbox=[], inivar=0, width=17, colspan=1,
        sticky='w', label_width=8, state="readonly"
    ):
        """
        创建一组 [标签 + 下拉框] 控件。
        返回 dict，方便外部单独或统一控制。

        - values: 下拉选项列表
        - default: 初始值（可选）
        - state: "readonly" 表示只能从列表选，"normal" 可手动输入
        """
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=col, columnspan=colspan, sticky=sticky, padx=5, pady=3)

        # 标签
        label = ttk.Label(
            frame,
            text=label_text + "：",
            width=label_width,
            anchor='w'
        )
        label.grid(row=0, column=0, sticky='w', padx=(0, 5))

        # 变量 + 下拉框
        var = tk.StringVar()
        combobox = ttk.Combobox(
            frame,
            textvariable=var,
            values=listbox,
            width=width,
            state=state
        )
        combobox.grid(row=0, column=1, sticky='w')
        if inivar>=0:
            var.set(listbox[inivar])

        return {
            "frame": frame,
            "label": label,
            "combobox": combobox,
            "var": var
        }


    # ---------------- 生成区 ----------------
    def create_generate_section(self):
        frame = ttk.Frame(self.root)
        frame.pack(fill='x', padx=10, pady=5)

        btn = ttk.Button(frame, text="生成点表文件", command=self.generate_csv)
        btn.pack(anchor='center')

    def generate_csv(self):
        if not self.template_data or not self.csv_data:
            messagebox.showwarning("警告", "请先加载模板和CSV数据！")
            return

        inputs = {
            "channel": self.channel["var"].get(), #所属通道
            "dev_name": self.dev_name["var"].get(), #所属设备
            "drive": self.drive["var"].get(),   #驱动
            "db_num": self.db_num["var"].get(),  #DB块号
            
            "device": self.device_cb["var"].get(),  #设备类型
        }

        output_path = self.csv_manager.generate_output(self.template_data, inputs)
        messagebox.showwarning("生成成功", output_path, icon="info")
        