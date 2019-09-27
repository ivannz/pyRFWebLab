import numpy as np

from .retry import retry_on

from .serialize import deserialize, serialize, checksum
from .interface import submit, fetch
from .interface import ResultNotReadyError


def rfweblab(signal):
    return recieve(send(signal))


def send(signal):
    """Send 1d signal to the RFWebLab"""
    assert isinstance(signal, np.ndarray)
    assert signal.ndim == 1

    signal = signal.astype(np.complex)
    data = serialize({
        "Client_version": np.float32(1.1),
        "OpMode": "A5Z6UNud",
        "PowerLevel": 1.0,
        "SA_Samples": len(signal),
        "Re_data": signal.real[np.newaxis],
        "Im_data": signal.imag[np.newaxis],
    })
    return submit(checksum(data) + data)


@retry_on(ResultNotReadyError, tries=20, delay=3, growth=1.5, verbose=True)
def recieve(filename):
    data = fetch(filename)
    result, pos = deserialize(data, pos=0, encoding="utf8")
    return result


def message(status):
    if status == -999000:
        return "OK"

    elif status == -999001:
        return "Measurement System failure. Please repeat the measurement."

    elif status == -999002:
        return "Invalid input data. Please verify your settings."

    elif status == -999003:
        return "You are using an old Client version. Please update."

    elif status == -999004:
        return "Corrupted data transfer. Please repeat the measurement."
