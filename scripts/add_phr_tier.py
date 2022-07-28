#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import re
from collections import namedtuple
from functools import partial

import click

import speechlabels as sl
from add_syl_tier import Segment, get_segments, segs_to_tier


PHNTIER = "phones"
EMPTYSEG = ""
SIL_PHNS = {"sp", "sil", ""}


@click.command()
@click.option("--outdir", type=click.Path())
@click.argument("input_files", nargs=-1, required=True, type=click.Path(exists=True))
def main(outdir, input_files):

    print(f"INFO: Processing {len(input_files)} input files...", file=sys.stderr)
    for i, fpath in enumerate(input_files):
        if (i + 1) % 100 == 0:
            print(f"INFO: Processed {i + 1} files...", file=sys.stderr)
        tiers, phntier = sl.Utterance.readTextgrid(fpath, maintier=PHNTIER)
        segs = list(get_segments(phntier))
        phrs = []
        in_phr = False
        for seg in segs:
            if seg.label in SIL_PHNS:
                in_phr = False
            else:
                if not in_phr:
                    in_phr = True
                    phrs.append(Segment(start=seg.start, end=seg.end, label="IP"))
                else:
                    lastp = phrs.pop()
                    phrs.append(Segment(start=lastp.start, end=seg.end, label="IP"))
        phrtier = segs_to_tier(phrs)
        if float(phrtier[-1][0]) != float(phntier[-1][0]):
            phrtier.append([phntier[-1][0], ""])
        tiers["iphrases"] = phrtier
        if outdir is not None:
            outfname = os.path.join(outdir, os.path.basename(fpath))
            sl.Utterance.writeTextgrid(outfname, tiers)

            

if __name__ == "__main__":
    main()
