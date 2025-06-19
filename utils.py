import subprocess
import time
import cv2
import pyautogui
import numpy as np
import datetime
import socket
import os
import threading

# 全局变量，用于控制是否退出程序
should_exit = threading.Event()

def find_and_click_button(logger, template_path, threshold=0.8):
    """
    此函数用于在屏幕上查找指定模板图片，并在找到后模拟点击。
    :param logger: 日志记录器实例
    :param template_path: 模板图片的文件路径
    :param threshold: 匹配阈值，范围在 0 到 1 之间，值越大匹配越严格
    """
    try:
        # 截取当前屏幕
        screenshot = pyautogui.screenshot()
        screenshot = np.array(screenshot)
        # 将颜色空间从 RGB 转换为 BGR
        screenshot = cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR)
        # 读取模板图片
        template = cv2.imread(template_path)
        if template is None:
            logger.error(f"无法读取模板图片: {template_path}")
            return False
        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        if max_val >= threshold:
            h, w, _ = template.shape
            center_x = max_loc[0] + w // 2
            center_y = max_loc[1] + h // 2
            pyautogui.click(center_x, center_y)
            logger.info("成功模拟点击按钮。")
            return True
        else:
            logger.info("未找到匹配的按钮。")
            return False
    except Exception as e:
        logger.error(f"发生错误: {e}")
        return False

def check_adb_devices(logger):
    """检查是否有 ADB 设备连接"""
    try:
        result = subprocess.run(['adb', 'devices'], capture_output=True, text=True, check=True)
        output_lines = result.stdout.split('\n')
        # 跳过标题行和空行，检查是否有设备信息
        for line in output_lines[1:]:
            if line.strip() and not line.startswith('*'):
                parts = line.split()
                if len(parts) >= 2 and parts[1] == 'device':
                    return True
        logger.error("adb.exe: no devices/emulators found")
        return False
    except subprocess.CalledProcessError as e:
        logger.error(f"检查 ADB 设备时出错: {e}")
        return False

def perform_adb_forward(logger):
    if not check_adb_devices(logger):
        return False
    try:
        # 执行 ADB 端口转发命令
        subprocess.run(['adb', 'forward', 'tcp:8888', 'tcp:8888'], check=True)
        logger.info("ADB 端口转发成功")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"ADB 端口转发失败: {e}")
        return False

def save_log_on_fail(logger, log_file):
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    log_backup_file = f'fail_log_{timestamp}.log'
    try:
        if os.path.getsize(log_file) == 0:
            logger.warning("原始日志文件为空，无需备份。")
            return
        # 先尝试以 utf-8 编码读取文件
        with open(log_file, 'r', encoding='utf-8') as f_in, open(log_backup_file, 'w', encoding='utf-8') as f_out:
            content = f_in.read()
            if content:
                f_out.write(content)
                logger.warning(f"日志已保存到 {log_backup_file}")
            else:
                logger.warning("读取到的日志内容为空，未进行备份。")
    except UnicodeDecodeError:
        try:
            with open(log_file, 'r', encoding='gbk') as f_in, open(log_backup_file, 'w', encoding='utf-8') as f_out:
                content = f_in.read()
                if content:
                    f_out.write(content)
                    logger.warning(f"日志已使用 gbk 编码保存到 {log_backup_file}")
                else:
                    logger.warning("读取到的日志内容为空，未进行备份。")
        except Exception as e:
            logger.error(f"使用 gbk 编码保存日志时出错: {e}")
    except Exception as e:
        logger.error(f"保存日志时出错: {e}")

def start_socket_server(logger, log_file, stop_callback):
    # 服务器地址和端口
    server_address = ('127.0.0.1', 8888)

    # 创建 TCP 套接字
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # 连接到服务器
        client_socket.connect(server_address)
        logger.info(f"成功连接到服务器 {server_address}")

        while not should_exit.is_set():
            # 接收服务器响应
            client_socket.settimeout(1)  # 设置较短的超时时间，以便及时响应退出事件
            try:
                data = client_socket.recv(1024)
            except socket.timeout:
                continue
            except Exception as e:
                logger.error(f"接收数据时发生异常: {e}")
                stop_callback()
                break
            if not data:
                # 如果没有接收到数据，说明服务器关闭连接
                logger.info("服务器关闭连接。")
                stop_callback()
                break
            message = data.decode('utf-8')
            logger.info(f"Received from server: {message}")
            if "FAIL" in message:
                logger.warning("检测到关键字 FAIL，开始保存日志。")
                save_log_on_fail(logger, log_file)
                stop_callback()
                break
    except ConnectionRefusedError:
        logger.error("连接被拒绝，请检查服务器是否启动。")
        stop_callback()
    except Exception as e:
        logger.error(f"发生错误: {e}")
        stop_callback()
    finally:
        # 关闭套接字
        logger.info("关闭客户端套接字。")
        client_socket.close()
