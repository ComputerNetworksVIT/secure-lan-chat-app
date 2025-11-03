# LANChatApp/client/client_gui.py
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
from datetime import datetime
from client_core import ChatClient  # expects the ChatClient class in client_core.py


# ---------------- UI COLORS & STYLES ----------------
BG = "#f4f7fb"
TOP_BG = "#1f6feb"
TAB_ACTIVE_BG = "#4ea1ff"
GLOBAL_TAB_COLOR = "#e9f2ff"
PRIVATE_TAB_COLOR = "#fff7e6"
MSG_FONT = ("Segoe UI", 10)
TIMESTAMP_FMT = "%H:%M"

# Chat bubble specific colors
SENT_MSG_COLOR = "#DCF8C6"  # Light green for sent messages
REC_MSG_COLOR = "#FFFFFF"  # White for received messages
JOIN_LEAVE_COLOR = "#90A4AE" # Grey for join/leave notifications
TEXT_COLOR = "#212121"      # Dark text for readability


class TabChat:
    """Helper container for tab widgets (each tab has its own text widget)"""
    def __init__(self, parent_notebook, title, bg_color):
        self.title = title
        self.frame = tk.Frame(parent_notebook, bg=bg_color)
        
        # Changed to tk.Text for more control over tags and alignment
        self.text = tk.Text(
            self.frame, wrap="word", state="disabled",
            font=MSG_FONT, bg=bg_color, relief="flat", padx=5, pady=5,
            foreground=TEXT_COLOR # Default text color for general content
        )
        self.text.pack(fill="both", expand=True, padx=6, pady=6)

        # Configure tags for message styling
        # lmargin1: indent for first line, lmargin2: indent for subsequent lines
        # rmargin: right margin
        # justify: text alignment
        self.text.tag_configure("sent", background=SENT_MSG_COLOR, lmargin1=150, lmargin2=150, rmargin=10, justify="right", wrap="word")
        self.text.tag_configure("received", background=REC_MSG_COLOR, lmargin1=10, lmargin2=10, rmargin=150, justify="left", wrap="word")
        self.text.tag_configure("info", foreground=JOIN_LEAVE_COLOR, justify="center", font=(MSG_FONT[0], 9, "italic"), wrap="word") # For join/leave messages, slightly smaller/italic
        

    def display_message(self, sender, message, is_self=False, is_info=False):
        self.text.config(state="normal")
        
        timestamp = datetime.now().strftime(TIMESTAMP_FMT)
        
        if is_info:
            full_msg = f"  {message}  \n" # Add some padding for info messages
            self.text.insert("end", full_msg, "info")
        elif is_self:
            # For sent messages, we embed timestamp
            full_msg = f"{message} [{timestamp}]\n"
            self.text.insert("end", full_msg, "sent")
        else:
            # For received messages, show sender, message, and timestamp
            full_msg = f"{sender}: {message} [{timestamp}]\n"
            self.text.insert("end", full_msg, "received")
            
        self.text.config(state="disabled")
        self.text.see("end")


class ClientGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("LAN Chat — Modern (Global + Private Tabs)")
        self.root.geometry("900x600")
        self.root.configure(bg=BG)

        self.client = None
        self.username = None

        self.users = set()            # current known online users
        self.private_tabs = {}        # username -> TabChat

        # Build connect UI first
        self._build_connect_ui()

    # ---------------- Connect UI ----------------
    def _build_connect_ui(self):
        for w in self.root.winfo_children(): w.destroy()

        frame = tk.Frame(self.root, bg=BG)
        frame.place(relx=0.5, rely=0.5, anchor="center")

        title = tk.Label(frame, text="LAN Chat", font=("Segoe UI", 20, "bold"), bg=BG, fg=TOP_BG)
        title.pack(pady=(0,10))

        lbl_ip = tk.Label(frame, text="Server IP:", bg=BG)
        lbl_ip.pack(anchor="w")
        self.ip_entry = ttk.Entry(frame, width=30)
        self.ip_entry.insert(0, "127.0.0.1")
        self.ip_entry.pack(pady=4)

        lbl_port = tk.Label(frame, text="Server Port:", bg=BG)
        lbl_port.pack(anchor="w")
        self.port_entry = ttk.Entry(frame, width=30)
        self.port_entry.insert(0, "5555")
        self.port_entry.pack(pady=4)

        lbl_pass = tk.Label(frame, text="Password:", bg=BG)
        lbl_pass.pack(anchor="w")
        self.pass_entry = ttk.Entry(frame, show="*", width=30)
        self.pass_entry.insert(0, "admin123") # Default password changed for consistency
        self.pass_entry.pack(pady=4)

        lbl_user = tk.Label(frame, text="Username:", bg=BG)
        lbl_user.pack(anchor="w")
        self.user_entry = ttk.Entry(frame, width=30)
        self.user_entry.insert(0, "user1")
        self.user_entry.pack(pady=8)

        connect_btn = tk.Button(frame, text="Connect", bg=TOP_BG, fg="white",
                                font=("Segoe UI", 10, "bold"), relief="flat",
                                command=self.connect_to_server)
        connect_btn.pack(pady=(6,0))

    # ---------------- Connect logic ----------------
    def connect_to_server(self):
        ip = self.ip_entry.get().strip()
        try:
            port = int(self.port_entry.get().strip())
        except ValueError: # Catch specific error for clarity
            messagebox.showerror("Invalid port", "Please enter a valid port number.")
            return
        password = self.pass_entry.get().strip()
        username = self.user_entry.get().strip()
        if not (ip and password and username):
            messagebox.showwarning("Missing", "Fill all fields before connecting.")
            return

        # create client and connect
        self.client = ChatClient(ip, port, password, username)
        ok = self.client.start()
        if not ok:
            # Check if connection failed due to specific error messages captured by client_core
            if "Invalid password" in self.client.last_error_msg:
                messagebox.showerror("Connection Failed", "Invalid server password.")
            elif "Duplicate username" in self.client.last_error_msg:
                messagebox.showerror("Connection Failed", "Username already in use. Please choose another.")
            else:
                # Generic connection failure
                messagebox.showerror("Connection failed", f"Could not connect to server: {self.client.last_error_msg}")
            return

        self.username = username
        # build main UI and start receiver thread
        self._build_main_ui()
        threading.Thread(target=self.receiver_loop, daemon=True).start()

    # ---------------- Main UI ----------------
    def _build_main_ui(self):
        for w in self.root.winfo_children(): w.destroy()

        # Top Header
        header = tk.Frame(self.root, bg=TOP_BG, height=50)
        header.pack(fill="x")
        title = tk.Label(header, text=f"Connected as {self.username}", bg=TOP_BG, fg="white",
                         font=("Segoe UI", 11, "bold"))
        title.pack(side="left", padx=12, pady=10)

        disconnect_btn = tk.Button(header, text="Disconnect", bg="#ff6b6b", fg="white",
                                   relief="flat", command=self.disconnect)
        disconnect_btn.pack(side="right", padx=12, pady=8)

        # Left: online users
        left = tk.Frame(self.root, bg="#f0f4f8", width=200)
        left.pack(side="left", fill="y")

        lbl = tk.Label(left, text="Online Users", bg="#f0f4f8", font=("Segoe UI", 10, "bold"))
        lbl.pack(anchor="nw", padx=8, pady=(8,0))

        self.users_listbox = tk.Listbox(left, bg="white", selectbackground="#4ea1ff",
                                        selectforeground="black", font=MSG_FONT, activestyle="none")
        self.users_listbox.pack(fill="both", expand=True, padx=8, pady=8)
        self.users_listbox.bind("<Double-Button-1>", self._open_private_tab_from_list)

        # Right: Notebook (tabs)
        right = tk.Frame(self.root, bg=BG)
        right.pack(side="right", fill="both", expand=True)

        # Notebook for tabs
        style = ttk.Style()
        style.theme_use("default")
        style.configure("TNotebook.Tab", padding=[12, 6], font=("Segoe UI", 10, "bold"))
        style.map("TNotebook.Tab", background=[("selected", TAB_ACTIVE_BG)])

        self.notebook = ttk.Notebook(right)
        self.notebook.pack(fill="both", expand=True, padx=6, pady=8)

        # Global tab pinned first
        self.global_tab = TabChat(self.notebook, "Global", GLOBAL_TAB_COLOR)
        self.notebook.add(self.global_tab.frame, text="Global")

        # Input area below tabs
        bottom = tk.Frame(self.root, bg=BG)
        bottom.pack(fill="x", side="bottom", padx=8, pady=8)

        self.msg_entry = ttk.Entry(bottom, font=MSG_FONT)
        self.msg_entry.pack(side="left", fill="x", expand=True, padx=(0,6))
        self.msg_entry.bind("<Return>", lambda e: self._on_send())

        send_btn = tk.Button(bottom, text="Send", bg=TOP_BG, fg="white", relief="flat",
                             command=self._on_send)
        send_btn.pack(side="right")

    # ---------------- open private tab via users list ----------------
    def _open_private_tab_from_list(self, event=None):
        sel = None
        try:
            # Check if something is actually selected
            if not self.users_listbox.curselection():
                return
            sel = self.users_listbox.get(self.users_listbox.curselection())
        except tk.TclError: # Handle case where nothing is selected or listbox interaction issue
            return
        if not sel or sel == self.username:
            return
        self.open_private_tab(sel)

    def open_private_tab(self, username):
        # if already exists, switch to it
        if username in self.private_tabs:
            # Find the tab's index by iterating through notebook frames
            for i, frame_id in enumerate(self.notebook.tabs()):
                if frame_id == str(self.private_tabs[username].frame):
                    self.notebook.select(i)
                    return
            return # Should not happen if in private_tabs (defensive)
        
        # create new tab
        tab = TabChat(self.notebook, username, PRIVATE_TAB_COLOR)
        self.private_tabs[username] = tab
        self.notebook.add(tab.frame, text=username)
        self.notebook.select(tab.frame) # Switch to the new tab

    # ---------------- sending messages ----------------
    def _on_send(self):
        text = self.msg_entry.get().strip()
        if not text:
            return
        
        # determine active tab
        sel = self.notebook.select()
        # if global tab active
        if sel == str(self.global_tab.frame):
            # Send public message
            self.client.send_message(text)
            # Display immediately in your own global tab as 'sent'
            self.global_tab.display_message(self.username, text, is_self=True)
        else:
            # private tab: find which username
            target = None
            for user, tab in self.private_tabs.items():
                if str(tab.frame) == sel:
                    target = user
                    self.client.send_message(text, target=target)
                    # Display immediately in private tab as 'sent'
                    # The server will echo this message back to the sender,
                    # but we will filter it out in _process_message
                    tab.display_message(self.username, text, is_self=True)
                    break
        self.msg_entry.delete(0, "end")

    # ---------------- receiver loop ----------------
    def receiver_loop(self):
        # Ensure UI built
        # This loop waits for the UI to be ready before proceeding,
        # preventing errors if messages arrive before elements exist.
        while not hasattr(self, "notebook") or not self.notebook.winfo_exists():
            time.sleep(0.05)
            if not self.client or not self.client.running: # Check if client disconnected while waiting
                return

        while self.client and self.client.running:
            try:
                msg = self.client.receive_message()
                if not msg:
                    # connection probably closed, or an error occurred
                    # Use a small delay to allow UI to finish current processing before disconnecting
                    self.root.after(100, self.disconnect)
                    break
                # process message on the GUI thread
                self.root.after(0, self._process_message, msg)
            except Exception as e:
                # Catch exceptions during message reception
                print(f"Error in receiver loop: {e}")
                self.root.after(100, self.disconnect)
                break


    # ---------------- process incoming messages ----------------
    def _process_message(self, msg):
        # Handle server rejecting duplicate username - this would be an internal client_core message
        # If client_core handles it and reports via last_error_msg, client_gui doesn't need to display it as a chat msg.
        if msg == "DUPLICATE_USERNAME":
            # This is an internal message, already handled by client.start() logic, so just ignore it here.
            return

        # Check for system messages first:
        if msg.startswith("USERS:"): # Handles updated user list (Issue 1)
            try:
                user_list_str = msg.split(":", 1)[1]
                # Filter out own username and empty strings, then convert to set
                users = {u.strip() for u in user_list_str.split(",") if u.strip() and u.strip() != self.username}
                
                # Clear and update self.users set
                self.users.clear()
                self.users.update(users)
                
                # Update listbox
                self.users_listbox.delete(0, "end")
                for u in sorted(list(self.users)): # Display sorted for consistency
                    self.users_listbox.insert("end", u)
            except Exception as e:
                self.global_tab.display_message(None, f"Error processing user list: {e}", is_info=True)
            return
        
        # 1) If it's a join/leave message
        # We no longer rely on these to update the user listbox (USERS: messages do that),
        # but we still display them in global chat as info.
        if msg.startswith("🟢 ") and " joined the chat" in msg:
            self.global_tab.display_message(None, msg, is_info=True) # Display as info
            return

        if msg.startswith("🔴 ") and " left the chat" in msg:
            self.global_tab.display_message(None, msg, is_info=True) # Display as info
            return

        # 2) Private messages from server: format server sends: "💬 [Private] sender: message"
        if msg.startswith("💬 [Private]"):
            try:
                rest = msg.replace("💬 [Private] ", "", 1)
                sender, content = rest.split(":", 1)
                sender = sender.strip()
                content = content.strip()
            except Exception:
                # If parsing fails, treat as general info
                self.global_tab.display_message(None, msg, is_info=True)
                return

            # --- MODIFIED (for Issue 2) ---
            # If this private message is an echo of *our own* sent message,
            # and we have already displayed it in _on_send (as is_self=True),
            # then simply return to avoid duplicate display in the sender's own tab.
            if sender == self.username:
                # The _on_send method already ensured the tab is open and displayed the message.
                # So we simply ignore the server's echo back to us.
                return 

            # If it's a private message from another user, ensure their tab is open and display
            if sender not in self.private_tabs:
                self.open_private_tab(sender)
            
            # Display in that tab as a 'received' message
            self.private_tabs[sender].display_message(sender, content, is_self=False)
            return
        
        # 3) Regular broadcast messages (your own messages are handled by _on_send,
        # and filtered out here to avoid duplicates. Others' broadcasts are displayed.)
        try:
            sender, content = msg.split(":", 1)
            sender = sender.strip()
            content = content.strip()
            
            # If the broadcast message is from ourselves, and we've already displayed it locally, skip it.
            # This avoids duplicate messages (one immediately displayed, one from server broadcast).
            if sender == self.username:
                return 
            
            self.global_tab.display_message(sender, content, is_self=False) # Display as received
        except ValueError:
            # If message doesn't fit "sender: content" format (e.g., server announcements not already caught)
            self.global_tab.display_message(None, msg, is_info=True)


    # ---------------- disconnect ----------------
    def disconnect(self):
        try:
            if self.client:
                self.client.disconnect()
                self.client = None # Clear client object
        except Exception as e:
            print(f"Error during GUI disconnect process: {e}")
        finally:
            messagebox.showinfo("Disconnected", "You have been disconnected from the server.")
            self._build_connect_ui()


if __name__ == "__main__":
    root = tk.Tk()
    app = ClientGUI(root)
    root.mainloop()