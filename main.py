import socket
import threading
import time
import sys

# Ensure pyperclip is installed before running
try:
    import pyperclip
except ImportError:
    print("[ERROR] 'pyperclip' is not installed! Run 'pip install pyperclip' in your terminal.")
    sys.exit(1)

PORT = 9999
last_synced_text = ""

def start_listener():
    """Background thread that listens for incoming clipboard data from the peer."""
    global last_synced_text
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server.bind(('0.0.0.0', PORT))
        server.listen(5)
        print(f"[SUCCESS] Background Listener is ACTIVE on port {PORT}")
    except Exception as e:
        print(f"[ERROR] Could not start listener on port {PORT}: {e}")
        return

    while True:
        try:
            conn, addr = server.accept()
            data = conn.recv(4096).decode('utf-8')
            
            if data and data != last_synced_text:
                print(f"\n[RECEIVED] New text from {addr[0]}: '{data[:30]}...'")
                last_synced_text = data
                pyperclip.copy(data)
                
            conn.close()
        except Exception as e:
            print(f"[ERROR] Error receiving data: {e}")

def send_text(target_ip, text):
    """Sends copied text to the other computer's listener."""
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(2)  
        client.connect((target_ip, PORT))
        client.sendall(text.encode('utf-8'))
        client.close()
        print(f"[SENT] Successfully pushed clipboard to {target_ip}")
    except socket.timeout:
        print(f"[WARNING] Could not connect to {target_ip} (Timed out - is the script running on the other PC?)")
    except ConnectionRefusedError:
        print(f"[WARNING] Connection refused by {target_ip} (Check Firewall / ensure script is running on peer)")
    except Exception as e:
        print(f"[ERROR] Failed to send: {e}")

def monitor_clipboard(target_ip):
    """Main thread loop that monitors the system clipboard for new copies."""
    global last_synced_text
    print("\n[MONITOR] Clipboard monitoring loop STARTED.")
    print("--------------------------------------------------")
    print("Copy any text (Ctrl+C) to test the network sync...\n")
    
    try:
        last_synced_text = pyperclip.paste()
    except Exception as e:
        print(f"[WARNING] Could not read initial clipboard state: {e}")

    while True:
        try:
            current_text = pyperclip.paste()
            if current_text != last_synced_text and current_text.strip() != "":
                print(f"\n[COPIED] Local change detected: '{current_text[:30]}...'")
                last_synced_text = current_text
                send_text(target_ip, current_text)
                
        except Exception as e:
            print(f"[ERROR] Error reading clipboard: {e}")
            
        time.sleep(1) 

if __name__ == "__main__":
    print("=== CROSS-DEVICE NETWORK CLIPBOARD SYNC ===")
    
    # 1. Start the background server thread first
    listener_thread = threading.Thread(target=start_listener, daemon=True)
    listener_thread.start()
    
    # 2. Get peer IP from user
    peer_ip = input("\nEnter the IP address of the peer computer: ").strip()
    
    if not peer_ip:
        print("[ERROR] No IP provided. Exiting.")
        sys.exit(1)
        
    # 3. Start monitoring clipboard on main thread
    monitor_clipboard(peer_ip)
