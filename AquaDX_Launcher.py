import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import os
import json
import sys
import subprocess
from icon import img
import base64

# --- 常量 ---
ACCOUNTS_FILE_NAME = 'accounts.json'
CONFIG_FILE_NAME = 'config.json'
DEFAULT_AUTH_FILENAME = "..\\AMDaemon\\DEVICE\\aime.txt"
DEFAULT_LAUNCH_BAT_FILENAME = "..\\启动.bat"
PLACEHOLDER_AUTH_PATH = "请设置卡号文件 (aime.txt) 的路径"
PLACEHOLDER_LAUNCH_BAT_PATH = "请设置游戏启动脚本 (启动.bat) 的路径"
DATA_DIR_NAME = 'LauncherConfig'

# --- 确定基础路径 ---
if getattr(sys, 'frozen', False):
    base_path = os.path.dirname(sys.executable)
elif __file__:
    base_path = os.path.dirname(os.path.abspath(__file__))
else:
    base_path = os.getcwd()

# --- 数据文件路径 ---
data_path = os.path.join(base_path, DATA_DIR_NAME)
ACCOUNTS_FILE = os.path.join(data_path, ACCOUNTS_FILE_NAME)
CONFIG_FILE = os.path.join(data_path, CONFIG_FILE_NAME)

# --- 辅助函数：确保目录存在 ---
def ensure_dir_exists(path):
    if not os.path.exists(path):
        try:
            os.makedirs(path, exist_ok=True)
            print(f"创建目录: {path}")
        except OSError as e:
            messagebox.showerror("目录错误", f"无法创建数据目录 '{path}': {e}")
            return False
    return True

