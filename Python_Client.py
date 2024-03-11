import socket
import time

def send_command(command):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect(("127.0.0.1", 65432))  # Ensure IP and port match Lua script
        sock.sendall((command + "\n").encode())  # Append newline to command
        time.sleep(1)  # Wait a bit to allow the server to process the command

def load_rom(rom_path):
    send_command(f"loadrom {rom_path}")
    
def save_state(state_path):
    send_command(f"savestate {state_path}")

def load_state(state_path):
    send_command(f"loadstate {state_path}")    

# Example usage
# load_rom("E:\\Coding\\Retro_Roulette\\Games\\Pokemon_FireRed.gba")
