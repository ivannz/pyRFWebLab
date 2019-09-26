from distutils.core import setup, Extension

setup(
    name="dpdchallenge",
    version="0.1",
    description="""A pythonic interface to dpdchallenge.com.""",
    license="MIT License",
    author="Ivan Nazarov",
    author_email="ivan.nazarov@skolkovotech.ru",
    packages=[
        "dpdchallenge",
    ],
    requires=["numpy", "urllib3"]
)