# --- 账号数据管理 ---
def load_accounts():
    if not ensure_dir_exists(data_path): return {}
    try:
        if os.path.exists(ACCOUNTS_FILE):
            with open(ACCOUNTS_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
                return json.loads(content) if content.strip() else {}
        else:
            save_accounts({})
            return {}
    except (json.JSONDecodeError, IOError) as e:
        messagebox.showerror("加载错误", f"加载账号文件 '{ACCOUNTS_FILE}' 时出错: {e}\n将使用空列表。")
        return {}

def save_accounts(accounts_data):
    if not ensure_dir_exists(data_path): return
    try:
        with open(ACCOUNTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(accounts_data, f, indent=4, ensure_ascii=False)
    except IOError as e:
        messagebox.showerror("保存错误", f"保存账号到 '{ACCOUNTS_FILE}' 时出错: {e}")

# --- 配置管理 ---
def load_config():
    if not ensure_dir_exists(data_path):
        return {
            "auth_file_path": PLACEHOLDER_AUTH_PATH,
            "launch_bat_path": PLACEHOLDER_LAUNCH_BAT_PATH
        }
    default_config = {
        "auth_file_path": PLACEHOLDER_AUTH_PATH,
        "launch_bat_path": PLACEHOLDER_LAUNCH_BAT_PATH
    }
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
                config = json.loads(content) if content.strip() else default_config
                if "auth_file_path" not in config or not config["auth_file_path"]:
                    config["auth_file_path"] = PLACEHOLDER_AUTH_PATH
                if "launch_bat_path" not in config or not config["launch_bat_path"]:
                    config["launch_bat_path"] = PLACEHOLDER_LAUNCH_BAT_PATH
                return config
        else:
            return default_config
    except (json.JSONDecodeError, IOError) as e:
        messagebox.showerror("加载错误", f"加载配置文件 '{CONFIG_FILE}' 时出错: {e}\n将使用默认设置。")
        return default_config

def save_config(config_data):
    if not ensure_dir_exists(data_path): return
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)
    except IOError as e:
        messagebox.showerror("保存错误", f"保存配置到 '{CONFIG_FILE}' 时出错: {e}")

# --- Helper Function to Center Window ---
def center_window(window):
    """Centers a Tkinter window (Tk or Toplevel) on the screen."""
    window.update_idletasks()  # Ensure window dimensions are calculated
    width = window.winfo_width()
    height = window.winfo_height()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    # Only set position, keep the original size set by geometry() or packing
    window.geometry(f'+{x}+{y}')
    # If you also want to force the size determined by winfo_width/height:
    # window.geometry(f'{width}x{height}+{x}+{y}')


def set_icon(root):
    tmp = open("tmp.ico","wb+")  
    tmp.write(base64.b64decode(img)) #写入到临时文件中
    tmp.close()
    root.iconbitmap(default="tmp.ico") #设置图标
    os.remove("tmp.ico")           #删除临时图标

class LauncherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AquaDX Launcher")
        self.root.geometry("450x330")

        self.current_active_username = None
        self.config = load_config()
        self.current_auth_path = self._resolve_path(self.config.get("auth_file_path"), PLACEHOLDER_AUTH_PATH, DEFAULT_AUTH_FILENAME)
        self.current_launch_bat_path = self._resolve_path(self.config.get("launch_bat_path"), PLACEHOLDER_LAUNCH_BAT_PATH, DEFAULT_LAUNCH_BAT_FILENAME)

        # --- 菜单栏 ---
        self.menu_bar = tk.Menu(root)
        root.config(menu=self.menu_bar)
        settings_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="设置", menu=settings_menu)
        settings_menu.add_command(label="账号管理...", command=self.open_manage_accounts_window)
        settings_menu.add_command(label="路径设置...", command=self.open_settings_window)
        settings_menu.add_separator()
        settings_menu.add_command(label="退出", command=root.quit)

        # --- 主界面 ---
        main_frame = ttk.Frame(root, padding="10",)
        main_frame.pack(fill=tk.BOTH, expand=True)

        self.account_label = ttk.Label(main_frame, text="当前账号:")
        self.account_label.pack(pady=(0, 5), anchor=tk.W)
        self.account_label.bind("<Button-1>", lambda event: self.process_current_account_on_startup())
        self.account_label.config(cursor="hand2")

        listbox_frame = ttk.Frame(main_frame)
        # 让这个框架填充可用空间，并允许 Listbox 扩展
        listbox_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # 创建 Scrollbar，父容器是 listbox_frame
        scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y) # 放在右侧，填充垂直空间

        # 创建 Listbox，父容器是 listbox_frame
        # 将 yscrollcommand 关联到 scrollbar.set
        self.account_listbox = tk.Listbox(listbox_frame, height=10, yscrollcommand=scrollbar.set)
        # 放在左侧，填充所有剩余空间
        self.account_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        # 配置 Scrollbar 的 command 来控制 Listbox 的视图
        scrollbar.config(command=self.account_listbox.yview)

        self.accounts = load_accounts()
        self.refresh_main_listbox()

        self.account_listbox.bind("<Double-Button-1>", self.on_double_click_switch)

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 5))

        self.switch_button = ttk.Button(button_frame, text="切换选中账号", command=self.on_switch_button_click)
        self.switch_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))

        # ### 修改 ###: 移除 style 参数，添加 default='active'
        self.launch_game_button = ttk.Button(button_frame, text="启动！", command=self.launch_game_with_switch, default='active')
        self.launch_game_button.pack(side=tk.LEFT, expand=True, fill=tk.X)
        # ### 新增 ###: 让 '启动！' 按钮响应 Enter 键 (需要窗口或框架获取焦点)
        self.root.bind('<Return>', lambda event=None: self.launch_game_button.invoke())
        self.root.bind('<Escape>', lambda event: self.process_current_account_on_startup())
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.update_status_bar()

        self.check_paths_on_start()

        center_window(self.root)

    def _resolve_path(self, config_value, placeholder, default_filename):
        if not config_value or config_value == placeholder:
            return os.path.join(base_path, default_filename)
        else:
            return config_value

    # ### 修改 ###: 重命名并扩展启动时处理逻辑
    def process_current_account_on_startup(self):
        """
        读取卡号文件，执行以下操作：
        1. 如果账号列表为空且卡号文件有卡号，提示用户添加。
        2. 如果账号列表不为空，尝试在列表中选中当前卡号对应的账号。
        3. 更新界面标签。
        """
        self.current_active_username = None # 重置状态
        current_id = ""
        aime_path = self.current_auth_path
        aime_exists = os.path.isfile(aime_path)

        # 1. 尝试读取卡号文件卡号
        if aime_exists:
            try:
                with open(aime_path, 'r', encoding='utf-8') as f:
                    current_id = f.read().strip()
            except IOError as e:
                messagebox.showerror("读取错误", f"读取卡号文件 '{aime_path}' 时出错: {e}", parent=self.root)
                self.account_label.config(text="当前账号: 读取错误")
                return
            except Exception as e:
                 messagebox.showerror("未知错误", f"读取卡号文件时发生未知错误: {e}", parent=self.root)
                 self.account_label.config(text="当前账号: 读取未知错误")
                 return
        else:
            # 文件不存在
            self.account_label.config(text="当前账号: 未知 (卡号文件丢失)")
            return # 无法继续

        # 2. 检查卡号是否为空
        if not current_id:
             # 卡号为空
             self.account_label.config(text="当前账号: 未知 (卡号文件为空)")
             return # 无法继续

        # 3. 在账号列表中查找卡号对应的用户名
        target_username = None
        for username, aid in self.accounts.items():
            if aid == current_id:
                target_username = username
                break # 找到即停止

        # --- 核心判断逻辑 ---
        if target_username is None:
            # === 情况：卡号存在于aime.txt，但在accounts.json中未找到匹配的用户名 ===
            print(f"卡号文件中的卡号 '{current_id}' 未在账号列表中找到，准备提示用户...")
            prompt_title = "未找到账号"
            prompt_message = (f"在卡号文件 ({os.path.basename(aime_path)}) 中检测到卡号:\n"
                              f"{current_id}\n\n"
                              "但此卡号尚未添加到账号列表中。\n"
                              "是否前往账号管理并添加此卡号？")
            add_confirm = messagebox.askyesno(prompt_title, prompt_message, parent=self.root)

            label_text = f"未在列表 (卡号：{current_id})" # 如果不添加，标签显示这个
            active_user_text = label_text        # 如果不添加，当前用户也标记为此状态

            if add_confirm:
                print("用户选择是，打开账号管理并预填卡号。")
                self.open_manage_accounts_window(prefill_id=current_id)
                label_text = f"待添加 (卡号：{current_id})" # 标签显示等待添加
                active_user_text = label_text # 内部状态也标记为等待添加
            else:
                print("用户选择否，不添加。")
                # label_text 和 active_user_text 保持默认的 "未在列表"

            self.account_label.config(text=f"当前账号: {label_text}")
            self.current_active_username = active_user_text

        else:
            # === 情况：卡号存在于aime.txt，且在accounts.json中找到了匹配的用户名 ===
            print(f"卡号文件卡号 '{current_id}' 匹配到账号: '{target_username}'，尝试选中...")
            listbox_items = self.account_listbox.get(0, tk.END)
            try:
                index = listbox_items.index(target_username)
                self.account_listbox.selection_clear(0, tk.END)
                self.account_listbox.selection_set(index)
                self.account_listbox.see(index)
                self.account_listbox.activate(index)
                print(f"启动时自动选中账号: {target_username}")
                self.account_label.config(text=f"当前账号: {target_username}")
                self.current_active_username = target_username # 更新激活用户名
            except ValueError:
                # 虽然找到了匹配，但在列表框中显示时出错了（理论上不应发生，除非列表刷新有问题）
                print(f"错误：账号 '{target_username}' 存在于数据中，但在列表框中未找到。")
                label_text = f"列表显示错误  (卡号: {current_id})"
                self.account_label.config(text=f"当前账号: {label_text}")
                self.current_active_username = label_text # 标记状态


    def update_status_bar(self):
        self.status_var.set(f"当前卡号文件: {self.current_auth_path}")

    def check_paths_on_start(self):
        warnings = []
        if not os.path.isfile(self.current_auth_path):
            if self.current_auth_path == os.path.join(base_path, DEFAULT_AUTH_FILENAME):
                warnings.append(f"默认卡号文件 '{DEFAULT_AUTH_FILENAME}' 在程序目录下未找到。")
            else:
                warnings.append(f"配置的卡号文件路径无效或文件不存在:\n'{self.current_auth_path}'")
        if not os.path.isfile(self.current_launch_bat_path):
            if self.current_launch_bat_path == os.path.join(base_path, DEFAULT_LAUNCH_BAT_FILENAME):
                warnings.append(f"默认游戏启动脚本 '{DEFAULT_LAUNCH_BAT_FILENAME}' 在程序目录下未找到。")
            else:
                warnings.append(f"配置的游戏启动脚本路径无效或文件不存在:\n'{self.current_launch_bat_path}'")
        if warnings:
            message = "启动检查发现问题:\n\n" + "\n\n".join(warnings) + "\n\n请将启动器文件夹放置在游戏目录下，或通过 '设置 -> 路径设置...' 重新指定有效路径。"
            messagebox.showwarning("路径检查警告", message, parent=self.root)

    def refresh_main_listbox(self):
        self.account_listbox.delete(0, tk.END)
        sorted_usernames = sorted(self.accounts.keys())
        for username in sorted_usernames:
            self.account_listbox.insert(tk.END, username)

    def _switch_account(self, username):
        selected_id = self.accounts.get(username)
        if not selected_id:
            messagebox.showerror("错误", f"找不到用户名 '{username}' 对应的卡号。", parent=self.root)
            return False
        if not os.path.isfile(self.current_auth_path):
            if os.path.exists(self.current_auth_path):
                messagebox.showerror("错误", f"卡号文件路径 '{self.current_auth_path}' 不是一个有效的文件！\n请在 '设置' 中修正。", parent=self.root)
            else:
                messagebox.showerror("错误", f"卡号文件 '{self.current_auth_path}' 不存在！\n请在 '设置' 中修正或确保文件存在。", parent=self.root)
            return False
        try:
            target_dir = os.path.dirname(self.current_auth_path)
            if target_dir and not os.path.exists(target_dir):
                os.makedirs(target_dir, exist_ok=True)
            with open(self.current_auth_path, 'w', encoding='utf-8') as f:
                f.write(selected_id)
            self.account_label.config(text=f"当前账号: {username}")
            self.current_active_username = username
            print(f"账号已切换为: {username}")
            return True
        except PermissionError:
            messagebox.showerror("权限错误", f"没有权限写入文件 '{self.current_auth_path}'。\n请检查文件权限或尝试使用管理员权限运行此程序。", parent=self.root)
            return False
        except IOError as e:
            messagebox.showerror("写入错误", f"写入文件 '{self.current_auth_path}' 时发生错误: {e}", parent=self.root)
            return False
        except Exception as e:
            messagebox.showerror("未知错误", f"切换账号时发生未知错误: {e}", parent=self.root)
            return False

    def on_switch_button_click(self):
        selected_indices = self.account_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("提示", "请先在列表中选择一个要切换的账号！", parent=self.root)
            return
        selected_username = self.account_listbox.get(selected_indices[0])
        self._switch_account(selected_username)

    def on_double_click_switch(self, event=None):
        self.on_switch_button_click()

    def _launch_game_script(self):
        if not os.path.isfile(self.current_launch_bat_path):
            messagebox.showerror("错误", f"游戏启动脚本路径无效或文件不存在！\n路径: {self.current_launch_bat_path}\n请在 '设置' 中修正或确保文件存在。", parent=self.root)
            return False
        try:
            bat_dir = os.path.dirname(self.current_launch_bat_path)
            print(f"尝试执行: {self.current_launch_bat_path} (工作目录: {bat_dir})")
            subprocess.Popen([self.current_launch_bat_path], cwd=bat_dir, shell=True)
            return True
        except Exception as e:
            messagebox.showerror("启动错误", f"启动游戏脚本时发生未知错误: {e}", parent=self.root)
            return False

    def launch_game_with_switch(self):
        selected_indices = self.account_listbox.curselection()
        if not selected_indices:
            # messagebox.showwarning("提示", "请先在列表中选择一个要使用的账号，然后再点击启动！", parent=self.root)
            self._launch_game_script()
            return
        selected_username = self.account_listbox.get(selected_indices[0])
        print(f"准备启动，先切换到账号: {selected_username}")

        # --- 新增验证逻辑 ---
        needs_switch = selected_username != self.current_active_username

        if needs_switch:
            # 当前选中账号与实际激活账号不同，需要弹出确认框
            
            proceed = messagebox.askyesno("确认切换并启动", f"将切换到 {selected_username} 并启动游戏。", parent=self.root)

            if proceed:
                # 用户确认切换
                print(f"用户确认，准备切换到账号: {selected_username}")
                if self._switch_account(selected_username):
                    # 切换成功，则启动游戏
                    print("切换成功，尝试启动游戏...")
                    self._launch_game_script()
                else:
                    # 切换失败，不启动游戏 (错误信息已由 _switch_account 显示)
                    print("切换账号失败，取消启动游戏。")
            else:
                # 用户取消切换
                print("用户取消切换操作。")
                return # 直接返回，不做任何事
        else:
            # 当前选中账号与实际激活账号相同，直接启动
            print(f"选中账号 '{selected_username}' 与当前账号一致，直接启动游戏...")
            self._launch_game_script()

    # ### 修改 ###: 接受可选的 prefill_id 参数
    def open_manage_accounts_window(self, prefill_id=None):
        """打开账号管理窗口，可选择预填卡号"""
        # 传递 prefill_id 给 ManageAccountsWindow
        ManageAccountsWindow(self.root, self.accounts.copy(), self.on_accounts_updated, prefill_id=prefill_id)

    def on_accounts_updated(self, updated_accounts):
        """账号管理窗口关闭后调用的回调函数"""
        self.accounts = updated_accounts
        save_accounts(self.accounts) # 保存更新后的账号

        # 刷新列表框
        self.refresh_main_listbox()

        # 账号更新后，重新处理当前账号状态，确保界面一致性
        print("账号列表已更新，重新处理当前账号状态...")
        self.process_current_account_on_startup() # 这会尝试选中当前aime.txt对应的账号

    def open_settings_window(self):
        SettingsWindow(
            self.root,
            self.current_auth_path,
            self.current_launch_bat_path,
            self.on_settings_updated
        )

    def on_settings_updated(self, updated_settings):
        new_auth_path = updated_settings.get("auth_file_path")
        new_bat_path = updated_settings.get("launch_bat_path")
        auth_path_changed = False
        bat_path_changed = False

        if new_auth_path and new_auth_path != self.current_auth_path:
            self.current_auth_path = new_auth_path
            self.config["auth_file_path"] = new_auth_path
            auth_path_changed = True
        if new_bat_path and new_bat_path != self.current_launch_bat_path:
            self.current_launch_bat_path = new_bat_path
            self.config["launch_bat_path"] = new_bat_path
            bat_path_changed = True

        if auth_path_changed or bat_path_changed:
            save_config(self.config)
            updated_items = []
            if auth_path_changed: updated_items.append("卡号文件路径")
            if bat_path_changed: updated_items.append("游戏启动脚本路径")
            messagebox.showinfo("设置更新", f"{' 和 '.join(updated_items)}已更新。", parent=self.root)

            if auth_path_changed:
                self.update_status_bar()
                # 认证路径改变后，需要重新处理当前账号
                print("认证路径已更新，重新处理当前账号状态...")
                self.process_current_account_on_startup()
            # 可以在这里重新检查新路径是否存在
            self.check_paths_on_start()


