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

function handleCommand(fullCommand)
    local command, path = fullCommand:match("^(%S+) (.+)$")
    if command == "loadrom" then
        loadROM(path)
    elseif command == "savestate" then
        saveState(path)
    elseif command == "loadstate" then
        loadState(path)
    end
    -- other commands...
end

function receiveCommand()
    if connectionSocket then
        local command, err = connectionSocket:receive('*l')  -- Receive one line
        if command then
            print("Received command:", command)
            return command
        elseif err and err ~= "timeout" then
            print("Error receiving command:", err)
            connectionSocket:close()
            connectionSocket = nil
            -- Reattempt connection
            connectionSocket = bizhawkSocket:accept()
            if connectionSocket then
                connectionSocket:settimeout(0)  -- Non-blocking receive
                print("Client reconnected")
            end
        end
    end
    return nil
end


function loadROM(romPath)
    print("Loading ROM:", romPath)
    client.openrom(romPath)  -- Load ROM using BizHawk's functions
    emu.frameadvance()       -- Advance a frame to allow ROM to load
    emu.frameadvance()       -- Additional frame advance for DS ROMs
end

function loadState(statePath)
    print("Attempting to load state:", statePath)
    if fileExists(statePath) then
        local success, err = pcall(function() savestate.load(statePath) end)
        if success then
            print("State loaded successfully:", statePath)
        else
            print("Error loading state:", err)
        end
    else
        print("State file not found:", statePath)
    end
end

function saveState(statePath)
    local success, err = pcall(function() savestate.save(statePath) end)
    if success then
        print("State saved successfully:", statePath)
    else
        print("Error saving state:", err)
    end
end

function fileExists(name)
    local f = io.open(name, "r")
    if f ~= nil then io.close(f) return true else return false end
end

while true do
    acceptConnection()

    -- Receive a command
    local receivedCommand = receiveCommand()

    if receivedCommand then
        handleCommand(receivedCommand)
    end
    emu.frameadvance() -- Keep BizHawk responsive
end
