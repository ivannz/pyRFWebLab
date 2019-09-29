import os
import re
import urllib3

from zipfile import ZipFile
from tempfile import TemporaryDirectory


class ResultNotReadyError(urllib3.exceptions.HTTPError):
    pass


def submit(data):
    url = """http://dpdcompetition.com/rfweblab/matlab/upload.php"""

    http = urllib3.PoolManager()

    form = {"myFile": ("dummy.dat", data,)}
    response = http.request_encode_body(
        "POST", url, encode_multipart=True,
        fields=form, retries=10, timeout=3.0)

    match = re.search(rb"(output_[^\.]+\.dat)", response.data)
    return str(match.group(1), "utf8")


def is_available(filename):
    base = """http://dpdcompetition.com/rfweblab/matlab/files"""

    http = urllib3.PoolManager()

    check = http.request("HEAD", f"{base}/{filename[:-3]}zip")
    return check.status == 200


def download(filename, path):
    base = """http://dpdcompetition.com/rfweblab/matlab/files"""
    assert os.path.isdir(path)

    http = urllib3.PoolManager()

    fname = f"{filename[:-3]}zip"
    local = os.path.join(path, fname)

    # GET the file from the server
    resp = http.request("GET", f"{base}/{fname}", preload_content=False)
    try:
        with open(local, "wb") as fin:
            for chunk in resp.stream(65536):
                fin.write(chunk)

    finally:
        resp.release_conn()

    return local


def fetch(filename):
    if not is_available(filename):
        raise ResultNotReadyError("Not found")

    with TemporaryDirectory() as tmpdir:
        local = download(filename, path=tmpdir)

        with ZipFile(local, mode="r") as zin:
            with zin.open(filename) as fin:
                data = fin.read()

        return data

