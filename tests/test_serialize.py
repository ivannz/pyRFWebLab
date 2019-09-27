import pytest
import numpy as np


def test_ndarray():
    from rfweblab.serialize import pack_ndarray, unpack_ndarray
    from rfweblab.serialize import dtype_to_fmt

    arr = np.random.rand(10) - 0.5
    for dtype in dtype_to_fmt:
        if not dtype.isbuiltin:
            continue

        obj = arr.astype(dtype)
        enc = pack_ndarray(obj)
        dec, pos = unpack_ndarray(enc, dtype, pos=0)
        assert np.allclose(dec, obj)

    arr = np.random.randn(10, 2, 3, 7) * 10
    for dtype in dtype_to_fmt:
        if not dtype.isbuiltin:
            continue

        obj = arr.astype(dtype)
        enc = pack_ndarray(obj)
        dec, pos = unpack_ndarray(enc, dtype, pos=0)
        assert np.allclose(dec, obj)


def test_shape():
    from rfweblab.serialize import pack_shape, unpack_shape

    with pytest.raises(AssertionError):
        pack_shape(257 * [129], fmt="I")

    pack_shape(251 * [129], fmt="I")

    shape = tuple(range(255))
    assert shape == unpack_shape(pack_shape(shape, "I"), 0, "I")[0]
    assert shape == unpack_shape(pack_shape(shape, "B"), 0, "B")[0]


def test_fields():
    from rfweblab.serialize import pack_fields, unpack_fields

    with pytest.raises(AssertionError):
        fields = tuple(map(str, range(257)))
        pack_fields(fields)

    fields = tuple(map(str, range(255)))
    assert fields == unpack_fields(pack_fields(fields), 0)[0]


def test_serialization():
    from rfweblab.serialize import serialize, deserialize
    def sede_helper(obj, pos=0):
        res, pos = deserialize(serialize(obj), pos)
        return res

    assert sede_helper({}) == {}
    assert sede_helper([]) == []

    obj = "dfsg*N**N ( _URU(U£ª^¨º•˙ ∫ †ƒ#¶ªç€¶¢"
    assert sede_helper(obj) == obj

    obj = {"foo": "foo", "bar": 12_34_56, "baz": np.euler_gamma}
    assert sede_helper(obj) == obj

    obj = [["foo", "bar"], ["bar", "baz"]]
    assert (sede_helper(obj) == obj).all()
