#app doesnt remove itself from task manager when its closed?!

import os
import cv2
import numpy as np
import pyautogui
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk


# Hide the console window
if os.name == 'nt':
    import ctypes
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

import sys
import traceback

notes_list = []
app_started = False
auto_refresh_enabled = False
roi_selected = False
roi = None

#####################################

class TransparentWindow(tk.Toplevel):
    def __init__(self, master=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.3)
        self.overrideredirect(True)
        self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}+0+0")
        self.canvas = tk.Canvas(self, bg="white", width=self.winfo_screenwidth(), height=self.winfo_screenheight())
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_move)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)

        self.start_x = None
        self.start_y = None
        self.end_x = None
        self.end_y = None

    def on_mouse_down(self, event):
        self.start_x = event.x
        self.start_y = event.y

    def on_mouse_move(self, event):
        self.end_x = event.x
        self.end_y = event.y

        self.canvas.delete("rectangle")
        self.canvas.create_rectangle(
            self.start_x, self.start_y, self.end_x, self.end_y, outline="red", width=3, tags="rectangle"
        )

    def on_mouse_up(self, event):
        roi_x = min(self.start_x, self.end_x)
        roi_y = min(self.start_y, self.end_y)
        roi_w = abs(self.end_x - self.start_x)
        roi_h = abs(self.end_y - self.start_y)

        roi_entry.delete(0, tk.END)
        roi_entry.insert(0, f"{roi_x},{roi_y},{roi_w},{roi_h}")

        self.destroy()
        start_app()

#####################################

# Hide the console window
ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

def excepthook(exc_type, exc_value, exc_traceback):
    # Show the console window
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 1)

    # Print the traceback to the console
    traceback.print_exception(exc_type, exc_value, exc_traceback)

    # Exit the program
    sys.exit()

    # Set the custom excepthook
    sys.excepthook = excepthook


def select_roi():
    TransparentWindow(root)

def update_roi():
    global roi_selected, roi
    if roi_selected:
        x, y, w, h = roi
        screen = capture_screen()
        height, width, channels = screen.shape

        if x >= 0 and y >= 0 and w > 0 and h > 0 and x + w <= width and y + h <= height:
            outlined_screen = draw_roi_rectangle(screen.copy(), x, y, w, h)
            selected_screen = screen[y:y+h, x:x+w]
            selected_screen = cv2.resize(selected_screen, (500, 500))
            hist_image = display_histogram(selected_screen)

            ax1.clear()
            ax1.imshow(cv2.cvtColor(outlined_screen, cv2.COLOR_BGR2RGB))
            ax1.set_title("Selected Region")

            ax2.clear()
            ax2.imshow(hist_image)
            ax2.set_title("Histogram")

            canvas.draw()


def load_notes():
    try:
        with open("notes.txt", "r") as notes_file:
            for line in notes_file:
                notes_list.append(line.strip())
    except FileNotFoundError:
        pass

load_notes()
app_started = False

def auto_refresh():
    global auto_refresh_enabled
    if auto_refresh_enabled:
        refresh()
        root.after(1000, auto_refresh)

def toggle_auto_refresh():
    global auto_refresh_enabled
    auto_refresh_enabled = not auto_refresh_enabled
    if auto_refresh_enabled:
        auto_refresh_button.config(text="Auto Refresh (On)")
        auto_refresh()
    else:
        auto_refresh_button.config(text="Auto Refresh (Off)")

def start_app():
    global app_started, auto_refresh_enabled
    if not app_started:
        app_started = True
        auto_refresh_enabled = True
        auto_refresh()

def stop_app():
    global app_started, auto_refresh_enabled
    if app_started:
        app_started = False
        auto_refresh_enabled = False

def capture_screen():
    screen = pyautogui.screenshot()
    return cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2BGR)

def draw_roi_rectangle(image, x, y, w, h, color=(0, 0, 255), thickness=5):
    return cv2.rectangle(image, (x, y), (x+w, y+h), color, thickness)


def notes_window():
    def close_notes_window():
        save_notes_to_file()
        notes_win.destroy()

    def save_note():
        note_text = text_box.get("1.0", tk.END).strip()
        if note_text:
            notes_list.append(note_text)
        text_box.delete("1.0", tk.END)

    def delete_notes():
        notes_list.clear()
        text_box.delete("1.0", tk.END)

    notes_win = tk.Toplevel(root)
    notes_win.title("Notes")

    text_box = tk.Text(notes_win, wrap=tk.WORD)
    text_box.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

    button_frame = tk.Frame(notes_win)
    button_frame.pack(side=tk.BOTTOM, pady=10, fill=tk.X, anchor=tk.CENTER)

    save_button = tk.Button(button_frame, text="Save Note", command=save_note)
    save_button.pack(side=tk.LEFT, padx=(0, 5))

    delete_button = tk.Button(button_frame, text="Delete All Notes", command=delete_notes)
    delete_button.pack(side=tk.RIGHT, padx=(5, 0))

    notes_win.protocol("WM_DELETE_WINDOW", close_notes_window)
    notes_win.mainloop()


def load_notes():
    try:
        with open("notes.txt", "r") as notes_file:
            for line in notes_file:
                notes_list.append(line.strip())
    except FileNotFoundError:
        pass


