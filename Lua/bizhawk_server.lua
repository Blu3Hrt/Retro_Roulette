local socket = require("socket")
local bizhawkSocket, err = socket.bind("127.0.0.1", 65432)

if bizhawkSocket then
    print("Server started: Listening on localhost:65432")
else
    print("Failed to start server:", err)
    return
end

bizhawkSocket:settimeout(0)  -- Non-blocking accept
local connectionSocket = nil

function acceptConnection()
    if not connectionSocket then
        connectionSocket = bizhawkSocket:accept()
        if connectionSocket then
            print("Client connected")
            connectionSocket:settimeout(0)  -- Non-blocking receive
        end
    end
end

function receiveCommand()
    if connectionSocket then
        local command, err = connectionSocket:receive('*l')  -- Receive one line, handle light userdata issue
        if command then
            print("Received command:", command)
            return command
        elseif err and err ~= "timeout" then
            print("Error receiving command:", err)
            connectionSocket:close()
            connectionSocket = nil
        end
    end
    return nil
end

function loadROM(romPath)
    print("Loading ROM:", romPath)
    client.openrom(romPath) -- Load ROM using BizHawk's functions
end

function saveState(statePath)
    if not fileExists(statePath) then
        -- Create a new save state if it doesn't exist
        savestate.save(statePath)
    end
    print("State saved:", statePath)
end

function loadState(statePath)
    if not fileExists(statePath) then
        print("Error: State not found -", statePath)
        -- Send error response to Python, if necessary
        return
    end
    local success, err = pcall(function() savestate.load(statePath) end)
    if not success then
        print("Error loading state:", err)
        -- Handle the error, like sending a response back to Python
    else
        print("State loaded successfully:", statePath)
    end
end

function fileExists(name)
    local f = io.open(name, "r")
    if f ~= nil then io.close(f) return true else return false end
end

while true do
    acceptConnection()
    local command = receiveCommand()
    if command then
        -- Existing load ROM command
        if command:sub(1, 8) == "loadrom " then
            local romPath = command:sub(9)
            loadROM(romPath)
        -- Additions for save/load state
        elseif command:sub(1, 9) == "savestate " then
            local statePath = command:sub(10)
            saveState(statePath)
        elseif command:sub(1, 10) == "loadstate " then
            local statePath = command:sub(11)
            loadState(statePath)
        end
    end
    emu.frameadvance() -- Keep BizHawk responsive
end
