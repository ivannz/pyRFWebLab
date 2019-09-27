import struct
import hashlib
import numpy as np

# ordered like in MATALB reference script
fmt_dtype_pairs = [
    ("d", 'float64'),  # double
    ("f", 'float32'),  # single
    ("?", 'bool'),     # logical
    ("c", '<S1'),      # char
    ("b", 'int8'),     # signed int8
    ("B", 'uint8'),    # unsigned int8
    ("h", 'int16'),    # signed int16 (short)
    ("H", 'uint16'),   # unsigned int16 (short)
    ("i", 'int32'),    # signed int32
    ("I", 'uint32'),   # unsigned int32
    ("q", 'int64'),    # signed int64 (long)
    ("Q", 'uint64'),   # unsigned int64 (long)
]

dtype_to_fmt = {np.dtype(d): f for f, d in fmt_dtype_pairs}
fmt_to_dtype = {f: np.dtype(d) for f, d in fmt_dtype_pairs}

dtype_to_cls = {np.dtype(d): i for i, (f, d) in enumerate(fmt_dtype_pairs)}
cls_to_dtype = {i: np.dtype(d) for i, (f, d) in enumerate(fmt_dtype_pairs)}


def unpack(fmt, data, pos=0):
    return struct.unpack_from(fmt, data, pos), pos + struct.calcsize(fmt)


def pack_shape(obj, fmt="I"):
    assert len(obj) <= 255
    return struct.pack(f"<B{len(obj)}{fmt}", len(obj), *obj)


def unpack_shape(data, pos=0, fmt="I"):
    (n_length,), pos = unpack("B", data, pos)
    vector, pos = unpack(f"<{n_length}{fmt}", data, pos)
    return vector, pos


def pack_string(obj, encoding="utf8"):
    b_str = bytes(obj, encoding=encoding)
    return struct.pack("<I", len(b_str)) + b_str


def unpack_string(data, pos=0, encoding="utf8"):
    (n_size,), pos = unpack("<I", data, pos)
    (string,), pos = unpack(f"<{n_size}s", data, pos)
    return str(string, encoding=encoding), pos


def pack_fields(obj, encoding="utf8"):
    assert len(obj) <= 255
    assert all(isinstance(el, str) for el in obj)

    b_fields = (pack_string(str, encoding) for str in obj)
    return struct.pack(f"B", len(obj)) + b"".join(b_fields)


def unpack_fields(data, pos=0, encoding="utf8"):
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


def serialize(obj):
    if isinstance(obj, dict):
        head = struct.pack("B", 255)
        head += pack_fields(obj.keys())

        head += pack_shape([1], fmt="I")
        return head + b"".join(map(serialize, obj.values()))

    elif isinstance(obj, list):
        return serialize(np.array(obj, dtype=object))

    elif isinstance(obj, np.float):
        return serialize(np.array([[obj]], dtype=float))

    elif isinstance(obj, np.int):
        return serialize(np.array([[obj]], dtype=int))

    elif isinstance(obj, str):
        # convert a string to a 1d ndarray of char
        encoded = bytes(obj, encoding="utf8")
        return serialize(np.frombuffer(encoded, np.dtype("<S1")))

    assert isinstance(obj, np.ndarray), f"{obj} Unrecognized type `{type(obj)}`"
    if obj.dtype in dtype_to_fmt:
        head = struct.pack("B", dtype_to_cls[obj.dtype])
        return head + pack_ndarray(obj)

    head = struct.pack("B", 254)
    head += pack_shape(obj.shape, fmt="I")
    return head + b"".join(map(serialize, obj.ravel()))


def deserialize(data, pos=0, encoding="utf8", flatten=True):
    (b_cls,), pos = unpack("B", data, pos)
    if b_cls == 255:
        output = {}
        fields, pos = unpack_fields(data, pos, encoding=encoding)
        shape, pos = unpack_shape(data, pos, fmt="I")
        for field in fields:
            value, pos = deserialize(data, pos, encoding=encoding)
            output[field] = value

        return output, pos

    elif b_cls == 254:
        shape, pos = unpack_shape(data, pos, fmt="I")
        output = np.empty(shape, dtype=object, order="C")
        for i in range(output.size):
            output.flat[i], pos = deserialize(data, pos, encoding=encoding)

        if output.ndim == 1 and flatten:
            output = output.tolist()

        return output, pos

    output, pos = unpack_ndarray(data, cls_to_dtype[b_cls], pos)
    if b_cls == 3 and flatten:
        output = str(b"".join(output), encoding=encoding)

    return output, pos



def checksum(data):
    # prepend an MD5-integrity check
    md5 = hashlib.new("md5", data=data)
    return md5.digest() + data


def validate(data, pos=0):
    (checksum,), pos = unpack("<16s", data, pos)

    md5 = hashlib.new("md5", data[pos:]).digest()
    assert checksum == md5

    return data, pos
