import logging
import tkinter as tk
from Tcp_gui import MainApp

# 配置日志记录
log_file = 'app.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

if __name__ == "__main__":
    root = tk.Tk()
    app = MainApp(root, log_file)
    root.mainloop()
