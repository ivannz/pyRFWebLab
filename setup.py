from distutils.core import setup, Extension

setup(
    name="rfweblab",
    version="0.1",
    description="""A pythonic interface to RFWebLab dpdchallenge.com.""",
    license="MIT License",
    author="Ivan Nazarov",
    author_email="ivan.nazarov@skolkovotech.ru",
    packages=[
        "rfweblab",
    ],
    requires=["numpy", "urllib3"]
)
