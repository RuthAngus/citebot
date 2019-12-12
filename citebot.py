#!/usr/bin/env python
# -*- coding: utf-8 -*-

__all__ = ["get_bibcodes_for_bibtex_file", "CiteBot"]

import os
import re
import ads
import time
import tqdm
import shelve
import requests
from collections import Counter


def get_bibcodes_for_bibtex_file(filename):
    txt = open(filename, "r").read()
    urls = re.findall(r"adsurl\s*=\s*(.+),", txt, re.I)
    bibcodes = (url.strip("{}").split("/")[-1] for url in urls)
    return [b for b in sorted(bibcodes) if len(b)]


class CiteBot:
    def __init__(
        self,
        article_cache=None,
        ref_cache=None,
        cite_cache=None,
        cache_file=None,
        cache_ttl=86400,
    ):
        self.article_cache = {} if article_cache is None else article_cache
        self.ref_cache = {} if ref_cache is None else ref_cache
        self.cite_cache = {} if cite_cache is None else cite_cache
        if cache_file is None:
            cache_file = os.path.expanduser("~/.citebot")
        self.cache_file = cache_file
        self.cache_ttl = cache_ttl

    def _get_all_bibcodes(self, q):
        limits = {"remaining": "unknown"}

        with shelve.open(self.cache_file) as cache:
            if q in cache:
                result = cache[q]
                if result["expires"] >= time.time():
                    return result["bibcodes"], limits
                else:
                    del cache[q]

        sort = "bibcode desc"
        query = ads.SearchQuery(q=q, sort=sort, fl=["bibcode", "title"])
        bibcodes = []
        while True:
            query.execute()
            limits = query.response.get_ratelimits()
            new_bibcodes = []
            for a in query.response.articles:
                code = a.bibcode
                self.article_cache[code] = dict(a.items())
                new_bibcodes.append(a.bibcode)
            bibcodes += new_bibcodes
            if len(new_bibcodes) < 50:
                break

            # Check rate limits
            if int(limits["remaining"]) <= 0:
                wait = int(limits["reset"]) - time.time()
                print(
                    "Request has been rate limited. "
                    "Resets in {0} minutes".format(wait / 60.0)
                )
                time.sleep(wait)

        with shelve.open(self.cache_file) as cache:
            cache[q] = dict(
                expires=time.time() + self.cache_ttl, bibcodes=bibcodes
            )

        return bibcodes, limits

    def get_refs_and_cites(self, bibcode):
        limits = {}
        if bibcode not in self.ref_cache:
            self.ref_cache[bibcode], limits = self._get_all_bibcodes(
                "references(bibcode:{0})".format(bibcode)
            )
        if bibcode not in self.cite_cache:
            self.cite_cache[bibcode], limits = self._get_all_bibcodes(
                "citations(bibcode:{0})".format(bibcode)
            )
        return self.ref_cache[bibcode] + self.cite_cache[bibcode], limits

    def get_connections(self, bibcode_list):
        connections = []
        with tqdm.tqdm(bibcode_list) as t:
            for bibcode in t:
                t.set_description(bibcode)
                new_connections, limits = self.get_refs_and_cites(bibcode)
                connections += new_connections
                t.set_postfix(
                    num=len(connections), api_limit=limits["remaining"]
                )
        return connections

    def get_recommendations(self, bibcode_list, num=100):
        results = self.get_connections(bibcode_list)
        hist = Counter(results)
        hist = Counter(
            dict((k, hist[k]) for k in set(hist.keys()) - set(bibcode_list))
        )
        sorted_entries = [entry[0] for entry in hist.most_common(num)]
        return [
            self.article_cache.get(bib, {"bibcode": bib})
            for bib in sorted_entries
        ]

    def upload_recommendations(
        self, name, bibcode_list, num=100, clobber=False
    ):
        url = "https://api.adsabs.harvard.edu/v1/biblib/"
        token = ads.base.BaseQuery().token
        headers = {
            "Authorization": "Bearer {}".format(token),
            "User-Agent": "citebot",
            "Content-Type": "application/json",
        }

        recs = self.get_recommendations(bibcode_list, num=num)
        data = dict(name=name, bibcode=[bib["bibcode"] for bib in recs])

        # Try to create the library
        r = requests.post(url + "libraries", json=data, headers=headers)

        # If this fails, try to delete the library
        if r.status_code == 409:
            if not clobber:
                raise RuntimeError(
                    "The library '{0}' already exists. "
                    "Use 'clobber' to overwrite"
                )

            # Get the list of libraries
            r = requests.get(url + "libraries", headers=headers)
            r.raise_for_status()

            for lib in r.json().get("libraries", []):
                if lib["name"] == name:
                    print("deleting")
                    r = requests.delete(
                        url + "documents/{0}".format(lib["id"]),
                        headers=headers,
                    )
                    print(url + "documents/{0}".format(lib["id"]))
                    r.raise_for_status()
                    break

            # Try again to create the library
            r = requests.post(url + "libraries", json=data, headers=headers)

        r.raise_for_status()

        return recs, r.json().get("id", None)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Get citation recommendations for your astrophysics paper"
    )
    parser.add_argument(
        "bibtex_file", type=str, help="the path to a BibTeX file"
    )
    parser.add_argument(
        "--num",
        "-n",
        type=int,
        default=100,
        help="the number of recommendations to provide",
    )
    parser.add_argument(
        "--upload",
        "-u",
        type=str,
        default=None,
        help="upload the recommendations as a personal library with this name",
    )
    parser.add_argument(
        "--clobber",
        "-c",
        action="store_true",
        help="overwrite any existing personal library with the same name",
    )

    args = parser.parse_args()

    bibcodes = get_bibcodes_for_bibtex_file(args.bibtex_file)

    citebot = CiteBot()
    if args.upload is not None:
        recs, lib_id = citebot.upload_recommendations(
            args.upload, bibcodes, num=args.num
        )
        print(
            "Library uploaded to: "
            "https://ui.adsabs.harvard.edu/user/libraries/{0}".format(lib_id)
        )

    else:
        recs = citebot.get_recommendations(bibcodes, num=args.num)

        for rec in recs:
            print(
                "https://ui.adsabs.harvard.edu/abs/{0}".format(rec["bibcode"])
            )


if __name__ == "__main__":
    main()
