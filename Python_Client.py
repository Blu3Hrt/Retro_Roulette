import socket
import os

sock = None

def send_command(command):
    global sock
    if sock is None or sock.fileno() == -1:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(("127.0.0.1", 65432))  # Ensure IP and port match Lua script
    sock.sendall((command + "\n").encode())  # Append newline to command

def to_absolute_path(relative_path):
    return os.path.abspath(relative_path)

def load_rom(rom_path):
    path = to_absolute_path(rom_path)
    print("Loading ROM from path:", path)
    send_command(f"loadrom {path}")
    
def save_state(state_path):
    path = to_absolute_path(state_path)
    print("Saving state to path:", path)
    send_command(f"savestate {path}")

def load_state(state_path):
    path = to_absolute_path(state_path)
    print("Loading state from path:", path)
    send_command(f"loadstate {path}")   


# Example usage
# load_rom("E:\\Coding\\Retro_Roulette\\Games\\Pokemon_FireRed.gba")
