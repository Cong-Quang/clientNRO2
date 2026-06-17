import socket
import struct
import threading
import time
from typing import Optional
from logger import log


class Message:
    def __init__(self, command: int, data: Optional[bytes] = None):
        self.command = command & 0xFF
        self._data = bytearray()

        if data is not None:
            self._data = bytearray(data)

    def writer(self):
        return self

    def reader(self):
        return self

    def getData(self) -> Optional[bytes]:
        return bytes(self._data) if self._data else None

    def cleanup(self):
        self._data = bytearray()

    def writeByte(self, value: int):
        self._data.append(value & 0xFF)

    def writeChar(self, value: int):
        self.writeByte(0)
        self.writeByte(value)

    def writeShort(self, value: int):
        self._data.extend(struct.pack('>h', value))

    def writeUnsignedShort(self, value: int):
        self._data.extend(struct.pack('>H', value))

    def writeInt(self, value: int):
        self._data.extend(struct.pack('>i', value))

    def writeLong(self, value: int):
        self._data.extend(struct.pack('>q', value))

    def writeBoolean(self, value: bool):
        self.writeByte(1 if value else 0)

    def writeUTF(self, value: str):
        encoded = value.encode('utf-8')
        self.writeShort(len(encoded))
        self._data.extend(encoded)

    def writeSByte(self, value: int):
        self._data.append(value & 0xFF)

    def _ensure_data(self):
        if not hasattr(self, '_pos'):
            self._pos = 0
            if not hasattr(self, '_buf'):
                self._buf = bytes(self._data)

    def readByte(self) -> int:
        self._ensure_data()
        val = self._buf[self._pos]
        self._pos += 1
        if val > 127:
            val -= 256
        return val

    def readSByte(self) -> int:
        return self.readByte()

    def readUnsignedByte(self) -> int:
        self._ensure_data()
        val = self._buf[self._pos]
        self._pos += 1
        return val

    def readShort(self) -> int:
        self._ensure_data()
        val = struct.unpack_from('>h', self._buf, self._pos)[0]
        self._pos += 2
        return val

    def readUnsignedShort(self) -> int:
        self._ensure_data()
        val = struct.unpack_from('>H', self._buf, self._pos)[0]
        self._pos += 2
        return val

    def readInt(self) -> int:
        self._ensure_data()
        val = struct.unpack_from('>i', self._buf, self._pos)[0]
        self._pos += 4
        return val

    def readLong(self) -> int:
        self._ensure_data()
        val = struct.unpack_from('>q', self._buf, self._pos)[0]
        self._pos += 8
        return val

    def readInt3Byte(self) -> int:
        self._ensure_data()
        val = (self._buf[self._pos] << 16) | (self._buf[self._pos + 1] << 8) | self._buf[self._pos + 2]
        if val > 0x7FFFFF:
            val -= 0x1000000
        self._pos += 3
        return val

    def readBoolean(self) -> bool:
        return self.readByte() != 0

    def readBool(self) -> bool:
        return self.readBoolean()

    def readUTF(self) -> str:
        length = self.readUnsignedShort()
        self._ensure_data()
        val = self._buf[self._pos:self._pos + length].decode('utf-8', errors='replace')
        self._pos += length
        return val

    def readStringUTF(self) -> str:
        return self.readUTF()

    def available(self) -> int:
        self._ensure_data()
        return len(self._buf) - self._pos

    def read(self, size: int = -1) -> bytes:
        self._ensure_data()
        if size == -1:
            remaining = self.available()
            data = self._buf[self._pos:]
            self._pos = len(self._buf)
            return data
        data = self._buf[self._pos:self._pos + size]
        self._pos += size
        return data


