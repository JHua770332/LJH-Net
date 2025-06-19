import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import logging
import threading
import socket
from utils import find_and_click_button, perform_adb_forward, save_log_on_fail, should_exit

class TextHandler(logging.Handler):
    def __init__(self, text):
        logging.Handler.__init__(self)
        self.text = text

    def emit(self, record):
        try:
            self.text.config(state=tk.NORMAL)
            msg = self.format(record)
            self.text.insert(tk.END, msg + '\n')
            self.text.see(tk.END)
            self.text.config(state=tk.DISABLED)
        except Exception:
            pass

class MainApp:
    def __init__(self, root, log_file):
        self.root = root
        self.root.title("TCP 测试工具")
        self.root.geometry("800x600")
        self.log_file = log_file
        self.adb_connected = False
        self.click_thread = None
        self.server_thread = None
        self.client_socket = None

        self.template_path = tk.StringVar()
        self.threshold = tk.DoubleVar(value=0.8)
        self.match_count = 0
        self.logger = logging.getLogger(__name__)

        # 配置控制区
        config_frame = ttk.LabelFrame(self.root, text="配置控制区", padding=10)
        config_frame.grid(row=0, column=0, columnspan=3, padx=10, pady=5, sticky='ew')

        # 连接设备按钮
        self.connect_button = ttk.Button(config_frame, text="连接设备", command=self.connect_device)
        self.connect_button.grid(row=0, column=0, padx=5, pady=5)

        # 模板文件选择
        ttk.Label(config_frame, text="模板图片路径:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        entry_template = ttk.Entry(config_frame, textvariable=self.template_path, width=30)
        entry_template.grid(row=1, column=1, padx=5, pady=5, sticky='ew')
        ttk.Button(config_frame, text="选择文件", command=self.select_template).grid(row=1, column=2, padx=5, pady=5)

        # 匹配阈值设置
        ttk.Label(config_frame, text="匹配阈值 (0-1):").grid(row=2, column=0, padx=5, pady=5, sticky='w')
        entry_threshold = ttk.Entry(config_frame, textvariable=self.threshold, width=10)
        entry_threshold.grid(row=2, column=1, padx=5, pady=5, sticky='w')

        # 操作按钮区
        button_frame = ttk.Frame(self.root, padding=10)
        button_frame.grid(row=1, column=0, columnspan=3, padx=10, pady=5, sticky='ew')
        self.start_button = ttk.Button(button_frame, text="开始", command=self.start_process, state=tk.DISABLED)
        self.start_button.pack(side=tk.LEFT, padx=5)
        self.stop_button = ttk.Button(button_frame, text="停止", command=self.stop_process, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)

        # 日志显示区
        log_frame = ttk.LabelFrame(self.root, text="日志显示区", padding=10)
        log_frame.grid(row=2, column=0, columnspan=3, padx=10, pady=5, sticky='nsew')
        self.log_text = tk.Text(log_frame, wrap=tk.WORD, state=tk.DISABLED)
        self.scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=self.scrollbar.set)

        self.log_text.grid(row=0, column=0, sticky='nsew', padx=(0, 5))
        self.scrollbar.grid(row=0, column=1, sticky='ns')

        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)

        # 配置日志处理器
        log_handler = TextHandler(self.log_text)
        log_handler.setLevel(logging.INFO)
        log_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(log_handler)
        self.logger.propagate = False

        self.root.grid_rowconfigure(2, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

    def connect_device(self):
        self.connect_button.config(state=tk.DISABLED)
        adb_success = perform_adb_forward(self.logger)
        if adb_success:
            self.adb_connected = True
            self.start_button.config(state=tk.NORMAL)
            messagebox.showinfo("成功", "ADB 端口转发成功，可以开始操作。")
        else:
            self.adb_connected = False
            messagebox.showerror("失败", "ADB 端口转发失败，请检查设备连接。")
        self.connect_button.config(state=tk.NORMAL)

    def select_template(self):
        file_path = filedialog.askopenfilename(filetypes=[("图片文件", "*.png;*.jpg;*.jpeg")])
        if file_path:
            self.template_path.set(file_path)

    def start_process(self):
        if not self.adb_connected:
            messagebox.showerror("错误", "请先连接设备。")
            return
        if not self.template_path.get():
            messagebox.showerror("错误", "请选择模板图片")
            return
        should_exit.clear()  # 清除退出事件
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            server_address = ('127.0.0.1', 8888)
            self.client_socket.connect(server_address)
            self.logger.info(f"成功连接到服务器 {server_address}")
            self.server_thread = threading.Thread(target=self.start_socket_client, args=(self.client_socket,))
            self.server_thread.start()
        except Exception as e:
            self.logger.error(f"连接服务器失败: {e}")
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            return

        self.click_thread = threading.Thread(target=self.click_loop)
        self.click_thread.start()

    def start_socket_client(self, client_socket):
        try:
            while not should_exit.is_set():
                client_socket.settimeout(1)  # 设置较短的超时时间，以便及时响应退出事件
                try:
                    data = client_socket.recv(1024)
                except socket.timeout:
                    continue
                except Exception as e:
                    self.logger.error(f"接收数据时发生异常: {e}")
                    self.stop_all()
                    break
                if not data:
                    # 如果没有接收到数据，说明服务器关闭连接
                    self.logger.info("服务器关闭连接。")
                    self.stop_all()
                    break
                message = data.decode('utf-8')
                self.logger.info(f"Received from server: {message}")
                if "FAIL" in message:
                    self.logger.warning("检测到关键字 FAIL，开始保存日志。")
                    save_log_on_fail(self.logger, self.log_file)
                    self.stop_all()
                    break
        except Exception as e:
            self.logger.error(f"发生错误: {e}")
            self.stop_all()
        finally:
            # 关闭套接字
            if client_socket:
                self.logger.info("关闭客户端套接字。")
                client_socket.close()

    def stop_process(self):
        should_exit.set()  # 设置退出事件
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.DISABLED)
        if self.client_socket:
            try:
                self.client_socket.shutdown(socket.SHUT_RDWR)
                self.client_socket.close()
                self.logger.info("已断开与服务器的连接")
            except Exception as e:
                self.logger.error(f"断开连接时出错: {e}")
        self.root.after(100, self.wait_for_threads)

    def wait_for_threads(self):
        if self.click_thread and self.click_thread.is_alive():
            self.root.after(100, self.wait_for_threads)
            return
        if self.server_thread and self.server_thread.is_alive():
            self.root.after(100, self.wait_for_threads)
            return
        # 所有线程已停止，重置状态
        self.start_button.config(state=tk.NORMAL)
        self.adb_connected = False
        self.match_count = 0
        self.template_path.set('')

    def click_loop(self):
        while not should_exit.is_set():
            if find_and_click_button(self.logger, self.template_path.get(), self.threshold.get()):
                self.match_count += 1
            time.sleep(1)  # 缩短休眠时间，以便更快响应退出事件

    def stop_all(self):
        should_exit.set()  # 设置退出事件
        self.root.after(100, self.wait_for_threads)
        save_log_on_fail(self.logger, self.log_file)
        messagebox.showwarning("警告", "服务器连接异常，已停止相关任务。")
        self.adb_connected = False
        self.match_count = 0
        self.template_path.set('')
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    log_file = "app.log"
    app = MainApp(root, log_file)
    root.mainloop()
