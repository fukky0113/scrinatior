import tkinter as tk
from tkinter import filedialog

from PIL import ImageDraw, ImageGrab, ImageTk


class ScreenshotOverlay:
    def __init__(self, window: tk.Toplevel, on_capture) -> None:
        self.window = window
        self.on_capture = on_capture
        self.canvas = tk.Canvas(window, cursor="cross", bg="black", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.start_local = None
        self.start_root = None
        self.rect_id = None

        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

        self.window.bind("<Escape>", lambda _e: self.window.destroy())
        self.window.bind("<ButtonPress-3>", lambda _e: self.window.destroy())

    def _capture(self, left: int, top: int, right: int, bottom: int) -> None:
        image = ImageGrab.grab(bbox=(left, top, right, bottom))
        self.on_capture(image)
        self.window.destroy()

    def on_press(self, event: tk.Event) -> None:
        self.start_local = (event.x, event.y)
        self.start_root = (event.x_root, event.y_root)
        if self.rect_id is not None:
            self.canvas.delete(self.rect_id)
        self.rect_id = self.canvas.create_rectangle(
            event.x,
            event.y,
            event.x,
            event.y,
            outline="red",
            width=2,
        )

    def on_drag(self, event: tk.Event) -> None:
        if not self.start_local or self.rect_id is None:
            return
        x0, y0 = self.start_local
        self.canvas.coords(self.rect_id, x0, y0, event.x, event.y)

    def on_release(self, event: tk.Event) -> None:
        if not self.start_root:
            return
        x0, y0 = self.start_root
        x1, y1 = event.x_root, event.y_root

        left = min(x0, x1)
        top = min(y0, y1)
        right = max(x0, x1)
        bottom = max(y0, y1)

        if right - left < 2 or bottom - top < 2:
            self.window.destroy()
            return

        # Hide the overlay before grabbing to avoid capturing it.
        self.window.withdraw()
        self.window.update_idletasks()
        self.window.after(80, lambda: self._capture(left, top, right, bottom))


class App:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.windows = set()

    def register_window(self, window: tk.Toplevel) -> None:
        self.windows.add(window)
        window.protocol("WM_DELETE_WINDOW", lambda w=window: self.close_window(w))
        window.bind("<Destroy>", lambda e, w=window: self._on_destroy(e, w))

    def close_window(self, window: tk.Toplevel) -> None:
        if window.winfo_exists():
            window.destroy()

    def _on_destroy(self, event: tk.Event, window: tk.Toplevel) -> None:
        if event.widget is not window:
            return
        self.windows.discard(window)
        if not self.windows:
            self.root.quit()
            self.root.destroy()

    def start_capture(self) -> None:
        overlay = tk.Toplevel(self.root)
        overlay.title("Screenshot Selector")
        overlay.attributes("-topmost", True)
        overlay.attributes("-alpha", 0.3)
        overlay.overrideredirect(True)
        overlay.geometry(
            f"{overlay.winfo_screenwidth()}x{overlay.winfo_screenheight()}+0+0"
        )

        self.register_window(overlay)
        ScreenshotOverlay(overlay, self.show_preview)

    def show_preview(self, image) -> None:
        PreviewWindow(self, image)


def main() -> int:
    root = tk.Tk()
    root.withdraw()
    app = App(root)
    app.start_capture()
    root.mainloop()
    return 0


class PreviewWindow:
    def __init__(self, app: App, image) -> None:
        self.app = app
        self.base_image = image
        self.annotated_image = image.copy()
        self.scale = 1.0
        self.last_point = None
        self.min_width = 140
        self.min_height = 90

        self.window = tk.Toplevel(app.root)
        self.window.title("Screenshot Preview")
        self.window.resizable(False, False)
        self.app.register_window(self.window)

        self.canvas = tk.Canvas(self.window, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.photo = None
        self.image_id = None

        self.capture_button = tk.Button(
            self.window, text="追加撮影", command=self.new_capture
        )
        self.capture_button.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-10)
        self.window.update_idletasks()
        self.min_width = max(140, self.capture_button.winfo_reqwidth() + 24)
        self.min_height = max(90, self.capture_button.winfo_reqheight() + 24)
        self._render_image()

        self.menu = tk.Menu(self.window, tearoff=0)
        self.menu.add_command(label="画像の保存", command=self.save_image)
        self.menu.add_separator()
        self.menu.add_command(label="ズームイン", command=self.zoom_in)
        self.menu.add_command(label="ズームアウト", command=self.zoom_out)

        self.canvas.bind("<Button-3>", self.show_menu)
        self.canvas.bind("<Control-ButtonPress-1>", self.on_ctrl_press)
        self.canvas.bind("<Control-B1-Motion>", self.on_ctrl_drag)
        self.canvas.bind("<Control-ButtonRelease-1>", self.on_ctrl_release)

    def close(self) -> None:
        if self.window.winfo_exists():
            self.window.destroy()

    def _render_image(self) -> None:
        image_width = max(1, int(self.annotated_image.width * self.scale))
        image_height = max(1, int(self.annotated_image.height * self.scale))
        resized = self.annotated_image.resize((image_width, image_height))
        self.photo = ImageTk.PhotoImage(resized)

        if self.image_id is None:
            self.image_id = self.canvas.create_image(0, 0, anchor="nw", image=self.photo)
        else:
            self.canvas.itemconfigure(self.image_id, image=self.photo)

        window_width = max(self.min_width, image_width)
        window_height = max(self.min_height, image_height)
        self.canvas.config(scrollregion=(0, 0, image_width, image_height))
        self.canvas.config(width=window_width, height=window_height)
        self.window.geometry(f"{window_width}x{window_height}")

    def show_menu(self, event: tk.Event) -> None:
        self.menu.tk_popup(event.x_root, event.y_root)

    def new_capture(self) -> None:
        self.app.start_capture()

    def save_image(self) -> None:
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg;*.jpeg"), ("All Files", "*.*")],
        )
        if not path:
            return
        self.annotated_image.save(path)

    def zoom_in(self) -> None:
        self.set_zoom(self.scale * 1.25)

    def zoom_out(self) -> None:
        self.set_zoom(self.scale / 1.25)

    def set_zoom(self, new_scale: float) -> None:
        self.scale = max(0.2, min(5.0, new_scale))
        self._render_image()

    def on_ctrl_press(self, event: tk.Event) -> None:
        self.last_point = (event.x / self.scale, event.y / self.scale)

    def on_ctrl_drag(self, event: tk.Event) -> None:
        if self.last_point is None:
            return
        current = (event.x / self.scale, event.y / self.scale)
        draw = ImageDraw.Draw(self.annotated_image)
        draw.line([self.last_point, current], fill="red", width=2)
        self.last_point = current
        self._render_image()

    def on_ctrl_release(self, _event: tk.Event) -> None:
        self.last_point = None


if __name__ == "__main__":
    raise SystemExit(main())
