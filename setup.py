import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="OWNd",
    version="0.7.28",
    author="anotherjulien",
    url="https://github.com/anotherjulien/OWNd",
    author_email="yetanotherjulien@gmail.com",
    description="Python interface for the OpenWebNet protocol",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    install_requires=["aiohttp", "pytz", "python-dateutil"],
    python_requires='>=3.8',
)