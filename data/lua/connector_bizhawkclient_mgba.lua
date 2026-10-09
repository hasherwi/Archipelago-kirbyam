-- KirbyAM adaptation of Zunawe/bhc-substitutes at 8954261f63f8032893b3a9a28a049a718ee480fc.
-- See README.mgba.md for provenance, changes and acceptance limits.
--[[
This is a beta version of a connector script that will allow mGBA to
communicate with Archipelago's BizHawk Client (yes, the name, I know).

Requires mGBA version 0.10.0 or newer.

Place it in the same directory as the normal BizHawk connector
(`Archipelago/data/lua/`). Open your ROM in mGBA, and open
`Tools > Scripting...` in the menus. Then `File > Load script...` in the new
Scripting window and select this file.

Everything should now work just as it does with BizHawk with one exception:

You can only have one instance of mGBA running this script at a time.

Multiple instances of mGBA won't detect each other and will attempt to
communicate over the same port. So you won't be able to have more than one
game connected at a time through mGBA. Still looking for a solution.
]]

local SCRIPT_VERSION = 1
local DEBUG = false

--[[
Copyright (c) 2023-2024 Zunawe

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
]]

local base64 = require("base64")
local json = require("json")

local SOCKET_PORT_FIRST = 43055
local SOCKET_PORT_RANGE_SIZE = 5
local SOCKET_PORT_LAST = SOCKET_PORT_FIRST + SOCKET_PORT_RANGE_SIZE - 1

local STATE_NOT_CONNECTED = 0
local STATE_CONNECTED = 1

local current_state = STATE_NOT_CONNECTED

local message_buffer = console:createBuffer("Archipelago Connector")

local server = nil
local client = nil

-- TCP callbacks do not preserve message boundaries. Keep incomplete lines and sends.
local receive_buffer = ""
local send_buffer = ""
local MAX_BUFFER_BYTES = 1024 * 1024
local last_activity

local locked = false
local platform = nil
local memory_domains = nil

function lock()
    locked = true
end

function unlock()
    locked = false
end

