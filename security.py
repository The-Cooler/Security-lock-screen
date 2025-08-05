from pynput import keyboard, mouse
import cv2
import os
import platform
import time
import threading
from pynput.keyboard import Key

os.system("chcp 65001")
cv2.setLogLevel(2)
lock = ""
desktop = ""

# 监控模式开关
monitoring = False
cooldown = False
should_exit = False  # 添加退出标志

system = platform.system()
if system == "Windows":
    desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')
    lock = "rundll32.exe user32.dll,LockWorkStation"
elif system == "Linux":
    desktop = os.path.join(os.environ['HOME'], 'Desktop')
    lock = "gnome-screensaver-command -l"
elif system == "Darwin":
    desktop = os.path.join(os.environ['HOME'], 'Desktop')
    lock = "osascript -e 'tell application \"System Events\" to keystroke \"q\" using {control down, command down}'"
else:
    print("未知系统!!!")


# 拍照
def create_photo():
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    if ret:
        filename = os.path.join(desktop, time.strftime("%Y%m%d_%H%M%S.jpg"))
        cv2.imwrite(filename, frame)
        print(f"拍照保存: {filename}")
    cap.release()

# 锁屏
def lock_screen():
    os.system(lock)    
  

# 冷却重置
def reset_cooldown():
    global cooldown
    time.sleep(10)
    cooldown = False

# 鼠标键盘事件处理函数
def on_input_event(event):
    global cooldown, monitoring
    if monitoring and not cooldown:
        cooldown = True
        print("[!] 监控模式激活，检测到活动，拍照并锁屏")
        create_photo()
        time.sleep(0.5)
        lock_screen()
        threading.Thread(target=reset_cooldown, daemon=True).start()


def normalize_key(k):
    if isinstance(k, Key):
        return k
    if hasattr(k, 'vk') and k.vk is not None:
        return k.vk
    if isinstance(k, int):
        return k
    if hasattr(k, 'char') and k.char is not None:
        return ord(k.char)
    return k


# 监听热键激活监控
# 定义所有可能的触发组合
trigger_combinations = [
    {keyboard.Key.ctrl_l, keyboard.Key.alt_l, 81},  
    {keyboard.Key.ctrl_l, keyboard.Key.alt_l, 81},  
    {keyboard.Key.ctrl_r, keyboard.Key.alt_l, 81},  
    {keyboard.Key.ctrl_r, keyboard.Key.alt_l, 81},  
    {keyboard.Key.ctrl_l, keyboard.Key.alt_r, 81},  
    {keyboard.Key.ctrl_l, keyboard.Key.alt_r, 81},  
    {keyboard.Key.ctrl_r, keyboard.Key.alt_r, 81},  
    {keyboard.Key.ctrl_r, keyboard.Key.alt_r, 81},  
]
trigger_combinations = [set(normalize_key(k) for k in combo) for combo in trigger_combinations]
pressed_keys = set()

def on_key_press(key):
    global monitoring, pressed_keys, should_exit
    
    # 检查Esc键退出
    if key == keyboard.Key.esc:
        print("[!] 检测到ESC键，程序即将退出...")
        should_exit = True
        # 停止所有监听器
        return False
        
    if key in pressed_keys:
        return
    pressed_keys.add(key)
    
    # 打印当前按下的键
    # print(f"当前按下的键: {pressed_keys}")

    tmp_key = set(normalize_key(k) for k in pressed_keys)
    
    # 检查是否有任一组合键被触发
    triggered = any(combination.issubset(tmp_key) for combination in trigger_combinations)
    # print(triggered)
    
    if triggered:
        if not monitoring:
            monitoring = True
            print("[*] 监控模式已启动，开始监听鼠标和键盘动作")
        else:
            monitoring = False
            print("[*] 监控模式已关闭，停止监听动作")

def on_key_release(key):
    if key in pressed_keys:
        pressed_keys.remove(key)

# 启动监听器
print("程序启动，按 Ctrl+Alt+Q 切换监控模式，按 ESC 键退出程序")
with keyboard.Listener(on_press=on_key_press, on_release=on_key_release) as kl, \
    mouse.Listener(on_move=on_input_event, on_click=on_input_event, on_scroll=on_input_event) as ml:
    try:
        while not should_exit:
            time.sleep(0.1)  # 减少CPU使用率
    except KeyboardInterrupt:
        print("[!] 接收到中断信号，程序退出")
    finally:
        # 确保监听器停止
        kl.stop()
        ml.stop()

