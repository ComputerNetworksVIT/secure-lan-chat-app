import socket
import threading
from cryptography.fernet import Fernet
import base64
from datetime import datetime


class ChatServer:
    def __init__(self, host='0.0.0.0', port=5555, password='admin123'):
        self.host = host
        self.port = port
        self.password = password
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients = {}      # {conn: username}
        self.user_conns = {}   # {username: conn}
        self.running = True

        # Generate encryption key
        key = Fernet.generate_key()
        self.cipher = Fernet(key)
        self.encoded_key = base64.b64encode(key)

    # ---------------- START SERVER ----------------
    def start(self, on_log):
        self.on_log = on_log
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(10)
        self.on_log(f"🟢 Server started on {self.host}:{self.port}")
        threading.Thread(target=self.accept_clients, daemon=True).start()

    # ---------------- ACCEPT CLIENTS ----------------
    def accept_clients(self):
        while self.running:
            try:
                conn, addr = self.server_socket.accept()
                threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()
            except OSError: # Server socket might be closed while waiting for accept
                break


    # ---------------- HANDLE EACH CLIENT ----------------
    def handle_client(self, conn, addr):
        username = None # Initialize username to None
        try:
            # Step 1: Authenticate with password
            password = conn.recv(1024).decode('utf-8')
            if password != self.password:
                conn.send(b"INVALID")
                conn.close()
                return

            # Step 2: Send encryption key
            conn.send(self.encoded_key)

            # Step 3: Get username
            username = conn.recv(1024).decode('utf-8')
            # Check for duplicate username
            if username in self.user_conns:
                conn.send(self.cipher.encrypt(b"DUPLICATE_USERNAME"))
                conn.close()
                self.on_log(f"❌ Connection from {addr} rejected: Duplicate username '{username}'")
                return
                
            self.clients[conn] = username
            self.user_conns[username] = conn

            self.on_log(f"👤 {username} connected from {addr}")
            
            # --- NEW: Send current user list to the newly connected client ---
            self.send_user_list(conn) # Send full user list only to the new client
            
            # --- MODIFIED: Broadcast join message and updated user list to ALL clients ---
            # Now, we also broadcast the updated user list to all existing clients
            self.broadcast(f"🟢 {username} joined the chat.")
            self.broadcast_user_list() # Broadcast updated user list
            

            # Step 4: Listen for messages
            while self.running:
                encrypted = conn.recv(4096)
                if not encrypted:
                    break

                msg = self.cipher.decrypt(encrypted).decode('utf-8')
                if msg.startswith("PRIVATE:"):
                    parts = msg.split(":", 2)
                    if len(parts) == 3:
                        _, target, content = parts
                        self.private_message(username, target, content)
                else:
                    self.broadcast(f"{username}: {msg}")

        except Exception as e:
            self.on_log(f"⚠️ Connection error with {addr} ({username or 'Unknown'}): {e}")
        finally:
            self.remove_client(conn, username) # Pass username to remove_client

    # ---------------- BROADCAST MESSAGE ----------------
    def broadcast(self, message):
        encrypted = self.cipher.encrypt(message.encode('utf-8'))
        for conn in list(self.clients.keys()):
            try:
                conn.send(encrypted)
            except:
                self.remove_client(conn) # This will now call remove_client with just conn
        self.on_log(message)
    
    # --- NEW: Send user list to a specific client ---
    def send_user_list(self, conn):
        users = ",".join(self.user_conns.keys())
        msg = f"USERS:{users}"
        try:
            conn.send(self.cipher.encrypt(msg.encode('utf-8')))
        except Exception as e:
            self.on_log(f"Error sending user list to a client: {e}")

    # --- NEW: Broadcast user list to all clients ---
    def broadcast_user_list(self):
        users = ",".join(self.user_conns.keys())
        msg = f"USERS:{users}"
        encrypted = self.cipher.encrypt(msg.encode('utf-8'))
        for conn in list(self.clients.keys()):
            try:
                conn.send(encrypted)
            except:
                self.on_log(f"Error broadcasting user list to client {self.clients.get(conn, 'Unknown')}")
                self.remove_client(conn)

    # ---------------- PRIVATE MESSAGE ----------------
    def private_message(self, sender, target, msg):
        if target in self.user_conns:
            target_conn = self.user_conns[target]
            text = f"💬 [Private] {sender}: {msg}"
            encrypted = self.cipher.encrypt(text.encode('utf-8'))
            
            # Send to target
            try:
                target_conn.send(encrypted)
            except:
                self.on_log(f"Error sending private message to {target}. Removing client.")
                self.remove_client(target_conn)
                return # If target fails, don't try to send to sender again

            # Also send back to sender’s own window for their record
            sender_conn = self.user_conns[sender]
            try:
                sender_conn.send(encrypted) # Send the same message back to sender
            except:
                self.on_log(f"Error sending private message echo to {sender}. Removing client.")
                self.remove_client(sender_conn)

            self.on_log(f"[Private] {sender} → {target}: {msg}")
        else:
            sender_conn = self.user_conns[sender]
            try:
                sender_conn.send(self.cipher.encrypt(f"❌ {target} not found.".encode('utf-8')))
            except:
                self.on_log(f"Error informing {sender} that {target} was not found. Removing client.")
                self.remove_client(sender_conn)


    # ---------------- REMOVE CLIENT ----------------
    # Modified to accept username, or derive it from conn if not provided
    def remove_client(self, conn, username=None):
        if conn in self.clients:
            if username is None: # If username not passed, find it
                username = self.clients.get(conn, "Unknown User")
            
            del self.clients[conn]
            if username in self.user_conns:
                del self.user_conns[username]
            
            # Only broadcast if there are other clients left to receive
            if self.clients:
                self.broadcast(f"🔴 {username} left the chat.")
                self.broadcast_user_list() # Broadcast updated user list after removal
            
            conn.close()
            self.on_log(f"🛑 {username} disconnected.")
        elif username: # If conn not in clients but username is known
            # Clean up user_conns if only username is known but conn is gone
            if username in self.user_conns:
                del self.user_conns[username]
            if self.clients: # Only broadcast if other clients exist
                self.broadcast(f"🔴 {username} left the chat.")
                self.broadcast_user_list()
            self.on_log(f"🛑 {username} (connection already gone) disconnected.")
        else:
            self.on_log(f"🛑 Unknown client disconnected.")


    # ---------------- STOP SERVER ----------------
    def stop(self):
        self.running = False
        # Close all client connections gracefully before closing server socket
        # Iterate over a copy of keys, as self.clients will be modified
        for conn in list(self.clients.keys()):
            self.remove_client(conn)
        
        try:
            self.server_socket.shutdown(socket.SHUT_RDWR) # Attempt graceful shutdown
        except OSError:
            pass # Socket might already be closed
        finally:
            self.server_socket.close()
        self.on_log("🛑 Server stopped.")
