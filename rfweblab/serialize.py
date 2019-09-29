import struct
import hashlib
import numpy as np

# ordered like in MATALB reference script
fmt_dtype_pairs = [
    ("d", 'float64'),  #  0 double
    ("f", 'float32'),  #  1 single
    ("?", 'bool'),     #  2 logical
    ("c", '<S1'),      #  3 string  (stored as bytes, handled specially)
    ("b", 'int8'),     #  4 signed int8
    ("B", 'uint8'),    #  5 unsigned int8
    ("h", 'int16'),    #  6 signed int16 (short)
    ("H", 'uint16'),   #  7 unsigned int16 (short)
    ("i", 'int32'),    #  8 signed int32
    ("I", 'uint32'),   #  9 unsigned int32
    ("q", 'int64'),    # 10 signed int64 (long)
    ("Q", 'uint64'),   # 11 unsigned int64 (long)
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

    # collapse explicit char arrays into byte strings
    if dtype == np.dtype("<S1"):
        *head, tail = shape
        arr = arr.view(f"<S{tail}").reshape(head)

    return arr, pos


def checksum(data):
    # prepend an MD5-integrity check
    prefix = struct.pack("<5sQQQ", b"uint8", 2, len(data), 1)

    md5 = hashlib.new("md5", data=prefix)
    md5.update(data)

    return md5.digest()


def validate(data, pos=0):
    (chkhash,), pos = unpack("16s", data, pos)
    assert checksum(data[pos:]) == chkhash

    return data, pos


def serialize(obj):
    if isinstance(obj, dict):
        # represent dict to a scalar struct (1x1)
        dtype = np.dtype([(f, object) for f in obj.keys()])
        return serialize(np.array([[tuple(obj.values())]], dtype=dtype))

    elif isinstance(obj, list):
        # represent a list as a cell array:
        # BUG: type/shape similar ndarrays in nested lists are misinterpreted
        return serialize(np.array(obj, dtype=object))

    elif isinstance(obj, (float, int, np.floating, np.integer)):
        # represent numeric scalars as 1x1 arrays
        return serialize(np.array([[obj]]))

    elif isinstance(obj, (str, bytes)):
        # get a bytes encoding of a string
        obj = obj.encode() if isinstance(obj, str) else obj

        # (bug) byte arrays with zero bytes are note packed
        # return serialize(np.frombuffer(obj, "<S1")[np.newaxis])

        # emulate 1xlen ndarray of char
        head = struct.pack("B", dtype_to_cls[np.dtype("<S1")])
        head += pack_shape([1, len(obj)], fmt="I")
        return head + struct.pack(f"<{len(obj)}s", obj)

    elif not isinstance(obj, np.ndarray):
        raise TypeError(f"`{obj}` Unrecognized type `{type(obj).__name__}`")

    # if the data is of one of the basic types
    if obj.dtype.names is not None:
        # this is a structured array, i.e. array of `named` tuples
        head = struct.pack("B", 255)
        head += pack_fields(obj.dtype.names)
        head += pack_shape(obj.shape, fmt="I")
        return head + b"".join(serialize(el[fl])
                               for el in obj.ravel()
                               for fl in obj.dtype.names)

    elif obj.dtype.kind == "O":
        # this is an unstructured array of objects
        head = struct.pack("B", 254)
        head += pack_shape(obj.shape, fmt="I")
        return head + b"".join(map(serialize, obj.ravel()))

    elif obj.dtype not in dtype_to_fmt:
        raise TypeError(f"Unrecognized data type `{obj.dtype}` in {obj}")

    head = struct.pack("B", dtype_to_cls[obj.dtype])
    return head + pack_ndarray(obj)


def deserialize(data, pos=0, encoding="utf8"):
    (b_cls,), pos = unpack("B", data, pos)
    if b_cls == 255:
        # a struct can be a scalar, i.e. [1, 1] or an ndarray
        #  (of equally sized elements)
        fields, pos = unpack_fields(data, pos, encoding)
        shape, pos = unpack_shape(data, pos, fmt="I")

        dtype = np.dtype([(f, "O") for f in fields])
        output = np.empty(shape, dtype=dtype, order="C")
        for el in range(output.size):
            for fl in fields:
                output.flat[el][fl], pos = deserialize(data, pos, encoding)

        if output.size == 1:
            output = {f: output[f].item() for f in output.dtype.names}

    elif b_cls == 254:
        shape, pos = unpack_shape(data, pos, fmt="I")

        output = np.empty(shape, dtype=object, order="C")
        for el in range(output.size):
            output.flat[el], pos = deserialize(data, pos, encoding)

    else:
        output, pos = unpack_ndarray(data, cls_to_dtype[b_cls], pos)
        if output.dtype.kind == "S":  # `S` is for special
            output = str(output.item(), encoding=encoding)

        elif output.size == 1:
            # return a scalar instead of redundant 1x1x...x1 arrays
            output = output.item()

    return output, pos
