import struct
import numpy as np


dtype_to_fmt = {   
    np.dtype('float64'): "d",
    np.dtype('float32'): "f",
    np.dtype('bool'):    "?",
    np.dtype('int8'):    "b", np.dtype('uint8'):   "B",
    np.dtype('int16'):   "h", np.dtype('uint16'):  "H",
    np.dtype('int32'):   "i", np.dtype('uint32'):  "I",
    np.dtype('int64'):   "q", np.dtype('uint64'):  "Q",
}

fmt_to_dtype = {v: k for k, v in dtype_to_fmt.items()}


def unpack(fmt, data, pos=0):
    return struct.unpack_from(fmt, data, pos), pos + struct.calcsize(fmt)


def pack_shape(obj, fmt="I"):
    assert len(obj) <= 255
    return struct.pack(f"<B{len(obj)}{fmt}", len(obj), *obj)


def unpack_shape(data, pos=0, fmt="I"):
    (n_length,), pos = unpack("B", data, pos)
    vector, pos = unpack(f"<{n_length}{fmt}", data, pos)
    return vector, pos


def pack_string(obj, encoding="ascii"):
    b_str = bytes(obj, encoding=encoding)
    return struct.pack("<I", len(b_str)) + b_str


def unpack_string(data, pos=0, encoding="ascii"):
    (n_size,), pos = unpack("<I", data, pos)
    (string,), pos = unpack(f"<{n_size}s", data, pos)
    return str(string, encoding=encoding), pos


def pack_fields(obj, encoding="ascii"):
    assert len(obj) <= 255
    assert all(isinstance(el, str) for el in obj)

    b_fields = (pack_string(str, encoding) for str in obj)
    return struct.pack(f"B", len(obj)) + b"".join(b_fields)


def unpack_fields(data, pos=0, encoding="ascii"):
    strings = []
    (n_strings,), pos = unpack("B", data, pos)
    for _ in range(n_strings):
        field, pos = unpack_string(data, pos, encoding=encoding)
        strings.append(field)

    return tuple(strings), pos


def pack_ndarray(obj):
    head = pack_shape(obj.shape, fmt="I")
    body = struct.pack(f"<{obj.size}{dtype_to_fmt[obj.dtype]}", *obj.ravel())

    return head + body


def unpack_ndarray(data, dtype, pos=0):
    shape, pos = unpack_shape(data, pos)

    arr = np.empty(shape, dtype=dtype, order="C")
    arr.flat[:], pos = unpack(
        f"<{arr.size}{dtype_to_fmt[dtype]}", data, pos)

    return arr, pos
