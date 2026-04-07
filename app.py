import tkinter as tk
from tkinter import simpledialog, messagebox
import pyautogui
import time
import threading
import json
import os
import glob

class MUAutoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Auto Click Loop")
        self.root.geometry("520x720")
        self.steps = []
        self.current_file = None
        self.pending_capture = None

        # --- SET APP ICON Ở ĐÂY ---
        try:
            icon_path = "logo-app.png" if os.path.exists("logo-app.png") else "logo.png"
            app_icon = tk.PhotoImage(file=icon_path)
            self.root.iconphoto(True, app_icon)
        except Exception as e:
            print(f"Lỗi load app icon: {e}")

        # --- Bố cục chính: Dùng PanedWindow có thanh kéo (sash) rõ ràng ---
        # sashwidth và sashrelief giúp tạo ra một đường rãnh nổi để người dùng biết có thể kéo được
        self.main_paned = tk.PanedWindow(self.root, orient=tk.VERTICAL, sashwidth=6, sashrelief=tk.RAISED)
        self.main_paned.pack(fill=tk.BOTH, expand=True)

        # 1. TOP PANEL: Quản lý file
        self.top_frame = tk.Frame(self.main_paned, bg="#f0f0f0", padx=8, pady=8)
        self.main_paned.add(self.top_frame, minsize=180)

        self.toolbar = tk.Frame(self.top_frame, bg="#f0f0f0")
        self.toolbar.pack(fill=tk.X)

        tk.Button(self.toolbar, text="➕", font=("Arial", 14), command=self.new_script, relief=tk.FLAT, bg="#e0e0e0").pack(side=tk.LEFT, padx=2)
        tk.Button(self.toolbar, text="💾", font=("Arial", 14), command=self.save_script, relief=tk.FLAT, bg="#e0e0e0").pack(side=tk.LEFT, padx=2)

        tk.Label(self.top_frame, text="Kịch bản hiện có:", bg="#f0f0f0", font=("Arial", 10, "italic")).pack(pady=(10, 0), anchor="w")
        
        self.file_listbox = tk.Listbox(self.top_frame, font=("Arial", 11), bg="white", selectmode=tk.SINGLE)
        self.file_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        self.file_listbox.bind('<<ListboxSelect>>', self.on_file_select)

        # 2. BOTTOM PANEL: Khu vực kịch bản và action
        self.content_frame = tk.Frame(self.main_paned, padx=10, pady=8)
        self.main_paned.add(self.content_frame, minsize=340)

        self.lbl_status = tk.Label(self.content_frame, text="Kịch bản mới", font=("Arial", 12, "bold"), fg="blue")
        self.lbl_status.pack(anchor="w")
        self.lbl_run_status = tk.Label(self.content_frame, text="Trạng thái automation: Chưa chạy", font=("Arial", 10), fg="#555555")
        self.lbl_run_status.pack(anchor="w", pady=(2, 6))

        self.step_listbox = tk.Listbox(self.content_frame, font=("Arial", 12))
        self.step_listbox.pack(fill=tk.BOTH, expand=True, pady=(4, 8))

        # --- VÙNG NÚT CHỨC NĂNG ---
        self.control_frame = tk.Frame(self.content_frame)
        self.control_frame.pack(fill=tk.X, pady=5)

        # Danh sách cấu hình các nút
        btn_configs = [
            ("📍 Tọa độ", self.get_mouse_pos, "black"),
            ("⏱ Delay", self.add_delay, "black"),
            ("🖱 Click", self.add_click, "black"),
            ("🔍 Tìm Ảnh", self.add_find_image, "black"),
            ("❌ Xóa", self.remove_step, "red"),
            ("ℹ️ Hướng dẫn", self.show_guide, "blue")
        ]

        self.action_buttons = []
        for text, cmd, color in btn_configs:
            btn = tk.Button(self.control_frame, text=text, command=cmd, fg=color, width=12)
            self.action_buttons.append(btn)

        # Bắt sự kiện khi khung chứa nút bị thay đổi kích thước
        self.control_frame.bind("<Configure>", self.on_control_resize)

        # --- Nút Chạy ---
        self.run_btn = tk.Button(self.content_frame, text="🚀 BẮT ĐẦU", bg="#28a745", font=("Arial", 14, "bold"), command=self.start_macro)
        self.run_btn.pack(fill=tk.X, pady=10)

        self.refresh_file_list()

    # --- Logic Flex-wrap cho các nút ---
    def on_control_resize(self, event):
        """Tính toán lại vị trí Grid để các nút rớt dòng tự động"""
        frame_width = event.width

        if frame_width <= 0 or not self.action_buttons:
            return

        # Đo chiều rộng thực tế của nút lớn nhất thay vì dùng số cố định.
        self.control_frame.update_idletasks()
        button_width = max(btn.winfo_reqwidth() for btn in self.action_buttons) + 8

        # Số cột tối đa có thể nhét vừa trong khung hiện tại
        columns = max(1, frame_width // button_width)

        for col in range(len(self.action_buttons)):
            self.control_frame.grid_columnconfigure(col, weight=0)
        for col in range(columns):
            self.control_frame.grid_columnconfigure(col, weight=1)

        # Xếp lại từng nút vào đúng hàng và cột
        for index, btn in enumerate(self.action_buttons):
            row = index // columns
            col = index % columns
            btn.grid(row=row, column=col, padx=3, pady=3, sticky="ew")

    # --- Các hàm Quản lý File & Logic cũ ---
    def refresh_file_list(self):
        self.file_listbox.delete(0, tk.END)
        for f in glob.glob("*.json"):
            self.file_listbox.insert(tk.END, f)

    def on_file_select(self, event):
        sel = self.file_listbox.curselection()
        if sel: self.load_script(self.file_listbox.get(sel[0]))

    def new_script(self):
        if self.steps and messagebox.askyesno("Xác nhận", "Tạo kịch bản mới? (Chưa lưu sẽ mất)"):
            self.steps = []; self.current_file = None
            self.lbl_status.config(text="Kịch bản mới", fg="blue")
            self.update_listbox()

    def save_script(self):
        if not self.steps: return
        if not self.current_file:
            name = simpledialog.askstring("Lưu", "Nhập tên kịch bản (không cần .json):")
            if not name: return
            self.current_file = f"{name}.json"
        with open(self.current_file, 'w', encoding='utf-8') as f:
            json.dump(self.steps, f, indent=4)
        self.lbl_status.config(text=f"Đang mở: {self.current_file}", fg="green")
        self.refresh_file_list()

    def load_script(self, filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f: self.steps = json.load(f)
            self.current_file = filename
            self.lbl_status.config(text=f"Đang mở: {filename}", fg="green")
            self.update_listbox()
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def update_listbox(self):
        self.step_listbox.delete(0, tk.END)
        for i, step in enumerate(self.steps):
            if step["action"] == "click":
                label = f"{i+1}. CLICK ({step['x']}, {step['y']})"
            elif step["action"] == "delay":
                label = f"{i+1}. DELAY ({step['value']}s)"
            elif step["action"] == "find_click":
                label = f"{i+1}. FIND_CLICK ({os.path.basename(step['image'])})"
            else:
                label = f"{i+1}. {step['action'].upper()}"
            self.step_listbox.insert(tk.END, label)

    def get_mouse_pos(self):
        if self.pending_capture:
            return
        self.pending_capture = "position"
        self.set_capture_state("Chuẩn bị lấy tọa độ...")
        self.root.after(3000, self.capture_mouse_pos)

    def finish_get_mouse_pos(self, x, y):
        coord_text = f"{x},{y}"
        self.root.clipboard_clear()
        self.root.clipboard_append(coord_text)
        self.clear_capture_state()
        messagebox.showinfo("Tọa độ", f"X: {x}, Y: {y}\n\nĐã copy vào clipboard: {coord_text}")

    def handle_get_mouse_pos_error(self, error):
        self.clear_capture_state()
        messagebox.showerror("Lỗi", f"Không thể lấy tọa độ: {error}")

    def add_delay(self):
        val = simpledialog.askfloat("Input", "Giây:"); 
        if val: self.steps.append({"action": "delay", "value": val}); self.update_listbox()

    def add_click(self):
        if self.pending_capture:
            return
        self.pending_capture = "click"
        self.set_capture_state("Chuẩn bị lấy tọa độ click...")
        self.root.after(3000, self.capture_click_pos)

    def finish_add_click(self, x, y):
        self.steps.append({"action": "click", "x": x, "y": y})
        self.update_listbox()
        self.clear_capture_state()
        messagebox.showinfo("Đã lưu tọa độ", f"Đã thêm click tại X: {x}, Y: {y}")

    def handle_add_click_error(self, error):
        self.clear_capture_state()
        messagebox.showerror("Lỗi", f"Không thể lấy tọa độ click: {error}")

    def set_capture_state(self, status_text):
        self.run_btn.config(text=status_text, state=tk.DISABLED)
        self.lbl_status.config(text="Đưa chuột tới vị trí cần lấy trong 3 giây...", fg="orange")

    def clear_capture_state(self):
        self.pending_capture = None
        self.run_btn.config(text="🚀 BẮT ĐẦU", state=tk.NORMAL)
        self.set_run_status("Trạng thái automation: Chưa chạy", "#555555")
        if self.current_file:
            self.lbl_status.config(text=f"Đang mở: {self.current_file}", fg="green")
        else:
            self.lbl_status.config(text="Kịch bản mới", fg="blue")

    def set_run_status(self, text, color="#555555"):
        self.lbl_run_status.config(text=text, fg=color)

    def capture_mouse_pos(self):
        try:
            x, y = pyautogui.position()
            self.finish_get_mouse_pos(x, y)
        except Exception as e:
            self.handle_get_mouse_pos_error(e)

    def capture_click_pos(self):
        try:
            x, y = pyautogui.position()
            self.finish_add_click(x, y)
        except Exception as e:
            self.handle_add_click_error(e)

    def add_find_image(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename()
        if path: self.steps.append({"action": "find_click", "image": path}); self.update_listbox()

    def remove_step(self):
        sel = self.step_listbox.curselection()
        if sel: del self.steps[sel[0]]; self.update_listbox()

    def show_guide(self):
        guide_text = (
            "HƯỚNG DẪN SỬ DỤNG TOOL AUTO\n\n"
            "1. Tạo hoặc mở kịch bản\n"
            "- Bấm nút + để tạo kịch bản mới.\n"
            "- Chọn file .json ở danh sách phía trên để mở kịch bản đã lưu.\n"
            "- Bấm nút lưu để lưu kịch bản hiện tại.\n\n"
            "2. Thêm step automation\n"
            "- Tọa độ: Sau 3 giây sẽ lấy vị trí chuột hiện tại và copy dạng x,y vào clipboard.\n"
            "- Delay: Thêm thời gian chờ giữa các bước.\n"
            "- Click: Sau 3 giây sẽ lấy vị trí chuột hiện tại và thêm step click vào kịch bản.\n"
            "- Tìm Ảnh: Chọn một ảnh mẫu để app tìm ảnh đó trên màn hình rồi click.\n"
            "- Xóa: Xóa step đang chọn trong danh sách.\n\n"
            "3. Chạy automation\n"
            "- Bấm BẮT ĐẦU.\n"
            "- Nhập số lần loop muốn chạy.\n"
            "- Theo dõi trạng thái ở dòng 'Trạng thái automation'.\n\n"
            "4. Lưu ý khi sử dụng\n"
            "- Trên macOS cần cấp quyền Accessibility cho Terminal hoặc app Python.\n"
            "- Khi lấy tọa độ hoặc thêm click, hãy đưa chuột tới đúng vị trí trong 3 giây.\n"
            "- Nếu dùng Tìm Ảnh, nên chụp ảnh mẫu rõ và đúng tỷ lệ màn hình đang dùng."
        )
        messagebox.showinfo("Hướng dẫn sử dụng", guide_text)

    def start_macro(self):
        if self.pending_capture:
            return
        if not self.steps:
            messagebox.showwarning("Chưa có step", "Hãy thêm ít nhất 1 step trước khi chạy.")
            return

        loop_count = simpledialog.askinteger("Số lần lặp", "Nhập số lần loop:", minvalue=1)
        if not loop_count:
            return

        self.run_btn.config(text="RUNNING...", state=tk.DISABLED)
        self.set_run_status(f"Trạng thái automation: Đang chạy 0/{loop_count} vòng", "#d17b00")
        threading.Thread(target=self.execute, args=(loop_count,), daemon=True).start()

    def execute(self, loop_count):
        total_steps = len(self.steps)
        try:
            for loop_index in range(loop_count):
                self.root.after(
                    0,
                    lambda current=loop_index + 1: self.set_run_status(
                        f"Trạng thái automation: Đang chạy vòng {current}/{loop_count}",
                        "#d17b00"
                    )
                )
                for step_index, step in enumerate(self.steps, start=1):
                    self.root.after(
                        0,
                        lambda current_loop=loop_index + 1, current_step=step_index, action=step["action"].upper(): self.set_run_status(
                            f"Trạng thái automation: Vòng {current_loop}/{loop_count} | Bước {current_step}/{total_steps} | {action}",
                            "#d17b00"
                        )
                    )
                    if step['action'] == 'delay':
                        time.sleep(step['value'])
                    elif step['action'] == 'click':
                        pyautogui.click(step['x'], step['y'], duration=0.2)
                    elif step['action'] == 'find_click':
                        try:
                            loc = pyautogui.locateOnScreen(step['image'], confidence=0.8)
                            if loc:
                                p = pyautogui.center(loc)
                                pyautogui.click(p.x / 2, p.y / 2, duration=0.2)
                        except Exception:
                            pass
            self.root.after(0, self.finish_macro_success)
        except Exception as e:
            self.root.after(0, lambda: self.finish_macro_error(e))

    def finish_macro_success(self):
        self.run_btn.config(text="🚀 BẮT ĐẦU", state=tk.NORMAL)
        self.set_run_status("Trạng thái automation: Hoàn thành", "green")

    def finish_macro_error(self, error):
        self.run_btn.config(text="🚀 BẮT ĐẦU", state=tk.NORMAL)
        self.set_run_status(f"Trạng thái automation: Lỗi - {error}", "red")
        messagebox.showerror("Lỗi automation", str(error))

if __name__ == "__main__":
    root = tk.Tk()
    app = MUAutoApp(root)
    root.mainloop()