class NRoSession:
    def __init__(self, host: str = '127.0.0.1', port: int = 14445):
        self.host = host
        self.port = port
        self.sock: Optional[socket.socket] = None
        self.connected = False
        self.getKeyComplete = False
        self.key: list[int] = []
        self.curR = 0
        self.curW = 0

        self.message_handler = None
        self._send_lock = threading.RLock()
        self._recv_buffer = bytearray()

    def setHandler(self, handler):
        self.message_handler = handler

    def connect(self):
        if self.connected:
            return
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(10)
        self.sock.connect((self.host, self.port))
        self.sock.settimeout(5)
        self.connected = True
        self.getKeyComplete = False
        self.key = []
        self.curR = 0
        self.curW = 0

        self._send_raw(Message(-27))

        recv_thread = threading.Thread(target=self._recv_loop, daemon=True)
        recv_thread.start()

    def _read_key(self, b: int) -> int:
        result = (self.key[self.curR] & 0xFF) ^ (b & 0xFF)
        self.curR = (self.curR + 1) % len(self.key)
        return result

    def _write_key(self, b: int) -> int:
        result = (self.key[self.curW] & 0xFF) ^ (b & 0xFF)
        self.curW = (self.curW + 1) % len(self.key)
        return result

    def _recv_loop(self):
        while self.connected:
            try:
                msg = self._read_message()
                if msg is None:
                    break
                if msg.command == -27 & 0xFF:
                    self._handle_key(msg)
                elif self.message_handler:
                    try:
                        self.message_handler.onMessage(msg)
                    except Exception as e:
                        log.error("NETWORK", f"Handler error: {e}")
            except ConnectionError:
                break
            except Exception as e:
                log.error("NETWORK", f"Recv error: {e}")
                break
        if self.connected:
            self.connected = False
            if self.message_handler:
                self.message_handler.onDisconnected(True)

    _3BYTE_LEN_CMDS = frozenset([-32, -66, -74, 11, -67, -87, 66, 12])

    def _read_message(self) -> Optional[Message]:
        try:
            cmd_byte = self._recv_exact(1)[0]
            if self.getKeyComplete:
                cmd_byte = self._read_key(cmd_byte)

            cmd = cmd_byte
            if cmd > 127:
                cmd -= 256

            if cmd in self._3BYTE_LEN_CMDS:
                raw_len = self._recv_exact(3)
                if self.getKeyComplete:
                    b1 = self._read_key(raw_len[0])
                    b2 = self._read_key(raw_len[1])
                    b3 = self._read_key(raw_len[2])
                else:
                    b1 = raw_len[0]
                    b2 = raw_len[1]
                    b3 = raw_len[2]
                def signed(v):
                    return v if v <= 127 else v - 256
                b1 = signed(b1) + 128
                b2 = signed(b2) + 128
                b3 = signed(b3) + 128
                length = ((b3 << 8) | b2) << 8 | b1
            else:
                raw_len = self._recv_exact(2)
                if self.getKeyComplete:
                    b2 = self._read_key(raw_len[0])
                    b3 = self._read_key(raw_len[1])
                    length = ((b2 & 0xFF) << 8) | (b3 & 0xFF)
                else:
                    length = struct.unpack('>H', raw_len)[0]

            data = bytearray(self._recv_exact(length))

            if self.getKeyComplete:
                for i in range(len(data)):
                    data[i] = self._read_key(data[i])

            return Message(cmd, bytes(data))
        except Exception:
            return None

    def _recv_exact(self, n: int) -> bytes:
        buf = bytearray()
        while len(buf) < n:
            try:
                chunk = self.sock.recv(n - len(buf))
            except socket.timeout:
                if not self.connected:
                    raise ConnectionError("Disconnected")
                continue
            if not chunk:
                raise ConnectionError("Connection closed")
            buf.extend(chunk)
        return bytes(buf)

    def sendMessage(self, msg: Message):
        with self._send_lock:
            self._send_raw(msg)

    def _send_raw(self, msg: Message):
        try:
            data = msg.getData()
            with self._send_lock:
                if self.getKeyComplete:
                    cmd_byte = self._write_key(msg.command)
                else:
                    cmd_byte = msg.command

                self.sock.sendall(bytes([cmd_byte]))

                if data:
                    if self.getKeyComplete:
                        enc_len_hi = self._write_key((len(data) >> 8) & 0xFF)
                        enc_len_lo = self._write_key(len(data) & 0xFF)
                        self.sock.sendall(bytes([enc_len_hi, enc_len_lo]))
                    else:
                        self.sock.sendall(struct.pack('>H', len(data)))

                    if self.getKeyComplete:
                        enc_data = bytearray()
                        for b in data:
                            enc_data.append(self._write_key(b))
                        self.sock.sendall(bytes(enc_data))
                    else:
                        self.sock.sendall(data)
                else:
                    if self.getKeyComplete:
                        enc_len_hi = self._write_key(0)
                        enc_len_lo = self._write_key(0)
                        self.sock.sendall(bytes([enc_len_hi, enc_len_lo]))
                    else:
                        self.sock.sendall(struct.pack('>H', 0))
        except Exception as e:
            log.error("NETWORK", f"Send error: cmd={msg.command}: {e}")

    def _handle_key(self, msg: Message):
        b = msg.readByte()
        self.key = [0] * b
        for i in range(b):
            self.key[i] = msg.readByte() & 0xFF
        for j in range(len(self.key) - 1):
            self.key[j + 1] ^= self.key[j]
        self.getKeyComplete = True

        if self.message_handler:
            self.message_handler.onConnectOK(True)

        if msg.available() > 0:
            try:
                ip2 = msg.readUTF()
                port2 = msg.readInt()
                is_connect2 = msg.readByte() != 0
                log.info("NETWORK", f"Key len={b}, ip2={ip2}, port2={port2}, connect2={is_connect2}")
            except Exception:
                pass
        else:
            log.info("NETWORK", f"Key received, len={b}")

    def isConnected(self) -> bool:
        return self.connected

    def close(self):
        self.connected = False
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
            self.sock = None
