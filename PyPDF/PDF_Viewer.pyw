import customtkinter as ctk
from tkinter import filedialog
from PIL import Image, ImageTk, ImageDraw
import fitz, os, threading, time
from customtkinter import *
from CTkScrollableDropdown import *
import customtkinter as ct
from ctypes import windll


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

image_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "images")
openfile_icon = ctk.CTkImage(Image.open(os.path.join(image_path, "pdf.png")), size=(30, 30))
pdf_icon = ctk.CTkImage(Image.open(os.path.join(image_path, "file.png")), size=(35, 30))
go_to_icon = ctk.CTkImage(Image.open(os.path.join(image_path, "go-to-top.png")), size=(30, 30))
left_icon = ctk.CTkImage(Image.open(os.path.join(image_path, "left.png")), size=(30, 30))
right_icon = ctk.CTkImage(Image.open(os.path.join(image_path, "right.png")), size=(30, 30))

# programmatic plus icon (white plus on transparent)
_plus_img = Image.new("RGBA", (30, 30), (0, 0, 0, 0))
_draw = ImageDraw.Draw(_plus_img)
_draw.rectangle([13, 5, 17, 25], fill=(255, 255, 255, 255))
_draw.rectangle([5, 13, 25, 17], fill=(255, 255, 255, 255))
plus_icon = ctk.CTkImage(_plus_img, size=(28, 28))

# programmatic minus icon (white minus on transparent)
_minus_img = Image.new("RGBA", (30, 30), (0, 0, 0, 0))
_draw2 = ImageDraw.Draw(_minus_img)
_draw2.rectangle([5, 13, 25, 17], fill=(255, 255, 255, 255))
minus_icon = ctk.CTkImage(_minus_img, size=(28, 28))


class PDFViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.geometry("1100x600")
        self.root.title("PDF Viewer")
        # self.root.overrideredirect(False)
        self.doc = None
        self.page = 0
        self.zoom = 1.0
        self.max_zoom = 3.0
        self.img = None
        self.chapters = {}
        self.root.configure(bg="#2b2b2b")

        # ===== TOP BAR =====
        top = ctk.CTkFrame(root, height=45, fg_color="#222", corner_radius=5)
        top.pack(fill="x", padx=10, pady=8, ipady=2, ipadx=2)

        self.open_frame = CTkFrame(top, fg_color="transparent")
        ctk.CTkButton(self.open_frame, text="", command=self.open_pdf, image=openfile_icon, width=0, height=0, fg_color="transparent", compound=TOP, hover_color="#333", corner_radius=4).pack(side="left", padx=0, ipadx=5)
        ctk.CTkButton(self.open_frame, text="", command=self.load_chapters, image=pdf_icon, width=0, height=0, fg_color="transparent", compound=TOP, hover_color="#333", corner_radius=4).pack(side="right", ipadx=5)
        self.open_frame.pack(side="left", padx=10, fill=X, expand=True, pady=2)
        self.title = ctk.CTkLabel(self.open_frame, text="file.pdf", font=("Segoe UI", 20, "bold"))
        self.title.pack(side="left", padx=15)


        # right-side nav frame (contains page label, prev/next and zoom-full / normal buttons)
        self.nav_frame = ctk.CTkFrame(top, fg_color="transparent")
        self.nav_frame.pack(side="right", padx=10)

        self.page_label = ctk.CTkLabel(self.nav_frame, text="0 / 0", font=("Segoe UI", 14, "bold"))
        self.page_label.pack(side="left", padx=(0, 8))

        ctk.CTkButton(self.nav_frame, text="", width=10, image=left_icon, command=self.prev_page, fg_color="transparent", hover_color="#333").pack(side="left")
        ctk.CTkButton(self.nav_frame, text="", width=10, image=right_icon, command=self.next_page, fg_color="transparent", hover_color="#333").pack(side="left", padx=2)


        # Zoom-full button (plus icon) and normal-view (minus icon) on the top-right corner
        ctk.CTkButton(self.nav_frame, text="", image=plus_icon, width=40, height=40, fg_color="transparent",
                      hover_color="#333", corner_radius=6, command=self.zoom_full).pack(side="left", padx=(10, 0))
        ctk.CTkButton(self.nav_frame, text="", image=minus_icon, width=40, height=40, fg_color="transparent",
                      hover_color="#333", corner_radius=6, command=self.zoom_normal).pack(side="left", padx=(6, 0))
        ctk.CTkButton(
                self.nav_frame,
                text="",
                width=55,
                image=go_to_icon,
                command=self.goto_popup, fg_color="#222", hover_color="#333"
            ).pack(side="right", padx=6)

        # ===== CHAPTER DROPDOWN =====
        self.chapter_menu = ctk.CTkButton(
            top, text="Chapters",
            width=300, height=37, font=("Segoe UI", 17), anchor="w",
        )
        self.chapter_menu.pack(side="right", padx=10)

        self.dropdown = CTkScrollableDropdown(self.chapter_menu, justify="left", font=("Segoe UI", 26), command=self.jump_chapter)

        frame = ctk.CTkFrame(root, fg_color="transparent")
        frame.pack(fill="both", expand=True)

        # self.canvas = ctk.CTkCanvas(frame, bg="#2b2b2b")
        self.canvas = ctk.CTkCanvas(frame, bg="#2b2b2b", borderwidth=0, highlightthickness=0)
        # self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.pack(side="left", fill="both", expand=True, padx=10)

        scrollbar = ctk.CTkScrollbar(frame, command=self.canvas.yview)
        scrollbar.pack(side="right", fill="y")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.bind_all("<MouseWheel>", self.on_scroll)

    def goto_popup(self):   # ← SAME TAB LEVEL AS def __init__
        if not self.doc:
            return
        pop = ctk.CTkToplevel(self.root)
        pop.title("Go To Page")
        pop.geometry("240x130")
        pop.grab_set()

        entry = ctk.CTkEntry(pop)
        entry.pack(pady=20)
        entry.focus()

        def go():
            try:
                p = int(entry.get())
                if 1 <= p <= len(self.doc):
                    self.page = p - 1
                    self.zoom = 1.0
                    self.render()
                    pop.destroy()
            except:
                pass


        btns = ctk.CTkFrame(pop, fg_color="transparent")
        btns.pack(pady=7)

        ctk.CTkButton(btns, text="OK", width=80, command=go).pack(side="left", padx=5)
        ctk.CTkButton(btns, text="Cancel", width=80, command=pop.destroy).pack(side="left", padx=5)

    # ---------- FILES ----------
    def open_pdf(self):
        path = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        if not path:
            return

        self.doc = fitz.open(path)
        self.page = 0
        self.zoom = 1.0
        self.title.configure(text=os.path.basename(path))
        self.render()

    def load_chapters(self):
        path = filedialog.askopenfilename(filetypes=[("Chapter file", "*.chapters")])
        if not path:
            return

        self.chapters.clear()
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line:
                    name, page = line.strip().split("=")
                    try:
                        self.chapters[name] = int(page)
                    except ValueError:
                        continue

        values = list(self.chapters.keys()) or ["No chapters"]

        # self.chapter_menu.configure(values=values)
        self.dropdown.configure(values=values, font=("Segoe UI", 18))
        # self.chapter_menu.set("Select chapter")
        # self.root.update_idletasks()

    # ---------- RENDER ----------
    def render(self):
        if not self.doc:
            return

        page = self.doc.load_page(self.page)
        pix = page.get_pixmap(matrix=fitz.Matrix(self.zoom, self.zoom))
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        self.img = ImageTk.PhotoImage(img)

        self.canvas.delete("all")
        self.canvas.create_image(
            self.canvas.winfo_width() // 2,
            20,
            image=self.img,
            anchor="n"
        )

        self.canvas.configure(scrollregion=(0, 0, pix.width, pix.height + 20))
        self.canvas.yview_moveto(0)

        self.page_label.configure(text=f"{self.page+1} / {len(self.doc)}")

    # ---------- NAV ----------
    def next_page(self):
        if self.doc and self.page < len(self.doc) - 1:
            self.page += 1
            self.render()

    def prev_page(self):
        if self.doc and self.page > 0:
            self.page -= 1
            self.render()

    def jump_chapter(self, name):
        self.root.update()
        if name in self.chapters:
            self.page = self.chapters[name] - 1
            self.zoom = 1.0
            self.canvas.yview_moveto(0)
            self.render()
            self.chapter_menu.configure(text=name)

    # ---------- SCROLL / ZOOM ----------
    def on_scroll(self, e):
        # CTRL + mouse wheel to zoom
        try:
            ctrl_pressed = (e.state & 0x0004) != 0
        except Exception:
            ctrl_pressed = False
        if ctrl_pressed:  # CTRL
            self.zoom += 0.1 if e.delta > 0 else -0.1
            self.zoom = max(0.5, min(self.max_zoom, self.zoom))
            self.render()
        else:
            # normal scroll
            self.canvas.yview_scroll(-1 if e.delta > 0 else 1, "units")

    def zoom_full(self):
        # set to maximum zoom and show top of page
        if not self.doc:
            return
        self.zoom = self.max_zoom
        self.canvas.yview_moveto(0)
        self.render()

    def zoom_normal(self):
        # reset to normal zoom and show top of page
        if not self.doc:
            return
        self.zoom = 1.0
        self.canvas.yview_moveto(0)
        self.render()