# --- 账号管理窗口 ---
class ManageAccountsWindow:
    # ### 修改 ###: 构造函数接受 prefill_id
    def __init__(self, parent, accounts_data, update_callback, prefill_id=None):
        self.parent = parent
        # 确保操作的是传入数据的副本，避免直接修改原始字典直到回调
        self.accounts = accounts_data.copy() # 使用 .copy() 确保是副本
        self.update_callback = update_callback
        self.prefill_id = prefill_id
        # <<< 新增: 初始化 IID 到 用户名键 的映射字典 >>>
        self.iid_to_key_map = {}

        self.window = tk.Toplevel(parent)
        self.window.withdraw()
        self.window.title("账号管理")
        # 初始尺寸设定，内容可能会调整实际大小
        self.window.geometry("600x400")
        self.window.transient(parent)
        self.window.grab_set() # 设置为模态窗口

        manage_frame = ttk.Frame(self.window, padding="10")
        manage_frame.pack(fill=tk.BOTH, expand=True)

        # --- Treeview 显示账号 ---
        list_frame = ttk.Frame(manage_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        ttk.Label(list_frame, text="现有账号 (用户名 - 卡号):").pack(anchor=tk.W)
        self.tree = ttk.Treeview(list_frame, columns=('Username', 'ID'), show='headings', selectmode='browse') # selectmode='browse' 确保单选
        self.tree.heading('Username', text='用户名')
        self.tree.heading('ID', text='卡号')
        self.tree.column('Username', width=200, anchor=tk.W)
        self.tree.column('ID', width=250, anchor=tk.W)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        # 填充 Treeview 内容
        self.refresh_treeview()

        # --- 输入框用于添加/编辑 ---
        entry_frame = ttk.Frame(manage_frame)
        entry_frame.pack(fill=tk.X, pady=10)
        ttk.Label(entry_frame, text="用户名:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.username_entry = ttk.Entry(entry_frame, width=25)
        self.username_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        ttk.Label(entry_frame, text="卡号:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.id_entry = ttk.Entry(entry_frame, width=40)
        self.id_entry.grid(row=1, column=1, padx=5, pady=5, columnspan=2, sticky=tk.EW)
        entry_frame.columnconfigure(1, weight=1) # 让输入框随窗口宽度变化
        # 调用 refresh_treeview 来填充并建立映射
        self.refresh_treeview()

        # --- 预填卡号 ---
        if self.prefill_id:
            self.id_entry.insert(0, self.prefill_id)
            self.username_entry.focus_set()

        # --- 按钮 ---
        button_frame = ttk.Frame(manage_frame)
        button_frame.pack(fill=tk.X, pady=5)
        self.add_button = ttk.Button(button_frame, text="添加/修改", command=self.add_or_update_account, default='active')
        self.add_button.pack(side=tk.LEFT, padx=5)
        self.window.bind('<Return>', lambda event=None: self.add_button.invoke())
        # 确认删除按钮绑定了正确的命令
        self.delete_button = ttk.Button(button_frame, text="删除选中", command=self.delete_selected_account)
        self.delete_button.pack(side=tk.LEFT, padx=5)
        self.close_button = ttk.Button(button_frame, text="完成", command=self.close_window)
        self.close_button.pack(side=tk.RIGHT, padx=5)

        # --- 事件绑定 ---
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)
        # <<< 新增: 绑定左键单击事件 >>>
        self.tree.bind("<Button-1>", self.on_tree_click)
        self.window.protocol("WM_DELETE_WINDOW", self.close_window) # 处理关闭窗口按钮

        # --- 窗口居中 ---
        center_window(self.window)
        self.window.deiconify()

    def refresh_treeview(self):
        """清空并重新填充 Treeview，并建立 IID -> Key 映射"""
        # 清空旧映射和 Treeview
        self.iid_to_key_map = {}
        for item in self.tree.get_children():
            try:
                self.tree.delete(item)
            except tk.TclError as e:
                print(f"Error deleting tree item {item}: {e}")

        # 填充新数据并建立映射
        try:
            sorted_usernames = sorted(self.accounts.keys())
            for username in sorted_usernames: # username 是原始的键 (str)
                account_id = self.accounts[username] # account_id 也是原始的 str
                # 插入 Treeview，确保使用字符串，并获取返回的 Item ID (IID)
                # <<< 修改: 获取 insert 返回的 iid >>>
                iid = self.tree.insert('', tk.END, values=(str(username), str(account_id)))
                # <<< 新增: 存储映射关系 >>>
                self.iid_to_key_map[iid] = username # 将 IID 映射到原始的 username 键
        except Exception as e:
             print(f"Error inserting data into treeview or creating map: {e}")

    def on_tree_click(self, event):
        """处理 Treeview 的单击事件，用于取消选中"""
        # 使用 identify_region 判断点击的区域
        region = self.tree.identify_region(event.x, event.y)
        # print(f"Tree clicked region: {region}") # 调试

        # 如果点击区域不是 'cell' 或 'heading' (通常是空白区域或其他非项目区域)
        # 'nothing' 也是 Tcl/Tk 中可能的返回值表示空白
        if region not in ('cell', 'heading', 'separator', 'vsb', 'hsb'): # 'vsb'/'hsb' 是滚动条区域
            # 也可以用 identify_item:
            # item_iid = self.tree.identify('item', event.x, event.y)
            # if not item_iid: # 如果 identify_item 返回空字符串

            # 获取当前的选中项 (可能是一个元组)
            selection = self.tree.selection()
            if selection:
                # 如果有选中项，则取消选中
                print("Clicked on empty space in treeview. Deselecting.") # 调试
                self.tree.selection_remove(selection) # 移除所有选中项
                # 同时清空下面的输入框
                self.clear_entries()

    def on_tree_select(self, event=None):
        """当 Treeview 中的选择变化时，使用 IID 映射获取原始数据填充输入框"""
        selected_items = self.tree.selection()
        if not selected_items:
            return

        # 获取选中的 Item ID (IID)
        iid = selected_items[0]
        try:
            # <<< 修改: 使用 IID 从映射中获取原始用户名键 >>>
            original_username = self.iid_to_key_map.get(iid)

            if original_username is not None: # 检查映射是否成功找到键
                # 使用原始用户名键从 self.accounts 获取原始 ID
                if original_username in self.accounts:
                    original_acc_id = self.accounts[original_username]

                    print(f"on_tree_select: IID '{iid}' mapped to key '{original_username}'. Populating with ID '{original_acc_id}'") # 调试

                    # 使用原始数据填充输入框
                    self.username_entry.delete(0, tk.END)
                    self.username_entry.insert(0, original_username)
                    self.id_entry.delete(0, tk.END)
                    self.id_entry.insert(0, original_acc_id)
                else:
                    # 映射成功但字典中找不到，数据可能已在别处被修改？（理论上不应发生）
                    print(f"Error: Key '{original_username}' from map not found in self.accounts!")
                    messagebox.showerror("内部错误", "账号数据不一致，请重新打开管理窗口。", parent=self.window)
                    self.clear_entries()
            else:
                # 映射失败，可能 IID 无效？
                print(f"Error: Could not find key mapping for selected IID '{iid}'")
                messagebox.showerror("内部错误", "无法识别选中的项目。", parent=self.window)
                self.clear_entries()

        except Exception as e:
             print(f"An unexpected error occurred during tree selection: {e}")
             messagebox.showerror("选择错误", f"处理选中项时发生错误: {e}", parent=self.window)
             self.clear_entries()


    def add_or_update_account(self):
        target_username = self.username_entry.get().strip()
        target_id = self.id_entry.get().strip()

        if not target_username or not target_id:
            messagebox.showwarning("输入不完整", "用户名和卡号都不能为空！", parent=self.window)
            return

        # --- 查找当前状态 ---
        username_exists = target_username in self.accounts
        id_exists = any(uid == target_id for uid in self.accounts.values())

        current_owner_of_id = None
        for uname, uid in self.accounts.items():
            if uid == target_id:
                current_owner_of_id = uname
                break

        current_id_of_username = self.accounts.get(target_username)

        # --- 开始逻辑判断 ---

        # 情况 1: 用户名和卡号都与现有某条记录完全匹配 (无更改)
        if username_exists and current_id_of_username == target_id:
            # 此时 current_owner_of_id 必然等于 target_username
            messagebox.showinfo("无修改", f"用户名 '{target_username}' (卡号: {target_id}) 已存在，未进行任何修改。", parent=self.window)
            return

        # 情况 2: 尝试添加全新的记录 (用户名和卡号都是新的)
        if not username_exists and not id_exists:
            self.accounts[target_username] = target_id
            print(f"Added new account: '{target_username}': '{target_id}'")

        # 情况 3: 用户名已存在，尝试修改其关联的卡号
        elif username_exists and current_id_of_username != target_id:
            # 子情况 3a: 目标卡号未被任何其他人使用 -> 允许修改卡号
            if not id_exists:
                if messagebox.askyesno("确认修改卡号？",
                                    f"用户名 '{target_username}' 已存在。\n"
                                    f"是否要将其关联的卡号从 '{current_id_of_username}' 修改为 '{target_id}'？",
                                    parent=self.window):
                    self.accounts[target_username] = target_id
                    print(f"Updated ID for user '{target_username}' to '{target_id}'")
                else: # 用户取消修改
                    return
            # 子情况 3b: 目标卡号已被其他人使用 -> 阻止操作 (卡号冲突)
            else: # id_exists is True, 并且 current_id_of_username != target_id 说明这个卡号属于别人
                messagebox.showerror("数据冲突",
                                    f"无法修改：\n"
                                    f"用户名 '{target_username}' 或卡号 '{target_id}' 已被占用。",
                                    parent=self.window)
                return

        # 情况 4: 卡号已存在，尝试修改其关联的用户名 (重命名)
        elif not username_exists and id_exists:
            # 子情况 4a: 目标用户名未被使用 -> 允许重命名
            # (这里的 username_exists 检查已经保证了目标用户名是新的)
            if messagebox.askyesno("确认重命名用户？",
                                f"卡号 '{target_id}' 当前属于用户:\n"
                                f"'{current_owner_of_id}'\n\n"
                                f"是否要将此卡号关联的用户重命名为 '{target_username}'？",
                                parent=self.window):
                 # 先删除旧的用户名条目
                del self.accounts[current_owner_of_id]
                 # 添加新的用户名和卡号条目
                self.accounts[target_username] = target_id
                print(f"Renamed user for ID '{target_id}' from '{current_owner_of_id}' to '{target_username}'")
            else: # 用户取消重命名
                return
            # 子情况 4b: (理论上不会发生，因为外层 elif 检查了 not username_exists)
            # else: # target_username 已存在 -> 阻止操作 (用户名冲突)
            #     messagebox.showerror("用户名冲突",
            #                         f"无法重命名：用户名 '{target_username}'\n"
            #                         f"已经被卡号 '{current_id_of_username}' 使用。\n\n"
            #                         f"每个用户名必须唯一。",
            #                         parent=self.window)
            #     return


        else:
             # 捕获未预料到的状态
            print(f"Warning: Unhandled state! username_exists={username_exists}, id_exists={id_exists}, current_id_of_username={current_id_of_username}, current_owner_of_id={current_owner_of_id}")
            messagebox.showerror("逻辑错误", "遇到未处理的账号状态，请联系开发者。", parent=self.window)
            return # 出现未处理情况，阻止后续

        # --- 如果执行到这里，说明进行了有效的添加或修改 ---
        self.refresh_treeview()
        self.clear_entries()
        self.username_entry.focus_set()

    # --- !!! 检查这个方法 !!! ---
    def delete_selected_account(self):
        """删除 Treeview 中选中的账号，使用 IID 映射获取键"""
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("未选择", "请先在列表中选择要删除的账号！", parent=self.window)
            return

        # 获取选中的 Item ID (IID)
        iid = selected_items[0]
        try:
            # <<< 修改: 使用 IID 从映射中获取原始用户名键 >>>
            username_to_delete = self.iid_to_key_map.get(iid)

            if username_to_delete is None:
                # 映射失败
                print(f"Error: Could not find key mapping for selected IID '{iid}' for deletion.")
                messagebox.showerror("内部错误", "无法识别要删除的项目。", parent=self.window)
                return

            print(f"Attempting to delete account with key from map: '{username_to_delete}'") # 调试

            # 再次确认删除
            if messagebox.askyesno("确认删除", f"确定要删除账号 '{username_to_delete}' 吗？", parent=self.window):
                # 使用从映射获取的原始键进行检查和删除
                if username_to_delete in self.accounts:
                    del self.accounts[username_to_delete] # 从字典副本中删除
                    print(f"Account '{username_to_delete}' deleted from internal dictionary.")
                    # 从映射中也移除（虽然刷新时会重建，但保持一致性较好）
                    if iid in self.iid_to_key_map:
                        del self.iid_to_key_map[iid]
                    self.refresh_treeview() # 刷新 Treeview 以移除该行并重建映射
                    self.clear_entries() # 清空输入框
                    print("Deletion successful in ManageAccountsWindow.")
                else:
                    # 映射成功但字典中找不到键
                    print(f"Error: Key '{username_to_delete}' from map not found in self.accounts dictionary for deletion!")
                    messagebox.showerror("数据不一致", f"尝试删除的用户 '{username_to_delete}' 在内部数据中未找到。", parent=self.window)
                    self.refresh_treeview() # 强制刷新同步
            else:
                print("Deletion cancelled by user.")

        except Exception as e:
             print(f"An error occurred during deletion process: {e}")
             messagebox.showerror("删除错误", f"删除过程中发生错误: {e}", parent=self.window)

    def clear_entries(self):
        """清空用户名和卡号输入框"""
        self.username_entry.delete(0, tk.END)
        self.id_entry.delete(0, tk.END)
        # 取消 Treeview 中的选择高亮可能不是必要的，但可以加上
        # self.tree.selection_remove(self.tree.selection())

    def close_window(self):
        """关闭窗口并调用回调函数传递修改后的数据"""
        print("Closing ManageAccountsWindow, calling update callback...") # 调试信息
        # 将修改后的 self.accounts (副本) 传递回主应用
        self.update_callback(self.accounts)
        self.window.destroy()


# --- 设置窗口 ---
# ... (SettingsWindow 类不变) ...
class SettingsWindow:
    def __init__(self, parent, current_auth_path, current_launch_path, update_callback):
        # ... (代码同前) ...
        self.parent = parent
        self.update_callback = update_callback
        self.auth_path_var = tk.StringVar(value=current_auth_path)
        self.launch_path_var = tk.StringVar(value=current_launch_path)
        self.window = tk.Toplevel(parent)
        self.window.withdraw()
        self.window.title("路径设置")
        self.window.geometry("600x230")
        self.window.transient(parent)
        self.window.grab_set()
        settings_frame = ttk.Frame(self.window, padding="15")
        settings_frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(settings_frame, text="卡号文件路径 (例如 aime.txt):").grid(row=0, column=0, padx=5, pady=(5,0), sticky=tk.W)
        self.auth_path_entry = ttk.Entry(settings_frame, textvariable=self.auth_path_var, width=70)
        self.auth_path_entry.grid(row=1, column=0, padx=5, pady=(0,10), sticky=tk.EW)
        auth_browse_button = ttk.Button(settings_frame, text="浏览...", command=self.browse_auth_file)
        auth_browse_button.grid(row=1, column=1, padx=5, pady=(0,10))
        ttk.Label(settings_frame, text="游戏启动脚本路径 (例如 启动.bat):").grid(row=2, column=0, padx=5, pady=(10,0), sticky=tk.W)
        self.launch_path_entry = ttk.Entry(settings_frame, textvariable=self.launch_path_var, width=70)
        self.launch_path_entry.grid(row=3, column=0, padx=5, pady=(0,10), sticky=tk.EW)
        launch_browse_button = ttk.Button(settings_frame, text="浏览...", command=self.browse_launch_file)
        launch_browse_button.grid(row=3, column=1, padx=5, pady=(0,10))
        settings_frame.columnconfigure(0, weight=1)
        button_frame = ttk.Frame(settings_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)
        save_button = ttk.Button(button_frame, text="保存", command=self.save_settings, default='active')
        self.window.bind('<Return>', lambda event=None: save_button.invoke())
        save_button.pack(side=tk.LEFT, padx=10)
        cancel_button = ttk.Button(button_frame, text="取消", command=self.window.destroy)
        cancel_button.pack(side=tk.LEFT, padx=10)
        self.window.protocol("WM_DELETE_WINDOW", self.window.destroy)

        center_window(self.window)
        self.window.deiconify()

    def browse_auth_file(self):
        current_val = self.auth_path_var.get()
        initial_dir = base_path
        try:
             dir_name = os.path.dirname(current_val)
             if dir_name and os.path.isdir(dir_name): initial_dir = dir_name
        except Exception: pass
        file_path = filedialog.askopenfilename(title="选择卡号文件 (.txt)", initialdir=initial_dir, filetypes=[("Text files", "*.txt"), ("All files", "*.*")], parent=self.window)
        if file_path: self.auth_path_var.set(file_path)

    def browse_launch_file(self):
        current_val = self.launch_path_var.get()
        initial_dir = base_path
        try:
            dir_name = os.path.dirname(current_val)
            if dir_name and os.path.isdir(dir_name): initial_dir = dir_name
        except Exception: pass
        file_path = filedialog.askopenfilename(title="选择游戏启动脚本 (.bat, .exe)", initialdir=initial_dir, filetypes=[("Scripts/Executables", "*.bat;*.exe"), ("Batch files", "*.bat"), ("Executable files", "*.exe"), ("All files", "*.*")], parent=self.window)
        if file_path: self.launch_path_var.set(file_path)

    def save_settings(self):
        new_auth_path = self.auth_path_var.get().strip()
        new_launch_path = self.launch_path_var.get().strip()
        errors = []
        if not new_auth_path: errors.append("卡号文件路径不能为空！")
        if not new_launch_path: errors.append("游戏启动脚本路径不能为空！")
        if errors:
            messagebox.showwarning("输入无效", "\n\n".join(errors), parent=self.window)
            return
        updated_settings = {"auth_file_path": new_auth_path, "launch_bat_path": new_launch_path}
        self.update_callback(updated_settings)
        self.window.destroy()


# --- 程序入口 ---
if __name__ == "__main__":
    root = tk.Tk()

    # <<< Add this line: Hide the window immediately >>>
    root.withdraw()

    # Initialize the app (this builds the UI and calls center_window internally)
    app = LauncherApp(root)

    set_icon(root)

    # <<< Add this line: Show the window only AFTER it's built and centered >>>
    root.deiconify()

    root.after(100, lambda: app.process_current_account_on_startup())

    root.mainloop()