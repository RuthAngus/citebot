# citebot

![badge-img](https://img.shields.io/badge/Made%20at-%23AstroHackWeek-8063d5.svg?style=flat)

A helpful bot that tells you if you've missed citations in your astrophysics paper.

## Installation

To install the `citebot` script, run

```bash
pip install citebot
```

or

```bash
python setup.py install
```

in this directory to get the development version.

Most of the heavy lifting will be done using the [ads library](https://github.com/andycasey/ads) so you'll need to make sure that you have your ADS API key set up properly [by following the docs](https://ads.readthedocs.io/en/latest/).

## Usage

The assumption is that, if you're writing an astrophysics paper, you're probably using [NASA ADS](https://ui.adsabs.harvard.edu/), and *this code will only work if (at least some of) your BibTeX entries were exported by ADS*.
To get a list of recommended references, you can run

```bash
citebot /path/to/a/bibtex/file.bib
```

This will print a list of recommended citations to the terminal which is useful, but probably not exactly what you want.
Instead, the best way to use this is probably to include the `--upload` argument to convert the recommendations to an ADS personal library:

```bash
citebot /path/to/a/bibtex/file.bib --upload name_of_the_library --clobber
```

where the `--clobber` command will overwrite an existing library with the same name (without asking).
