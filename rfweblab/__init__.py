import numpy as np

from .retry import retry_on

from .serialize import deserialize, serialize, checksum
from .interface import submit, fetch
from .interface import ResultNotReadyError


def validate(signal, rmsin=None):
    signal = np.asarray(signal).astype(np.complex).ravel()

    assert len(signal) <= 1_000_000, "x is too long, cutting to 1 000 000 samples."
    assert 1_000 <= len(signal), "x must be more than 1000 samples."
    assert np.all(np.isfinite(signal)), "Invalid IQ Data. Data contain NaN or Inf value(s)"

    nrm = np.linalg.norm(signal) / np.sqrt(len(signal))
    if rmsin is None:
        rmsin = 10 * np.log10(nrm**2 / 50) + 30

    peak = max(np.max(abs(signal.real)), np.max(abs(signal.imag)))
    if peak > 0:
        signal = signal / peak

    papr = 20 * np.log10(max(abs(signal)) * peak / nrm)

    assert papr < 20, "Signal PAPR too high."
    assert papr + rmsin < -8, "Peak input power too high."
    assert rmsin + 0.77 * papr < -8, "rms input power too high."

    return signal, rmsin


def send(signal, rmsin):
    """Send 1d signal to the RFWebLab"""
    assert isinstance(signal, np.ndarray)
    assert signal.ndim == 1

    data = serialize({
        "Client_version": np.float32(1.1),  # cannot use float64 -- old client
        "OpMode": "A5Z6UNud",
        "PowerLevel": float(rmsin),
        "SA_Samples": len(signal),
        "Re_data": np.real(signal)[np.newaxis],
        "Im_data": np.imag(signal)[np.newaxis],
    })
    return submit(checksum(data) + data)


@retry_on(ResultNotReadyError, tries=20, delay=3, growth=1.5, verbose=True)
def receive(filename):
    data = fetch(filename)
    result, pos = deserialize(data, pos=0, encoding="utf8")
    return result


def rfweblab(signal, rmsin=None):
    # GA_call()
    filename = send(*validate(signal, rmsin))
    result = {"filename": filename}
    try:
        reponse = receive(filename)

    except:
        raise RuntimeError(f"Could not receive `{filename}`.")

    status, error = reponse["status"], reponse["error_hanlde"]
    result.update({
        "status": int(status),
        "error": message(error),
    })

    if status > 0:
        result.update({
            "y": np.ravel(reponse["b3_re"] + 1j * reponse["b3_im"]),
            "rmsout": reponse["RMS_out"],
            "Idc": reponse["DCmeas"]["Id"],
            "Vdc": reponse["DCmeas"]["Vd"],
        })

    return result


def message(error):
    if error == -999000:
        return "OK"

    elif error == -999001:
        return "Measurement System failure. Please repeat the measurement."

    elif error == -999002:
        return "Invalid input data. Please verify your settings."

    elif error == -999003:
        return "You are using an old Client version. Please update."

    elif error == -999004:
        return "Corrupted data transfer. Please repeat the measurement."
