import re
import urllib3

from zipfile import ZipFile
from io import BytesIO

from .serialize import deserialize, serialize, checksum


class ResultNotReadyError(urllib3.exceptions.HTTPError):
    pass


def subimt(object):
    url = """http://dpdcompetition.com/rfweblab/matlab/upload.php"""

    http = urllib3.PoolManager()

    form = {"myFile": ("dummy.dat", checksum(serialize(object)),)}
    response = http.request_encode_body(
        "POST", url, encode_multipart=True,
        fields=form, retries=100, timeout=3.0)

    match = re.search(rb"(output_[^\.]+\.dat)", response.data)
    return str(match.group(1), "utf8")


def fetch(filename):
    base = """http://dpdcompetition.com/rfweblab/matlab/files"""

    http = urllib3.PoolManager()
    fresult = f"{base}/{filename[:-3]}zip"

    # see if a file exists
    check = http.request("HEAD", fresult)
    if check.status != 200:
        raise ResultNotReadyError("Not found")

    # GET the file from the server
    resp = http.request('GET', fresult, preload_content=True)
    with ZipFile(BytesIO(resp.data), mode="r") as zin:
        with zin.open(filename) as fin:
            data = fin.read()

    return deserialize(data, pos=0, encoding="utf8")
