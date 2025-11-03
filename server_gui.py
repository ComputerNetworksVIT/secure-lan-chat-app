import tkinter as tk
from tkinter import scrolledtext, messagebox
from server_core import ChatServer


class ChatServerGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("💬 LAN Chat Server")
        self.master.geometry("650x500")
        self.master.configure(bg="#121212")

        self.server = None

        # ---------------- UI SETUP ----------------
        tk.Label(master, text="Server Password:", bg="#121212", fg="white").pack(pady=(10, 0))
        self.password_entry = tk.Entry(master, show="*", width=30)
        self.password_entry.pack(pady=(0, 10))

        self.start_btn = tk.Button(master, text="Start Server", bg="#00C853", fg="white",
                                   font=('Segoe UI', 10, 'bold'), command=self.start_server)
        self.start_btn.pack(pady=10)

        tk.Label(master, text="Server Log:", bg="#121212", fg="#CCCCCC").pack()
        self.log_box = scrolledtext.ScrolledText(master, bg="#1E1E1E", fg="white",
                                                 state="disabled", wrap="word", height=20)
        self.log_box.pack(fill="both", expand=True, padx=10, pady=5)

        stop_btn = tk.Button(master, text="Stop Server", bg="#D50000", fg="white",
                             font=('Segoe UI', 10, 'bold'), command=self.stop_server)
        stop_btn.pack(pady=(0, 10))

    # ---------------- START SERVER ----------------
    def start_server(self):
        password = self.password_entry.get().strip()
        if not password:
            messagebox.showwarning("Missing Field", "Please enter a password!")
            return

        self.server = ChatServer(password=password)
        self.server.start(self.log_message)
        self.start_btn.config(state="disabled")

    # ---------------- LOG MESSAGES ----------------
    def log_message(self, msg):
        self.log_box.config(state="normal")
        self.log_box.insert("end", msg + "\n")
        self.log_box.config(state="disabled")
        self.log_box.see("end")

    # ---------------- STOP SERVER ----------------
    def stop_server(self):
        if self.server:
            self.server.stop()
        self.master.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = ChatServerGUI(root)
    root.mainloop()
