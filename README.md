# 💬 Secure LAN Chat App

A **secure, real-time LAN chat application** built using Python — featuring **encrypted communication**, **private and global chat tabs**, and a **modern GUI** for both server and client.  
This project is developed as part of a **Computer Networks (CN) B.Tech project**, enabling seamless communication between users connected to the same local network.

---

## 🚀 Overview

The **Secure LAN Chat App** provides a simple yet powerful platform for **real-time messaging within a LAN** (Local Area Network).  
It operates on a **client-server architecture** — where the server manages connections, encryption, and message routing, while clients offer an easy-to-use graphical interface for chatting securely.

Messages are **end-to-end encrypted** using **Fernet (AES-based symmetric encryption)** to ensure complete privacy even within the local network.

---

## ✨ Features

- 🔒 **End-to-End Encryption** using `cryptography.Fernet`
- 🌐 **Global Chat Tab** – for all users on the LAN
- 💬 **Private Chat Tabs** – automatically open when you click a user
- 👥 **Dynamic Online User List**
- 🧱 **Cross-Platform GUI (Tkinter)**
- 🧵 **Multi-threaded Communication**
- 🧠 **Server-Side Authentication**
- ⚡ **Lightweight and Portable**

---

### 🗂️ Folder Structure

```bash
Secure-LAN-Chat/
│
├── server/
│   ├── server_core.py
│   └── server_gui.py
│
├── client/
│   ├── client_core.py
│   └── client_gui.py
│
└── README.md
```

---

## ⚙️ Installation & Setup

---

### 🪟 For Windows

1. **Install Python 3.13.1**

   * Download from [https://www.python.org/downloads/](https://www.python.org/downloads/)
   * During installation, check ✅ *“Add Python to PATH”*

2. **Install Required Package**

   ```bash
   pip install cryptography
   ```

3. **Start the Server**

   ```bash
   cd server
   python server_gui.py
   ```

   * Enter a password (default: `admin123`)
   * Click **Start Server**

4. **Start the Client**

   ```bash
   cd client
   python client_gui.py
   ```

   * Enter:

     * **Server IP:** local IP of the server (e.g. `127.0.0.1`)
     * **Port:** `5555`
     * **Password:** same as server password
     * **Username:** your display name
   * Click **Connect**

---

### 🍏 For macOS / Linux

1. **Install Python 3**

   ```bash
   brew install python3         # macOS (Homebrew)
   sudo apt install python3-pip # Linux (Debian/Ubuntu)
   ```

2. **Install Required Package**

   ```bash
   pip3 install cryptography
   ```

3. **Run the Server**

   ```bash
   cd server
   python3 server_gui.py
   ```

4. **Run the Client**

   ```bash
   cd client
   python3 client_gui.py
   ```

---

## 🧩 How It Works

### 🔐 Encryption

* The server generates a **unique Fernet key** at startup.
* This key is securely shared with connected clients.
* All messages are **encrypted before sending** and **decrypted upon receipt**, ensuring full confidentiality.

### 🌐 Global Chat

* Every user connected to the LAN can chat in the **Global** tab.
* The server broadcasts these messages to all connected clients.
* System messages notify users when someone joins or leaves.

### 💬 Private Chat

* Double-click a username in the **Online Users list** to open a private chat tab.
* Messages are routed securely between the two selected clients only.
* The server handles delivery while preserving end-to-end encryption.

### 🧠 User Management

* Server maintains:

  * A dictionary mapping connections ↔ usernames
  * Real-time user list updates on connect/disconnect

### 🧵 Multithreading

* The server uses **one thread per client** to handle concurrent communication.
* The client runs a background thread for receiving messages without blocking the UI.

---

## 🖼️ GUI Overview

### 🖥️ Server Window

* **Password field**
* **Start/Stop buttons**
* **Connection logs**
* **Real-time status messages**

### 💻 Client Window

* **Global Chat tab (always pinned)**
* **List of online users**
* **Private chat tabs (open dynamically)**
* **Timestamped chat bubbles**
* **Clean, responsive layout**

---

## 🧪 Example Usage

1. **Start the Server**

   ```bash
   python server_gui.py
   ```

   Output:

   ```
   🟢 Server started on 0.0.0.0:5555
   Waiting for clients...
   ```

2. **Start Clients on LAN Devices**

   ```bash
   python client_gui.py
   ```

   Console:

   ```
   🟢 Connected to server 192.168.1.10:5555
   ✅ Authentication successful!
   ```

3. **Chat Example**

   ```
   [Global] Raghav: Hey everyone!
   [Private → Nikhita]: Ready for the CN lab test?
   ```

---

## 🛠️ Tech Stack

| Component    | Technology                         |
| ------------ | ---------------------------------- |
| Language     | Python 3                           |
| GUI          | Tkinter                            |
| Networking   | Socket, Threading                  |
| Security     | `cryptography` (Fernet encryption) |
| Architecture | Client-Server over TCP             |

---

## 🧱 requirements.txt

If you’d like, create a file named `requirements.txt` with this single line:

```
cryptography
```

Then install all dependencies easily using:

```bash
pip install -r requirements.txt
```

---

## 💡 Future Enhancements

* 📁 File Transfer between clients
* 💾 Chat History / Message Logging
* 🔔 Notification pop-ups for new messages
* 🌙 Dark Mode
* 🧑‍💼 Admin Control Panel
* 📡 Multi-room (Group) Chat

---


