import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import os
import json
import sys

# --- 常量 ---
ACCOUNTS_FILE_NAME = 'accounts.json'
CONFIG_FILE_NAME = 'config.json'
DEFAULT_AUTH_PATH = "请设置认证文件的路径" # 默认提示路径

# --- 确定基础路径 (用于数据文件) ---
# 这个路径将是 .py 脚本所在的目录，或者是 .exe 文件所在的目录
if getattr(sys, 'frozen', False):
    # 如果是打包后的程序 (frozen)
    base_path = os.path.dirname(sys.executable)
elif __file__:
    # 如果是作为 .py 脚本运行
    base_path = os.path.dirname(os.path.abspath(__file__))
else:
    # Fallback (例如在交互式解释器中，虽然不太可能用于此应用)
    base_path = os.getcwd()

# --- 定义数据文件的完整路径 ---
ACCOUNTS_FILE = os.path.join(base_path, ACCOUNTS_FILE_NAME)
CONFIG_FILE = os.path.join(base_path, CONFIG_FILE_NAME)

# --- 账号数据管理 ---
def load_accounts():
    """从 JSON 文件加载账号数据"""
    try:
        if os.path.exists(ACCOUNTS_FILE):
            with open(ACCOUNTS_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
                return json.loads(content) if content else {}
        else:
            return {}
    except (json.JSONDecodeError, IOError) as e:
        messagebox.showerror("加载错误", f"加载账号文件 '{ACCOUNTS_FILE_NAME}' 时出错: {e}\n将使用空列表。")
        return {}

def save_accounts(accounts_data):
    """将账号数据保存到 JSON 文件"""
    try:
        with open(ACCOUNTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(accounts_data, f, indent=4, ensure_ascii=False)
    except IOError as e:
        messagebox.showerror("保存错误", f"保存账号到 '{ACCOUNTS_FILE_NAME}' 时出错: {e}")

# --- 配置管理 ---
def load_config():
    """从 JSON 文件加载配置数据"""
    default_config = {"auth_file_path": DEFAULT_AUTH_PATH}
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
                config = json.loads(content) if content else default_config
                # 确保关键键存在
                if "auth_file_path" not in config:
                    config["auth_file_path"] = DEFAULT_AUTH_PATH
                return config
        else:
            return default_config # 文件不存在，返回默认配置
    except (json.JSONDecodeError, IOError) as e:
        messagebox.showerror("加载错误", f"加载配置文件 '{CONFIG_FILE_NAME}' 时出错: {e}\n将使用默认设置。")
        return default_config

def save_config(config_data):
    """将配置数据保存到 JSON 文件"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)
    except IOError as e:
        messagebox.showerror("保存错误", f"保存配置到 '{CONFIG_FILE_NAME}' 时出错: {e}")

# --- 主应用逻辑 ---
class AccountSwitcherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("账号切换器")
        self.root.geometry("400x350")

        self.config = load_config() # 加载配置
        self.accounts = load_accounts() # 加载账号
        self.current_auth_path = self.config.get("auth_file_path", DEFAULT_AUTH_PATH) # 获取当前路径

        # --- 创建菜单栏 ---
        self.menu_bar = tk.Menu(root)
        root.config(menu=self.menu_bar)

        # --- 设置菜单 ---
        settings_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="设置", menu=settings_menu)
        settings_menu.add_command(label="管理账号...", command=self.open_manage_accounts_window)
        settings_menu.add_command(label="认证文件路径设置...", command=self.open_settings_window)
        settings_menu.add_separator()
        settings_menu.add_command(label="退出", command=root.quit)

        # --- 主界面元素 ---
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="请选择要切换的账号 (用户名):").pack(pady=(0, 5))

        self.account_listbox = tk.Listbox(main_frame, height=10)
        self.account_listbox.pack(fill=tk.X, expand=True, pady=5)
        self.refresh_main_listbox()

        self.account_listbox.bind("<Double-Button-1>", self.on_switch_button_click)

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)

        self.switch_button = ttk.Button(button_frame, text="切换选中账号", command=self.on_switch_button_click)
        self.switch_button.pack(side=tk.LEFT, expand=True, padx=5)

        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.update_status_bar()

        # 启动时检查路径是否有效
        self.check_auth_path_on_start()

    def update_status_bar(self):
        """更新状态栏显示当前认证路径"""
        path_to_display = self.current_auth_path
        if path_to_display == DEFAULT_AUTH_PATH:
             self.status_var.set("状态: 未设置认证文件路径，请前往“设置”菜单配置")
        else:
            # 可以在状态栏显示部分路径如果太长
            # short_path = "..." + path_to_display[-40:] if len(path_to_display) > 43 else path_to_display
            self.status_var.set(f"当前认证文件: {path_to_display}")

    def check_auth_path_on_start(self):
         """启动时检查路径配置"""
         if self.current_auth_path == DEFAULT_AUTH_PATH:
             messagebox.showwarning("配置提示", "尚未配置认证文件的路径。\n请通过 '设置 -> 认证文件路径设置...' 来指定文件。", parent=self.root)

    def refresh_main_listbox(self):
        """刷新主窗口的账号列表"""
        self.account_listbox.delete(0, tk.END)
        sorted_usernames = sorted(self.accounts.keys())
        for username in sorted_usernames:
            self.account_listbox.insert(tk.END, username)

    def on_switch_button_click(self, event=None):
        """切换按钮点击或双击列表项事件"""
        # 检查路径是否已设置
        if self.current_auth_path == DEFAULT_AUTH_PATH or not self.current_auth_path:
            messagebox.showerror("错误", "请先在 '设置 -> 认证文件路径设置...' 中设置有效的认证文件路径！", parent=self.root)
            return

        selected_indices = self.account_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("提示", "请先在列表中选择一个账号！", parent=self.root)
            return

        selected_username = self.account_listbox.get(selected_indices[0])
        selected_id = self.accounts.get(selected_username)

        if not selected_id:
            messagebox.showerror("错误", f"找不到用户名 '{selected_username}' 对应的ID。", parent=self.root)
            return

        # --- 写入认证文件 ---
        try:
            # 确保目标目录存在 (如果路径包含目录)
            target_dir = os.path.dirname(self.current_auth_path)
            if target_dir and not os.path.exists(target_dir):
                os.makedirs(target_dir, exist_ok=True)
                print(f"创建目录: {target_dir}") # Debugging

            # 写入文件
            with open(self.current_auth_path, 'w', encoding='utf-8') as f:
                f.write(selected_id)

            messagebox.showinfo("成功", f"账号已成功切换为: {selected_username}\nID: {selected_id}\n文件 '{os.path.basename(self.current_auth_path)}' 已更新。", parent=self.root)
            self.update_status_bar() # 更新状态栏可能没必要，但可以放着

        except PermissionError:
             messagebox.showerror("权限错误", f"没有权限写入文件 '{self.current_auth_path}'。\n请检查文件权限或尝试使用管理员权限运行此程序。", parent=self.root)
        except IOError as e:
             messagebox.showerror("写入错误", f"写入文件 '{self.current_auth_path}' 时发生错误: {e}", parent=self.root)
        except Exception as e:
            messagebox.showerror("未知错误", f"切换账号时发生未知错误: {e}", parent=self.root)

    def open_manage_accounts_window(self):
        """打开账号管理窗口"""
        # 传入当前账号数据和保存回调
        ManageAccountsWindow(self.root, self.accounts.copy(), self.on_accounts_updated)

    def on_accounts_updated(self, updated_accounts):
        """账号管理窗口关闭后调用的回调函数"""
        self.accounts = updated_accounts
        save_accounts(self.accounts) # 保存更新后的账号
        self.refresh_main_listbox() # 刷新主列表
        # self.status_var.set("账号列表已更新") # 暂时不更新状态栏这个信息

    def open_settings_window(self):
        """打开设置窗口"""
        SettingsWindow(self.root, self.current_auth_path, self.on_settings_updated)

    def on_settings_updated(self, new_path):
        """设置窗口关闭后调用的回调函数"""
        if new_path and new_path != self.current_auth_path:
            self.current_auth_path = new_path
            self.config["auth_file_path"] = new_path
            save_config(self.config) # 保存新的配置
            self.update_status_bar() # 更新状态栏显示新路径
            messagebox.showinfo("设置更新", "认证文件路径已更新。", parent=self.root)


# --- 账号管理窗口 (基本不变，主要是调用方式变化) ---
class ManageAccountsWindow:
    # ... (之前的 ManageAccountsWindow 代码基本可以原样复制过来) ...
    # (确保构造函数、方法中的 parent=self.window 等模态设置正确)
    def __init__(self, parent, accounts_data, update_callback):
        self.parent = parent
        self.accounts = accounts_data # 直接使用传入的副本
        self.update_callback = update_callback

        self.window = tk.Toplevel(parent)
        self.window.title("管理账号")
        self.window.geometry("500x400")
        self.window.transient(parent)
        self.window.grab_set()

        manage_frame = ttk.Frame(self.window, padding="10")
        manage_frame.pack(fill=tk.BOTH, expand=True)

        list_frame = ttk.Frame(manage_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        ttk.Label(list_frame, text="现有账号 (用户名 - ID):").pack(anchor=tk.W)
        self.tree = ttk.Treeview(list_frame, columns=('Username', 'ID'), show='headings')
        self.tree.heading('Username', text='用户名')
        self.tree.heading('ID', text='账号ID')
        self.tree.column('Username', width=200)
        self.tree.column('ID', width=250)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.refresh_treeview()

        entry_frame = ttk.Frame(manage_frame)
        entry_frame.pack(fill=tk.X, pady=10)
        ttk.Label(entry_frame, text="用户名:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.username_entry = ttk.Entry(entry_frame, width=25)
        self.username_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        ttk.Label(entry_frame, text="账号ID:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.id_entry = ttk.Entry(entry_frame, width=40)
        self.id_entry.grid(row=1, column=1, padx=5, pady=5, columnspan=2, sticky=tk.EW)
        entry_frame.columnconfigure(1, weight=1)

        button_frame = ttk.Frame(manage_frame)
        button_frame.pack(fill=tk.X, pady=5)
        self.add_button = ttk.Button(button_frame, text="添加/更新", command=self.add_or_update_account)
        self.add_button.pack(side=tk.LEFT, padx=5)
        self.delete_button = ttk.Button(button_frame, text="删除选中", command=self.delete_selected_account)
        self.delete_button.pack(side=tk.LEFT, padx=5)
        self.close_button = ttk.Button(button_frame, text="完成", command=self.close_window) # 改为“完成”更合适
        self.close_button.pack(side=tk.RIGHT, padx=5)

        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)

    def refresh_treeview(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        sorted_usernames = sorted(self.accounts.keys())
        for username in sorted_usernames:
            self.tree.insert('', tk.END, values=(username, self.accounts[username]))

    def on_tree_select(self, event):
        selected_items = self.tree.selection()
        if not selected_items: return
        item = self.tree.item(selected_items[0])
        username, acc_id = item['values']
        self.username_entry.delete(0, tk.END); self.username_entry.insert(0, username)
        self.id_entry.delete(0, tk.END); self.id_entry.insert(0, acc_id)

    def add_or_update_account(self):
        username = self.username_entry.get().strip()
        account_id = self.id_entry.get().strip()
        if not username or not account_id:
            messagebox.showwarning("输入不完整", "用户名和账号ID都不能为空！", parent=self.window)
            return

        if username in self.accounts and self.accounts[username] != account_id:
            if messagebox.askyesno("确认更新", f"用户名 '{username}' 已存在。\n是否要将其ID更新为 '{account_id}'？", parent=self.window):
                self.accounts[username] = account_id
            else: return
        elif username not in self.accounts:
             self.accounts[username] = account_id
        # else: # ID相同无需提示
        #     messagebox.showinfo("提示", f"账号 '{username}' 及其ID已存在。", parent=self.window)

        self.refresh_treeview()
        self.clear_entries()

    def delete_selected_account(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("未选择", "请先在列表中选择要删除的账号！", parent=self.window)
            return
        item = self.tree.item(selected_items[0])
        username_to_delete = item['values'][0]
        if messagebox.askyesno("确认删除", f"确定要删除账号 '{username_to_delete}' 吗？", parent=self.window):
            if username_to_delete in self.accounts:
                del self.accounts[username_to_delete]
                self.refresh_treeview()
                self.clear_entries()
            # else: # 理论上不会发生
            #     messagebox.showerror("错误", "找不到要删除的账号。", parent=self.window)

    def clear_entries(self):
        self.username_entry.delete(0, tk.END)
        self.id_entry.delete(0, tk.END)
        self.tree.selection_remove(self.tree.selection())

    def close_window(self):
        self.update_callback(self.accounts) # 将修改后的数据传回主窗口
        self.window.destroy()

# --- 设置窗口 (管理认证文件路径) ---
class SettingsWindow:
    def __init__(self, parent, current_path, update_callback):
        self.parent = parent
        # 确保即使 current_path 是 None 或空字符串也能处理
        initial_value = current_path if current_path and current_path != DEFAULT_AUTH_PATH else ""
        self.current_path = tk.StringVar(value=initial_value)
        self.update_callback = update_callback

        self.window = tk.Toplevel(parent)
        self.window.title("认证文件路径设置")
        self.window.geometry("550x150")
        self.window.transient(parent)
        self.window.grab_set()

        settings_frame = ttk.Frame(self.window, padding="15")
        settings_frame.pack(fill=tk.BOTH, expand=True)

        # 提示文字修改为“选择”
        ttk.Label(settings_frame, text="选择认证文件 (aime.txt):").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.path_entry = ttk.Entry(settings_frame, textvariable=self.current_path, width=60)
        self.path_entry.grid(row=1, column=0, padx=5, pady=5, sticky=tk.EW)

        browse_button = ttk.Button(settings_frame, text="浏览...", command=self.browse_file)
        browse_button.grid(row=1, column=1, padx=5, pady=5)

        settings_frame.columnconfigure(0, weight=1)

        button_frame = ttk.Frame(settings_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=15)

        save_button = ttk.Button(button_frame, text="保存", command=self.save_settings)
        save_button.pack(side=tk.LEFT, padx=10)

        cancel_button = ttk.Button(button_frame, text="取消", command=self.window.destroy)
        cancel_button.pack(side=tk.LEFT, padx=10)

        self.window.protocol("WM_DELETE_WINDOW", self.window.destroy)

    def browse_file(self):
        """打开文件对话框选择 *现有* 的认证文件路径"""
        # 确定初始浏览目录
        current_val = self.current_path.get()
        initial_dir = "/" # 默认根目录
        # 尝试使用当前设置路径的目录，如果有效的话
        if current_val and os.path.exists(os.path.dirname(current_val)):
             initial_dir = os.path.dirname(current_val)
        # 否则尝试使用程序所在的目录
        elif os.path.exists(base_path): # base_path 是全局计算的程序或脚本目录
             initial_dir = base_path

        # ******** 主要修改点：使用 askopenfilename ********
        file_path = filedialog.askopenfilename(
            title="选择认证文件 (.txt)",
            initialdir=initial_dir,
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            parent=self.window  # 确保对话框在设置窗口之上
        )
        # ******** 修改结束 ********

        if file_path: # 如果用户选择了文件 (返回的是选定文件的完整路径)
            self.current_path.set(file_path) # 更新输入框中的路径

    def save_settings(self):
        """保存设置并关闭窗口"""
        new_path = self.current_path.get().strip()
        if not new_path:
             messagebox.showwarning("路径为空", "认证文件路径不能为空！", parent=self.window)
             return
        # 检查选择的文件是否存在 (虽然askopenfilename保证存在，但作为防御性编程)
        if not os.path.exists(new_path):
             messagebox.showerror("文件不存在", f"选择的文件 '{new_path}' 似乎不存在或无法访问。", parent=self.window)
             return
        # 也可以加一个检查是否真的是文件而不是目录
        if not os.path.isfile(new_path):
             messagebox.showerror("路径无效", f"选择的路径 '{new_path}' 不是一个有效的文件。", parent=self.window)
             return

        self.update_callback(new_path)
        self.window.destroy()


# --- 程序入口 ---
if __name__ == "__main__":
    root = tk.Tk()
    app = AccountSwitcherApp(root)
    root.mainloop()