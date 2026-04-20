import tkinter as tk
from tkinter import simpledialog, messagebox
import pyautogui
import time
import threading
import json
import os
import glob
import queue
import pyperclip
from datetime import datetime, timedelta

class MUAutoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Auto Click Loop")
        self.root.geometry("500x760")
        self.steps = []
        self.current_file = None
        self.pending_capture = None
        self.automation_running = False
        self.ui_queue = queue.Queue()
        self.selected_file = None
        self.schedule_enabled = tk.BooleanVar(value=False)
        default_schedule = self.get_next_hour_slot()
        self.schedule_date_var = tk.StringVar(value=default_schedule.strftime("%Y-%m-%d"))
        self.schedule_time_var = tk.StringVar(value=default_schedule.strftime("%H:%M:%S"))
        self.countdown_var = tk.StringVar(value="Countdown: chưa bật hẹn giờ")

        # --- SET APP ICON Ở ĐÂY ---
        try:
            icon_path = "logo-app.png" if os.path.exists("logo-app.png") else "logo.png"
            app_icon = tk.PhotoImage(file=icon_path)
            self.root.iconphoto(True, app_icon)
        except Exception as e:
            print(f"Lỗi load app icon: {e}")

        self.main_frame = tk.Frame(self.root, padx=10, pady=10)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.top_frame = tk.Frame(self.main_frame)
        self.top_frame.pack(fill=tk.BOTH, expand=True)
        self.top_frame.grid_columnconfigure(0, weight=1, uniform="top")
        self.top_frame.grid_columnconfigure(1, weight=1, uniform="top")
        self.top_frame.grid_rowconfigure(0, weight=1)

        self.files_panel = tk.Frame(self.top_frame, bg="#f0f0f0", padx=8, pady=8, relief=tk.GROOVE, bd=1)
        self.files_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        self.files_panel.grid_rowconfigure(2, weight=1)
        self.files_panel.grid_columnconfigure(0, weight=1)

        self.script_panel = tk.Frame(self.top_frame, padx=8, pady=8, relief=tk.GROOVE, bd=1)
        self.script_panel.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        self.script_panel.grid_rowconfigure(2, weight=1)
        self.script_panel.grid_columnconfigure(0, weight=1)

        self.toolbar = tk.Frame(self.files_panel, bg="#f0f0f0")
        self.toolbar.grid(row=0, column=0, sticky="ew")

        tk.Button(self.toolbar, text="➕", font=("Arial", 14), command=self.new_script, relief=tk.FLAT, bg="#e0e0e0").pack(side=tk.LEFT, padx=2)
        tk.Button(self.toolbar, text="💾", font=("Arial", 14), command=self.save_script, relief=tk.FLAT, bg="#e0e0e0").pack(side=tk.LEFT, padx=2)

        tk.Label(self.files_panel, text="Kịch bản hiện có", bg="#f0f0f0", font=("Arial", 12, "bold")).grid(row=1, column=0, sticky="w", pady=(10, 6))
        self.file_listbox = tk.Listbox(self.files_panel, font=("Arial", 11), bg="white", selectmode=tk.SINGLE)
        self.file_listbox.grid(row=2, column=0, sticky="nsew")
        self.file_listbox.bind('<<ListboxSelect>>', self.on_file_select)

        self.lbl_status = tk.Label(self.script_panel, text="Kịch bản mới", font=("Arial", 12, "bold"), fg="blue")
        self.lbl_status.grid(row=0, column=0, sticky="w")
        self.lbl_run_status = tk.Label(self.script_panel, text="Trạng thái automation: Chưa chạy", font=("Arial", 10), fg="#555555")
        self.lbl_run_status.grid(row=1, column=0, sticky="w", pady=(2, 6))

        self.step_listbox = tk.Listbox(self.script_panel, font=("Arial", 12))
        self.step_listbox.grid(row=2, column=0, sticky="nsew")

        self.bottom_frame = tk.Frame(self.main_frame, padx=2, pady=10)
        self.bottom_frame.pack(fill=tk.X)

        # --- VÙNG NÚT CHỨC NĂNG ---
        self.control_frame = tk.Frame(self.bottom_frame)
        self.control_frame.pack(fill=tk.X, pady=(0, 8))

        # Danh sách cấu hình các nút
        btn_configs = [
            ("📍 Lấy Tọa độ", self.get_mouse_pos, "black"),
            ("⏱ Delay", self.add_delay, "black"),
            ("🖱 Click", self.add_click, "black"),
            ("📋 Dán MSG", self.add_paste_message, "black"),
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

        self.message_frame = tk.LabelFrame(self.bottom_frame, text="Tin nhắn cần dán", padx=8, pady=8)
        self.message_frame.pack(fill=tk.X, pady=(0, 8))
        self.message_input = tk.Text(self.message_frame, height=5, font=("Arial", 11))
        self.message_input.pack(fill=tk.X)

        self.schedule_frame = tk.LabelFrame(self.bottom_frame, text="Lịch chạy", padx=8, pady=8)
        self.schedule_frame.pack(fill=tk.X, pady=(0, 8))
        self.schedule_toggle = tk.Checkbutton(
            self.schedule_frame,
            text="Auto theo giờ",
            variable=self.schedule_enabled,
            command=self.on_schedule_toggle
        )
        self.schedule_toggle.grid(row=0, column=0, sticky="w")
        tk.Label(self.schedule_frame, text="Ngày").grid(row=1, column=0, sticky="w", pady=(8, 4))
        tk.Entry(self.schedule_frame, textvariable=self.schedule_date_var, width=16).grid(row=1, column=1, sticky="w", padx=(8, 0))
        tk.Label(self.schedule_frame, text="Giờ").grid(row=1, column=2, sticky="w", padx=(16, 0), pady=(8, 4))
        tk.Entry(self.schedule_frame, textvariable=self.schedule_time_var, width=12).grid(row=1, column=3, sticky="w", padx=(8, 0))
        self.schedule_hint = tk.Label(self.schedule_frame, text="Bỏ chọn để bấm BẮT ĐẦU chạy ngay.", fg="#555555")
        self.schedule_hint.grid(row=2, column=0, columnspan=4, sticky="w", pady=(8, 0))
        self.countdown_label = tk.Label(self.schedule_frame, textvariable=self.countdown_var, fg="#0057b8", font=("Arial", 10, "bold"))
        self.countdown_label.grid(row=3, column=0, columnspan=4, sticky="w", pady=(6, 0))

        # --- Nút Chạy ---
        self.run_btn = tk.Button(self.bottom_frame, text="🚀 BẮT ĐẦU", bg="#28a745", font=("Arial", 14, "bold"), command=self.start_macro)
        self.run_btn.pack(fill=tk.X, pady=10)

        self.refresh_file_list()
        self.on_schedule_toggle()

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
        if self.selected_file:
            matches = [index for index, name in enumerate(self.file_listbox.get(0, tk.END)) if name == self.selected_file]
            if matches:
                self.file_listbox.selection_set(matches[0])

    def on_file_select(self, event):
        sel = self.file_listbox.curselection()
        if sel:
            self.selected_file = self.file_listbox.get(sel[0])
            self.load_script(self.selected_file)

    def new_script(self):
        has_unsaved_content = bool(
            self.steps or
            self.message_input.get("1.0", tk.END).strip() or
            self.schedule_enabled.get()
        )
        if has_unsaved_content and messagebox.askyesno("Xác nhận", "Tạo kịch bản mới? (Chưa lưu sẽ mất)"):
            self.steps = []
            self.current_file = None
            self.selected_file = None
            self.message_input.delete("1.0", tk.END)
            self.schedule_enabled.set(False)
            now = datetime.now()
            self.schedule_date_var.set(now.strftime("%Y-%m-%d"))
            self.schedule_time_var.set(now.strftime("%H:%M:%S"))
            self.file_listbox.selection_clear(0, tk.END)
            self.lbl_status.config(text="Kịch bản mới", fg="blue")
            self.update_listbox()
            self.on_schedule_toggle()

    def save_script(self):
        if not self.steps and not self.message_input.get("1.0", tk.END).strip() and not self.schedule_enabled.get():
            return
        if not self.current_file:
            name = simpledialog.askstring("Lưu", "Nhập tên kịch bản (không cần .json):")
            if not name: return
            self.current_file = f"{name}.json"
        payload = {
            "steps": self.steps,
            "message": self.message_input.get("1.0", tk.END).rstrip("\n"),
            "schedule_enabled": self.schedule_enabled.get(),
            "scheduled_at": self.get_schedule_text(),
        }
        with open(self.current_file, 'w', encoding='utf-8') as f:
            json.dump(payload, f, indent=4, ensure_ascii=False)
        self.selected_file = self.current_file
        self.lbl_status.config(text=f"Đang mở: {self.current_file}", fg="green")
        self.refresh_file_list()

    def load_script(self, filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                payload = json.load(f)
            if isinstance(payload, list):
                self.steps = payload
                message = ""
                schedule_enabled = False
                scheduled_at = ""
            else:
                self.steps = payload.get("steps", [])
                message = payload.get("message", "")
                schedule_enabled = payload.get("schedule_enabled", False)
                scheduled_at = payload.get("scheduled_at", "")
            self.current_file = filename
            self.selected_file = filename
            self.message_input.delete("1.0", tk.END)
            self.message_input.insert("1.0", message)
            self.schedule_enabled.set(schedule_enabled)
            if scheduled_at:
                self.set_schedule_text(scheduled_at)
            self.lbl_status.config(text=f"Đang mở: {filename}", fg="green")
            self.update_listbox()
            self.on_schedule_toggle()
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
            elif step["action"] == "paste_message":
                label = f"{i+1}. PASTE_MESSAGE"
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

    def add_paste_message(self):
        self.steps.append({"action": "paste_message"})
        self.update_listbox()

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
        self.reset_countdown()
        if self.current_file:
            self.lbl_status.config(text=f"Đang mở: {self.current_file}", fg="green")
        else:
            self.lbl_status.config(text="Kịch bản mới", fg="blue")

    def set_run_status(self, text, color="#555555"):
        self.lbl_run_status.config(text=text, fg=color)

    def on_schedule_toggle(self):
        state = tk.NORMAL if self.schedule_enabled.get() else tk.DISABLED
        for child in self.schedule_frame.grid_slaves(row=1):
            child.configure(state=state)
        if self.schedule_enabled.get():
            next_slot = self.get_next_hour_slot()
            self.schedule_date_var.set(next_slot.strftime("%Y-%m-%d"))
            self.schedule_time_var.set(next_slot.strftime("%H:%M:%S"))
        hint = "Đã bật auto theo giờ. App sẽ đợi tới thời điểm cấu hình rồi mới chạy." if self.schedule_enabled.get() else "Bỏ chọn để bấm BẮT ĐẦU chạy ngay."
        self.schedule_hint.config(text=hint)
        self.reset_countdown()

    def get_schedule_text(self):
        return f"{self.schedule_date_var.get().strip()} {self.schedule_time_var.get().strip()}".strip()

    def set_schedule_text(self, schedule_text):
        try:
            dt = datetime.strptime(schedule_text, "%Y-%m-%d %H:%M:%S")
            self.schedule_date_var.set(dt.strftime("%Y-%m-%d"))
            self.schedule_time_var.set(dt.strftime("%H:%M:%S"))
        except ValueError:
            pass

    def get_scheduled_datetime(self):
        return datetime.strptime(self.get_schedule_text(), "%Y-%m-%d %H:%M:%S")

    def get_next_hour_slot(self):
        now = datetime.now()
        next_hour = now.replace(minute=0, second=0, microsecond=0)
        if now.minute != 0 or now.second != 0 or now.microsecond != 0:
            next_hour = next_hour + timedelta(hours=1)
        return next_hour

    def reset_countdown(self):
        if self.schedule_enabled.get():
            self.countdown_var.set("Countdown: sẵn sàng chờ lịch chạy")
        else:
            self.countdown_var.set("Countdown: chưa bật hẹn giờ")

    def set_countdown(self, seconds, scheduled_at=None):
        if scheduled_at:
            self.countdown_var.set(
                f"Countdown: còn {seconds} giây, sẽ chạy lúc {scheduled_at.strftime('%Y-%m-%d %H:%M:%S')}"
            )
        else:
            self.countdown_var.set(f"Countdown: còn {seconds} giây")

    def perform_paste_message(self, message):
        pyperclip.copy(message)
        modifier = "command" if self.root.tk.call("tk", "windowingsystem") == "aqua" else "ctrl"
        pyautogui.hotkey(modifier, "v")

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
            "1. Quản lý kịch bản\n"
            "- Cột trái là danh sách Kịch bản hiện có.\n"
            "- Cột phải là nội dung Kịch bản mới hoặc file đang mở.\n"
            "- Bấm + để tạo kịch bản mới.\n"
            "- Bấm biểu tượng lưu để lưu toàn bộ step, tin nhắn cần dán và cấu hình lịch chạy vào file .json.\n\n"
            "2. Thêm step automation\n"
            "- Tọa độ: Sau 3 giây lấy vị trí chuột hiện tại và copy dạng x,y vào clipboard.\n"
            "- Delay: Thêm thời gian chờ giữa các bước.\n"
            "- Click: Sau 3 giây lấy vị trí chuột hiện tại và thêm step click.\n"
            "- Dán MSG: Lấy nội dung ở ô Tin nhắn cần dán, copy vào clipboard rồi bấm Command/Ctrl + V tại vị trí con trỏ hiện tại.\n"
            "- Tìm Ảnh: Chọn một ảnh mẫu để app tìm trên màn hình rồi click.\n"
            "- Xóa: Xóa step đang chọn trong danh sách kịch bản.\n\n"
            "3. Tin nhắn cần dán\n"
            "- Nhập nội dung muốn dán vào ô Tin nhắn cần dán.\n"
            "- Khi step Dán MSG chạy, app sẽ dùng chính nội dung này để paste.\n"
            "- Nội dung tin nhắn cũng được lưu cùng file kịch bản.\n\n"
            "4. Lịch chạy và countdown\n"
            "- Bỏ chọn Auto theo giờ nếu muốn bấm BẮT ĐẦU là chạy ngay.\n"
            "- Khi bật Auto theo giờ, app tự điền ngày hiện tại và mốc đầu giờ kế tiếp, ví dụ 13:35 sẽ thành 14:00:00.\n"
            "- Có thể chỉnh lại ngày và giờ nếu muốn.\n"
            "- Sau khi bấm BẮT ĐẦU, app sẽ countdown số giây còn lại trước khi bắt đầu chạy.\n"
            "- Countdown và trạng thái chạy được hiển thị ngay dưới phần lịch chạy và ở dòng trạng thái automation.\n\n"
            "5. Chạy automation\n"
            "- Bấm BẮT ĐẦU.\n"
            "- Nhập số lần loop muốn chạy.\n"
            "- App sẽ chạy ngay hoặc chờ đến lịch đã cấu hình rồi mới thực hiện các step.\n\n"
            "6. Lưu ý khi sử dụng\n"
            "- Trên macOS cần cấp quyền Accessibility cho Terminal hoặc app Python.\n"
            "- Khi lấy tọa độ hoặc thêm click, hãy đưa chuột tới đúng vị trí trong 3 giây.\n"
            "- Nếu dùng Tìm Ảnh, nên chụp ảnh mẫu rõ và đúng tỷ lệ màn hình đang dùng."
        )
        guide_window = tk.Toplevel(self.root)
        guide_window.title("Hướng dẫn sử dụng")
        guide_window.transient(self.root)
        guide_window.grab_set()

        root_width = self.root.winfo_width() or 500
        root_height = self.root.winfo_height() or 760
        guide_width = max(420, int(root_width * 0.9))
        guide_height = max(320, int(root_height * (2 / 3)))

        root_x = self.root.winfo_rootx()
        root_y = self.root.winfo_rooty()
        pos_x = root_x + max(20, (root_width - guide_width) // 2)
        pos_y = root_y + max(20, (root_height - guide_height) // 2)
        guide_window.geometry(f"{guide_width}x{guide_height}+{pos_x}+{pos_y}")

        container = tk.Frame(guide_window, padx=10, pady=10)
        container.pack(fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        guide_textbox = tk.Text(
            container,
            wrap=tk.WORD,
            yscrollcommand=scrollbar.set,
            font=("Arial", 11),
            padx=8,
            pady=8
        )
        guide_textbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=guide_textbox.yview)

        guide_textbox.insert("1.0", guide_text)
        guide_textbox.config(state=tk.DISABLED)

        close_btn = tk.Button(guide_window, text="Đóng", command=guide_window.destroy)
        close_btn.pack(pady=(0, 10))

    def start_macro(self):
        if self.pending_capture:
            return
        if not self.steps:
            messagebox.showwarning("Chưa có step", "Hãy thêm ít nhất 1 step trước khi chạy.")
            return

        loop_count = simpledialog.askinteger("Số lần lặp", "Nhập số lần loop:", minvalue=1)
        if not loop_count:
            return

        scheduled_at = None
        if self.schedule_enabled.get():
            try:
                scheduled_at = self.get_scheduled_datetime()
            except ValueError:
                messagebox.showerror("Sai định dạng thời gian", "Vui lòng nhập đúng định dạng YYYY-MM-DD và HH:MM:SS.")
                return
            if scheduled_at <= datetime.now():
                messagebox.showerror("Thời gian không hợp lệ", "Thời gian hẹn phải lớn hơn thời gian hiện tại.")
                return

        self.run_btn.config(text="RUNNING...", state=tk.DISABLED)
        if scheduled_at:
            self.set_run_status(f"Trạng thái automation: Đang chờ tới {scheduled_at.strftime('%Y-%m-%d %H:%M:%S')}", "#0057b8")
        else:
            self.set_run_status(f"Trạng thái automation: Đang chạy 0/{loop_count} vòng", "#d17b00")
        self.automation_running = True
        message_text = self.message_input.get("1.0", tk.END).rstrip("\n")
        threading.Thread(
            target=self.execute,
            args=(loop_count, list(self.steps), scheduled_at, message_text),
            daemon=True
        ).start()
        self.process_ui_queue()

    def queue_run_status(self, text, color="#555555"):
        self.ui_queue.put(("status", text, color))

    def queue_countdown(self, seconds, scheduled_at=None):
        self.ui_queue.put(("countdown", seconds, scheduled_at))

    def queue_finish(self, success, error=None):
        self.ui_queue.put(("finish", success, error))

    def process_ui_queue(self):
        try:
            while True:
                event = self.ui_queue.get_nowait()
                if event[0] == "status":
                    _, text, color = event
                    self.set_run_status(text, color)
                elif event[0] == "countdown":
                    _, seconds, scheduled_at = event
                    self.set_countdown(seconds, scheduled_at)
                elif event[0] == "finish":
                    _, success, error = event
                    if success:
                        self.finish_macro_success()
                    else:
                        self.finish_macro_error(error)
        except queue.Empty:
            pass

        if self.automation_running or not self.ui_queue.empty():
            self.root.after(100, self.process_ui_queue)

    def execute(self, loop_count, steps, scheduled_at=None, message_text=""):
        total_steps = len(steps)
        try:
            if scheduled_at:
                while True:
                    remaining = (scheduled_at - datetime.now()).total_seconds()
                    if remaining <= 0:
                        break
                    self.queue_countdown(int(remaining), scheduled_at)
                    self.queue_run_status(
                        f"Trạng thái automation: Chờ chạy sau {int(remaining)} giây lúc {scheduled_at.strftime('%Y-%m-%d %H:%M:%S')}",
                        "#0057b8"
                    )
                    time.sleep(min(1, remaining))
            self.queue_countdown(0, scheduled_at)
            for loop_index in range(loop_count):
                self.queue_run_status(
                    f"Trạng thái automation: Đang chạy vòng {loop_index + 1}/{loop_count}",
                    "#d17b00"
                )
                for step_index, step in enumerate(steps, start=1):
                    self.queue_run_status(
                        f"Trạng thái automation: Vòng {loop_index + 1}/{loop_count} | Bước {step_index}/{total_steps} | {step['action'].upper()}",
                        "#d17b00"
                    )
                    if step['action'] == 'delay':
                        time.sleep(step['value'])
                    elif step['action'] == 'click':
                        pyautogui.click(step['x'], step['y'], duration=0.2)
                    elif step['action'] == 'paste_message':
                        self.perform_paste_message(message_text)
                    elif step['action'] == 'find_click':
                        try:
                            loc = pyautogui.locateOnScreen(step['image'], confidence=0.8)
                            if loc:
                                p = pyautogui.center(loc)
                                pyautogui.click(p.x / 2, p.y / 2, duration=0.2)
                        except Exception:
                            pass
            self.queue_finish(True)
        except Exception as e:
            self.queue_finish(False, e)

    def finish_macro_success(self):
        self.automation_running = False
        self.run_btn.config(text="🚀 BẮT ĐẦU", state=tk.NORMAL)
        self.set_run_status("Trạng thái automation: Hoàn thành", "green")
        self.countdown_var.set("Countdown: đã hoàn thành")

    def finish_macro_error(self, error):
        self.automation_running = False
        self.run_btn.config(text="🚀 BẮT ĐẦU", state=tk.NORMAL)
        self.set_run_status(f"Trạng thái automation: Lỗi - {error}", "red")
        self.countdown_var.set("Countdown: dừng do lỗi")
        messagebox.showerror("Lỗi automation", str(error))

if __name__ == "__main__":
    root = tk.Tk()
    app = MUAutoApp(root)
    root.mainloop()