def save_notes_to_file():
    with open("notes.txt", "w") as notes_file:
        for note in notes_list:
            notes_file.write(note + "\n")



def show_saved_notes():
    notes_text = "\n\n".join(notes_list)
    if notes_text:
        messagebox.showinfo("Saved Notes", notes_text)
    else:
        messagebox.showinfo("Saved Notes", "No notes saved.")



def show_saved_notes_window():
    notes_text = "\n\n".join(notes_list)

    show_notes_win = tk.Toplevel(root)
    show_notes_win.title("Saved Notes")

    text_box = tk.Text(show_notes_win, wrap=tk.WORD)
    text_box.insert(tk.END, notes_text)
    text_box.config(state=tk.DISABLED)
    text_box.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

    close_button = tk.Button(show_notes_win, text="Close", command=show_notes_win.destroy)
    close_button.pack(side=tk.BOTTOM, pady=10)





def display_histogram(image):
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    hist, bins = np.histogram(gray_image.ravel(), 256, [0, 256])

    # Normalize the histogram data
    total_pixels = gray_image.size
    normalized_hist = hist / total_pixels

    fig_hist, ax_hist = plt.subplots(figsize=(5, 2))
    ax_hist.bar(range(256), normalized_hist, color='k', width=1.0)
    ax_hist.set_xlim([0, 256])
    ax_hist.set_ylim([0, np.max(normalized_hist)])
    ax_hist.set_xlabel('Luminance')
    ax_hist.set_ylabel('Normalized Strength')
    fig_hist.canvas.draw()
    hist_image = np.frombuffer(fig_hist.canvas.tostring_rgb(), dtype=np.uint8)
    hist_image = hist_image.reshape(fig_hist.canvas.get_width_height()[::-1] + (3,))
    plt.close(fig_hist)
    return hist_image



def update_roi():
    roi_coords = roi_entry.get()
    if roi_coords:
        try:
            x, y, w, h = map(int, roi_coords.split(","))
        except ValueError:
            return

        screen = capture_screen()
        height, width, channels = screen.shape

        if x >= 0 and y >= 0 and w > 0 and h > 0 and x + w <= width and y + h <= height:
            outlined_screen = draw_roi_rectangle(screen.copy(), x, y, w, h)
            selected_screen = screen[y:y+h, x:x+w]
            selected_screen = cv2.resize(selected_screen, (500, 500))
            hist_image = display_histogram(selected_screen)

            ax1.clear()
            ax1.imshow(cv2.cvtColor(outlined_screen, cv2.COLOR_BGR2RGB))
            ax1.set_title("Selected Region")

            ax2.clear()
            ax2.imshow(hist_image)
            ax2.set_title("Histogram")

            canvas.draw()


def refresh():
    update_roi()

root = tk.Tk()
root.title("Histogrammer")
root.attributes("-topmost", True)
root.configure(bg="#1a1a1a")

script_directory = os.path.dirname(os.path.realpath(__file__))
icon_file_path = os.path.join(script_directory, 'histogram.ico')
root.iconbitmap(icon_file_path)

def on_deiconify(event):
    root.attributes("-topmost", True)

def on_iconify(event):
    root.attributes("-topmost", False)

root.bind("<Unmap>", on_iconify)
root.bind("<Map>", on_deiconify)

## preview windows area
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))
fig.patch.set_facecolor("#2b2b2b")
ax1.set_facecolor("#2b2b2b")
ax2.set_facecolor("#2b2b2b")
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

# Create a frame for buttons
button_frame = tk.Frame(root, bg="#212121")
button_frame.pack(side=tk.BOTTOM, pady=10)

roi_label = tk.Label(button_frame, text="ROI (x,y,w,h):")
roi_label.pack(side=tk.LEFT)

roi_entry = tk.Entry(button_frame)
roi_entry.pack(side=tk.LEFT)
roi_entry.bind('<KeyRelease>', lambda e: update_roi())

select_roi_button = tk.Button(master=button_frame, text="Select ROI", command=select_roi, bg="blue", fg="white")
select_roi_button.pack(side=tk.RIGHT, padx=(30, 5), anchor=tk.CENTER)

refresh_button = tk.Button(master=button_frame, text="Refresh", command=refresh, bg="green", fg="white")
refresh_button.pack(side=tk.RIGHT, padx=(30, 5))

auto_refresh_button = tk.Button(master=button_frame, text="Auto Refresh (Off)", command=toggle_auto_refresh, bg="yellow")
auto_refresh_button.pack(side=tk.RIGHT)

start_button = tk.Button(master=button_frame, text="Start", command=start_app, bg="green", fg="white")
start_button.pack(side=tk.RIGHT, padx=(30, 5))

stop_button = tk.Button(master=button_frame, text="Stop", command=stop_app, bg="red", fg="white")
stop_button.pack(side=tk.RIGHT, padx=(0, 5))

notes_button = tk.Button(master=button_frame, text="Notes", command=notes_window, bg="blue", fg="white")
notes_button.pack(side=tk.RIGHT, padx=(30, 5))

show_notes_button = tk.Button(master=button_frame, text="Show Notes", command=show_saved_notes_window, bg="blue", fg="white")
show_notes_button.pack(side=tk.RIGHT, padx=(30, 5))






root.mainloop()
