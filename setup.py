import setuptools

with open("README.MD", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="midi-macro",
    version="0.1.1",
    author="David Vos",
    author_email="vosdavid2@gmail.com",
    description="Simple script to run python functions on midi input, using an optional gui",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://example.com/example",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.5',
)
