import socket
import threading
import base64
import time
from cryptography.fernet import Fernet


class ChatClient:
    def __init__(self, server_ip, server_port, password, username):
        self.server_ip = server_ip
        self.server_port = server_port
        self.password = password
        self.username = username

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.cipher = None
        self.running = True
        self.last_error_msg = "" # NEW: To store specific error messages

    # ---------------- CONNECT TO SERVER ----------------
    def start(self):
        self.last_error_msg = "" # Reset error message on each connection attempt
        try:
            self.socket.connect((self.server_ip, self.server_port))

            # Step 1: Send password for authentication
            self.socket.send(self.password.encode('utf-8'))
            response = self.socket.recv(1024)
            if response == b"INVALID":
                self.last_error_msg = "Invalid password."
                print("❌ Invalid password.")
                return False

            # Step 2: Decode encryption key and set up Fernet cipher
            self.cipher = Fernet(base64.b64decode(response))

            time.sleep(0.1)

            # Step 3: Send username once encryption is ready
            self.socket.send(self.username.encode('utf-8'))
            
            # Receive immediate feedback after sending username, could be DUPLICATE_USERNAME
            # We use a non-blocking check here to see if there's an immediate response
            # from the server, like a duplicate username rejection.
            self.socket.settimeout(0.5) # Temporarily set a timeout
            try:
                initial_response_encrypted = self.socket.recv(4096)
                if initial_response_encrypted:
                    initial_response = self.cipher.decrypt(initial_response_encrypted).decode('utf-8')
                    if initial_response == "DUPLICATE_USERNAME":
                        self.last_error_msg = "Duplicate username. Please choose another."
                        print("❌ Duplicate username.")
                        self.socket.close()
                        return False
                    # If it's not a duplicate username message, process it as a regular message
                    # This might be the initial USERS: list or a join message from another client
                    # For now, we'll let receive_message handle it in the loop
                    # For a robust solution, you might want to buffer this first message
                    # or explicitly handle the initial USERS: response here.
                    # For simplicity, we'll rely on _process_message in client_gui.py
                    # to correctly handle the first incoming messages in the receiver_loop.

            except socket.timeout:
                pass # No immediate response, which is fine
            except Exception as e:
                self.last_error_msg = f"Error during initial server response: {e}"
                print(f"❌ Error during initial server response: {e}")
                self.socket.close()
                return False
            finally:
                self.socket.settimeout(None) # Reset to blocking mode

            print("🟢 Connected successfully!")
            return True

        except Exception as e:
            self.last_error_msg = f"Connection failed: {e}"
            print(f"❌ Connection failed: {e}")
            return False

    # ---------------- RECEIVE MESSAGES ----------------
    def receive_message(self):
        try:
            encrypted = self.socket.recv(4096)
            if not encrypted:
                return None
            message = self.cipher.decrypt(encrypted).decode('utf-8')
            return message
        except Exception as e:
            # print(f"Error receiving message: {e}") # Debugging
            self.running = False
            return None

    # ---------------- SEND PUBLIC OR PRIVATE MESSAGES ----------------
    def send_message(self, msg, target=None):
        """
        Sends a public message if target is None,
        or a private message if target is provided.
        """
        if not msg.strip():
            return

        try:
            if target:
                msg = f"PRIVATE:{target}:{msg}"
            encrypted = self.cipher.encrypt(msg.encode('utf-8'))
            self.socket.send(encrypted)
        except Exception as e:
            print(f"❌ Error sending message: {e}")

    # ---------------- DISCONNECT ----------------
    def disconnect(self):
        try:
            self.running = False
            # Attempt a graceful shutdown if socket is still connected
            if self.socket:
                self.socket.shutdown(socket.SHUT_RDWR)
                self.socket.close()
        except OSError: # Socket might already be closed
            pass
        except Exception as e:
            print(f"Error during disconnect: {e}")