request_handlers = {
    ["PING"] = function (req)
        return {
            ["type"] = "PONG",
        }
    end,

    ["SYSTEM"] = function (req)
        local res = {
            ["type"] = "SYSTEM_RESPONSE",
        }

        if emu:platform() == C.PLATFORM.GB then
            if emu.memory.cart0:read8(0x143) == 0xC0 then
                res["value"] = "GBC"
            else
                res["value"] = "GB"
            end
        elseif emu:platform() == C.PLATFORM.GBA then
            res["value"] = "GBA"
        end

        return res
    end,

    ["PREFERRED_CORES"] = function (req)
        return {
            ["type"] = "PREFERRED_CORES_RESPONSE",
            ["value"] = {},
        }
    end,

    ["HASH"] = function (req)
        local checksum = 0
        for i, v in ipairs({emu:checksum(C.CHECKSUM.CRC32):byte(1, 4)}) do
            checksum = checksum * 256 + v
        end

        return {
            ["type"] = "HASH_RESPONSE",
            ["value"] = string.format("%x", checksum),
        }
    end,

    ["MEMORY_SIZE"] = function (req)
        local res = {}

        res["type"] = "MEMORY_SIZE_RESPONSE"
        res["value"] = memory_domains[req["domain"]]:size()
        return res
    end,

    ["GUARD"] = function (req)
        local expected_data = base64.decode(req["expected_data"])

        local s = memory_domains[req["domain"]]:readRange(req["address"], #expected_data)
        local actual_data = {}
        for i = 1, #s do
            actual_data[i] = s:byte(i)
        end

        local data_is_validated = true
        for i, byte in ipairs(actual_data) do
            if byte ~= expected_data[i] then
                data_is_validated = false
                break
            end
        end

        return {
            ["type"] = "GUARD_RESPONSE",
            ["address"] = req["address"],
            ["value"] = data_is_validated,
        }
    end,

    ["LOCK"] = function (req)
        lock()

        return {
            ["type"] = "LOCKED",
        }
    end,

    ["UNLOCK"] = function (req)
        unlock()

        return {
            ["type"] = "UNLOCKED",
        }
    end,

    ["READ"] = function (req)
        local s = memory_domains[req["domain"]]:readRange(req["address"], req["size"])
        local d = {}
        for i = 1, #s do
            d[i] = s:byte(i)
        end

        return {
            ["type"] = "READ_RESPONSE",
            ["value"] = base64.encode(d),
        }
    end,

    ["WRITE"] = function (req)
        for i, byte in ipairs(base64.decode(req["value"])) do
            memory_domains[req["domain"]]:write8(req["address"] + (i - 1), byte)
        end

        return {
            ["type"] = "WRITE_RESPONSE",
        }
    end,

    ["DISPLAY_MESSAGE"] = function (req)
        message_buffer:print(req["message"].."\n")

        return {
            ["type"] = "DISPLAY_MESSAGE_RESPONSE",
        }
    end,

    ["default"] = function (req)
        return {
            ["type"] = "ERROR",
            ["err"] = "Unknown command: "..req["type"],
        }
    end,
}

function process_request (req)
    if request_handlers[req["type"]] then
        local success, res = pcall(request_handlers[req["type"]], req)

        if not success then
            res = {
                ["type"] = "ERROR",
                ["err"] = res
            }
        end

        return res
    else
        return request_handlers["default"](req)
    end
end

local function disconnect_client(reason)
    local previous = client
    client = nil
    locked = false
    receive_buffer = ""
    send_buffer = ""
    last_activity = nil
    if previous then previous:close() end
    console:log("Client disconnected: "..reason)
end

local function flush_responses()
    while client and #send_buffer > 0 do
        local sent, err = client:send(send_buffer)
        if not sent then
            if err ~= socket.ERRORS.AGAIN then disconnect_client(tostring(err)) end
            return
        end
        if sent == 0 then return end
        send_buffer = send_buffer:sub(sent + 1)
    end
end

local function process_line(line)
    if line == "VERSION" then return tostring(SCRIPT_VERSION) end
    local requests = json.decode(line)
    if type(requests) ~= "table" then error("Expected a request array") end
    local responses = {}
    local failed_guard_response = nil
    for i, req in ipairs(requests) do
        if failed_guard_response then
            responses[i] = failed_guard_response
        else
            responses[i] = process_request(req)
            if responses[i].type == "GUARD_RESPONSE" and not responses[i].value then
                failed_guard_response = responses[i]
            end
        end
    end
    return json.encode(responses)
end

function received()
    if not client then return end
    while client do
        local piece, err = client:receive(1024)
        if not piece then
            if err ~= socket.ERRORS.AGAIN then disconnect_client(tostring(err)) end
            break
        end
        if #piece == 0 then disconnect_client("EOF"); return end
        last_activity = os.time()
        receive_buffer = receive_buffer..piece
        if #receive_buffer > MAX_BUFFER_BYTES then
            disconnect_client("Request buffer limit exceeded")
            return
        end
        while client do
            local ending = receive_buffer:find("\n", 1, true)
            if not ending then break end
            local line = receive_buffer:sub(1, ending - 1)
            receive_buffer = receive_buffer:sub(ending + 1)
            local ok, response = pcall(process_line, line)
            if not ok then
                -- Reject this stream; never execute the tail of a malformed batch.
                disconnect_client("Malformed request")
                return
            end
            send_buffer = send_buffer..response.."\n"
            if #send_buffer > MAX_BUFFER_BYTES then
                disconnect_client("Response buffer limit exceeded")
                return
            end
            flush_responses()
        end
    end
end

function accept()
    console:log("")  -- Black Magic: Printing something here allows recovery from a timeout due to last_activity.
                     -- Removing this causes a timeout to be unrecoverable. The client never appears to connect.

    local err = nil
    local data = nil

    if client == nil then
        client, err = server:accept()
        if err then
            console:error(err)
            return
        end
        receive_buffer = ""
        send_buffer = ""
        locked = false
        last_activity = os.time()
        console:log("Connected (mGBA protocol 1)")

        client:add("received", received)
        client:add("error", function() disconnect_client("Socket error") end)

        server:close()
        server = nil
    end
end

function tick()
    if platform ~= emu:platform() then
        platform = emu:platform()

        if platform == C.PLATFORM.GB then
            memory_domains = {
                ["ROM"] = emu.memory.cart0,
                ["VRAM"] = emu.memory.vram,
                ["SRAM"] = emu.memory.sram,
                ["CartRAM"] = emu.memory.sram,
                ["WRAM"] = emu.memory.wram,
                ["OAM"] = emu.memory.oam,
                ["IO"] = emu.memory.io,
                ["HRAM"] = emu.memory.hram,
                ["System Bus"] = emu
            }
        else
            memory_domains = {
                ["BIOS"] = emu.memory.bios,
                ["ROM"] = emu.memory.cart0,
                ["EWRAM"] = emu.memory.wram,
                ["IWRAM"] = emu.memory.iwram,
                ["VRAM"] = emu.memory.vram,
                ["OAM"] = emu.memory.oam,
                ["Combined WRAM"] = emu.memory.wram,
                ["System Bus"] = emu,
                -- ["SRAM"] = emu.memory.cart0,
                -- ["PALRAM"] = emu.memory.cart0,
            }
        end
    end

    if client == nil then
        if server == nil then
            create_server()
        end
    else
        if last_activity ~= nil and os.time() - last_activity > 5 then
            disconnect_client("Timeout")
        else
            flush_responses()
            while locked and client do
                if os.time() - last_activity > 5 then
                    disconnect_client("Timeout while locked")
                    break
                end
                client:poll()
                flush_responses()
            end
        end
    end
end

function create_server()
    -- The AP client scans exactly 43055..43059, on loopback only.
    for port = SOCKET_PORT_FIRST, SOCKET_PORT_LAST do
        local candidate, err = socket.tcp()
        if not candidate then
            console:error(tostring(err))
            return
        end
        local bound
        bound, err = candidate:bind("127.0.0.1", port)
        if bound then
            local listening
            listening, err = candidate:listen(1)
            if listening then
                server = candidate
                console:log("Waiting for client on 127.0.0.1:"..port.." (mGBA protocol 1)")
                server:add("received", accept)
                return
            end
        end
        candidate:close()
    end
    console:error("No connector port available (43055-43059); stop other connector instances")
end

callbacks:add("frame", tick)
