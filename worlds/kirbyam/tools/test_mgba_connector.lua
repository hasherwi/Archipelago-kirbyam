-- Host contract harness. No ROM, real sockets, emulator, or save files.
-- From repository root, after reviewing the adapter: lua worlds/kirbyam/tools/test_mgba_connector.lua
package.path = "data/lua/?.lua;"..package.path
local json = require("json")
local base64 = require("base64")
local logs, bound_ports = {}, {}
console = {
    log = function(_, msg) logs[#logs + 1] = msg end,
    error = function(_, msg) logs[#logs + 1] = msg end,
    createBuffer = function() return {print = function(_, msg) logs[#logs + 1] = msg end} end,
}
C = {PLATFORM = {GBA = 1, GB = 2}, CHECKSUM = {CRC32 = 1}}
local function memory()
    return {
        bytes = {},
        readRange = function(self, address, count)
            local bytes = {}
            for i = 0, count - 1 do bytes[#bytes + 1] = string.char(self.bytes[address + i] or 0) end
            return table.concat(bytes)
        end,
        write8 = function(self, address, value) self.bytes[address] = value end,
        size = function() return 0x1000000 end,
    }
end
emu = memory()
emu.platform = function() return C.PLATFORM.GBA end
emu.checksum = function() return string.char(0x12, 0x34, 0x56, 0x78) end
emu.memory = {cart0 = memory(), wram = memory(), iwram = memory()}
local frame
callbacks = {add = function(_, event, fn) assert(event == "frame"); frame = fn end}
local now = 100
os.time = function() return now end
local accepted, listener
local busy_ports = {}
socket = {ERRORS = {AGAIN = "again"}}
local function connection()
    return {
        callbacks = {}, input = {}, output = "", closed = false,
        add = function(self, event, fn) self.callbacks[event] = fn end,
        close = function(self) self.closed = true end,
        receive = function(self)
            if #self.input > 0 then return table.remove(self.input, 1) end
            return nil, socket.ERRORS.AGAIN
        end,
        send = function(self, value)
            if self.blocked then return nil, socket.ERRORS.AGAIN end
            local count = math.min(#value, self.send_limit or #value)
            self.output = self.output..value:sub(1, count)
            return count
        end,
        poll = function(self) self.callbacks.error() end,
    }
end
socket.tcp = function()
    local sock = connection()
    sock.bind = function(_, address, port)
        assert(address == "127.0.0.1")
        bound_ports[#bound_ports + 1] = port
        if busy_ports[port] then return nil, "busy" end
        return 1
    end
    sock.listen = function(self) listener = self; return 1 end
    sock.accept = function() return accepted end
    return sock
end

dofile("worlds/kirbyam/mgba/connector_bizhawkclient_mgba.lua")
local function connect()
    frame()
    accepted = connection()
    listener.callbacks.received()
    return accepted
end
local function feed(conn, text)
    conn.input[#conn.input + 1] = text
    conn.callbacks.received()
end
local function request(conn, requests)
    conn.output = ""
    feed(conn, json.encode(requests).."\n")
    return json.decode(conn.output)
end
local conn = connect()
assert(bound_ports[1] == 43055)
feed(conn, "VER")
assert(conn.output == "")
feed(conn, "SION\n")
assert(conn.output == "1\n")
conn.output = ""
local wire = '[{"type":"SYSTEM"},{"type":"HASH"}]\n'
for i = 1, #wire - 1 do feed(conn, wire:sub(i, i)); assert(conn.output == "") end
feed(conn, wire:sub(-1))
local response = json.decode(conn.output)
assert(response[1].value == "GBA" and response[2].value == "12345678")
conn.output = ""
conn.send_limit = 2
feed(conn, 'VERSION\n[{"type":"PING"}]\n')
assert(conn.output == '1\n[{"type":"PONG"}]\n')
conn.send_limit = nil
conn.blocked = true
conn.output = ""
feed(conn, "VERSION\n")
assert(conn.output == "")
conn.blocked = false
frame()
assert(conn.output == "1\n")
emu.memory.cart0.bytes[0xA0] = 0x41
response = request(conn, {{type="READ", domain="ROM", address=0xA0, size=1}})
assert(base64.decode(response[1].value)[1] == 0x41)
response = request(conn, {
    {type="GUARD", domain="System Bus", address=0x02000000, expected_data=base64.encode({1})},
    {type="WRITE", domain="System Bus", address=0x02000001, value=base64.encode({9})},
})
assert(response[1].value == false and response[2].type == "GUARD_RESPONSE")
assert(emu.bytes[0x02000001] == nil)
emu.bytes[0x02000000] = 1
response = request(conn, {
    {type="GUARD", domain="System Bus", address=0x02000000, expected_data=base64.encode({1})},
    {type="WRITE", domain="System Bus", address=0x02000001, value=base64.encode({9})},
    {type="READ", domain="System Bus", address=0x02000001, size=1},
    {type="DISPLAY_MESSAGE", message="Received item"},
})
assert(response[2].type == "WRITE_RESPONSE" and emu.bytes[0x02000001] == 9)
assert(base64.decode(response[3].value)[1] == 9)
assert(logs[#logs] == "Received item\n")
response = request(conn, {{type="READ", domain="Unsupported", address=0, size=1}})
assert(response[1].type == "ERROR")
-- Drop partial input on disconnect; the next connection starts at a fresh line.
feed(conn, '[{"type":')
conn.callbacks.error()
assert(conn.closed)
conn = connect()
feed(conn, "VERSION\n")
assert(conn.output == "1\n")
-- A lock must not keep polling a dead client forever.
request(conn, {{type="LOCK"}})
frame()
assert(conn.closed)
conn = connect()
frame()
assert(not conn.closed)
now = now + 6
frame()
assert(conn.closed)
conn = connect()
feed(conn, 'broken-json\n')
assert(conn.closed)
conn = connect()
feed(conn, string.rep("x", 1024 * 1024 + 1))
assert(conn.closed)
-- All ports occupied: never bind 43060 and never listen on a failed socket.
for port = 43055, 43059 do busy_ports[port] = true end
bound_ports = {}
listener = nil
frame()
assert(#bound_ports == 5 and bound_ports[5] == 43059 and listener == nil)
print("PASS: mGBA adapter host contract (mock memory and sockets only)")
