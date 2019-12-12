from setuptools import setup


def get_long_description():
    with open("README.md", encoding="utf8") as ld_file:
        return ld_file.read()


setup(
    name="citebot",
    use_scm_version=True,
    description="Get citation recommendations for your astrophysics paper",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    author="Ruth Angus & Dan Foreman-Mackey",
    author_email="foreman.mackey@gmail.com",
    url="https://github.com/RuthAngus/citebot",
    license="MIT",
    py_modules=["citebot"],
    zip_safe=False,
    install_requires=["requests", "ads"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
    ],
    entry_points={"console_scripts": ["citebot=citebot:main"]},
)