loading_icon = ctk.CTkImage(Image.open(os.path.join(image_path, "pdf.png")), size=(150, 150))

class SplashScreen:
    def __init__(self, root):
        self.root = root
        self.root.title("Splash Screen")
        self.root.geometry("550x300")
        self.root.overrideredirect(True)

        image_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "images")
        logo_image = ct.CTkImage(Image.open(os.path.join(image_path, "pdf.png")), size=(130, 130))

        self.logoframe = ct.CTkFrame(self.root, fg_color="transparent", height=0, width=0)

        ct.CTkLabel(self.logoframe, text="", image=logo_image, compound='top', font=("Poppins", 30, "bold"), text_color="white").pack(padx=10, anchor="center")
        ct.CTkLabel(self.logoframe, text=" Pdf Workspaces", font=("Poppins", 30, "bold"), text_color="white").pack(padx=10, pady=10, anchor="center")


        self.logoframe.pack(side='top', fill='x', pady=75)

        self.text = ct.CTkLabel(self.root, text="Please wait...The First launch of the app may take longer...", font=("IBM Plex Sans", 15))
        self.progressbar = ct.CTkProgressBar(self.root, orientation='horizontal', width=300, mode='determinate', determinate_speed=0.35, fg_color="white", height=8, progress_color="#EA454A", corner_radius=0)

        self.get_started()
        self.set_appwindow(self.root)
        self.center_window(self.root)

    def get_started(self):
        self.progressbar.pack(side='bottom', fill='x')
        self.text.pack(side='bottom', anchor='center')
        self.thread = threading.Thread(target=self.loading)
        self.thread.start()
        self.progressbar.set(0)
        self.progressbar.start()

    def loading(self):
        time.sleep(4)  # Simulate loading time
        self.text.configure(text="")
        self.text.configure(text="Please wait.....The First launch of the app may take longer...")
        self.progressbar.stop()
        self.progressbar.set(100)

        self.root.after(0, self.close_splash_and_open_new)

    def close_splash_and_open_new(self):
        self.root.destroy()
        self.open_new_window()

    def open_new_window(self):
        win = ct.CTk()
        win.geometry("1000x600")
        PDFViewerApp(win)
        win.mainloop()

    def center_window(self, win):
        win.update_idletasks()
        width = win.winfo_width()
        height = win.winfo_height()
        x = (win.winfo_screenwidth() // 2) - (width // 2)
        y = (win.winfo_screenheight() // 2) - (height // 2)
        win.geometry('{}x{}+{}+{}'.format(width, height, x, y))

    def set_appwindow(self, mainWindow): 
        GWL_EXSTYLE = -20
        WS_EX_APPWINDOW = 0x00040000
        WS_EX_TOOLWINDOW = 0x00000080
        hwnd = windll.user32.GetParent(mainWindow.winfo_id())
        stylew = windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        stylew = stylew & ~WS_EX_TOOLWINDOW
        stylew = stylew | WS_EX_APPWINDOW
        windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, stylew)   
        mainWindow.wm_withdraw()
        mainWindow.after(10, lambda: mainWindow.wm_deiconify())

# ===== RUN =====
if __name__ == "__main__":
    root = ctk.CTk()
    SplashScreen(root)
    # PDFViewerApp(root)
    root.mainloop()
