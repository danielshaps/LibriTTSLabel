#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import re
from collections import namedtuple
from functools import partial

import click

import speechlabels as sl

MAINTIER = "phones"
IGNORE_WORDS = {""}
EMPTY_SEGMENT = ""

Segment = namedtuple("Segment", ["start", "end", "label"])


def get_segments(boundslist, start=None, end=None, ignore=None):
    for ((segstart, _), (segend, seglab)) in zip([[0.0, ""]] + boundslist, boundslist):
        seglab = seglab.strip()
        segstart = float(segstart)
        segend = float(segend)
        if ignore is not None and seglab in ignore:
            continue
        if start is not None and (segstart < start or segend < start):
            continue
        if end is not None and (segstart > end or segend > end):
            break
        yield Segment(segstart, segend, seglab)


def syllabify_textgrid(words, phones, phoneset, syllabify):
    utt_syls = []
    for word in get_segments(words, ignore=IGNORE_WORDS):
        word_phones = list(get_segments(phones, word.start, word.end))
        if any(ph.label not in phoneset for ph in word_phones):
            continue
        try:
            syllables = syllabify([ph.label for ph in word_phones])
        except:
            print(f"WARNING: Failed to syllabify '{word.label}': {word_phones}",
                  file=sys.stderr)
            continue
        phone_idx = 0
        for syl in syllables:
            utt_syls.append(Segment(word_phones[phone_idx].start,
                                    word_phones[phone_idx + len(syl) - 1].end,
                                    "_".join([word.label, "-".join(syl)])))
            phone_idx += len(syl)
    return utt_syls


def segs_to_tier(segs, empty=EMPTY_SEGMENT):
    tier = []
    prev_t = 0.0
    for seg in segs:
        if seg.start != prev_t:
            tier.append([str(seg.start), empty])
        tier.append([str(seg.end), seg.label])
        prev_t = seg.end
    return tier
    

def cleansplit(e, sep="-"):
    return e.strip(sep).split(sep) if e else []


def syllabify(phones, vowels, vwls_re, cons_re):
    phonestr = "-".join(phones)
    vwls = [ph for ph in phones if ph in vowels]
    conseqs = vwls_re.split(phonestr)
    cns = []
    for conseq in conseqs:
        if not conseq.startswith("-"):
            cns.append(cleansplit(conseq))
            continue
        if not conseq.endswith("-"):
            cns.append(cleansplit(conseq))
            continue
        m = cons_re.match(conseq)
        cns.extend(cleansplit(e) for e in m.groups())
    syls = []
    for i, v in enumerate(vwls):
        syls.append(cns[i*2] + [v] + cns[i*2+1])
    return syls


@click.command()
@click.option("--phoneset", default="etc/phoneset.txt", type=click.File())
@click.option("--vowels", default="etc/vowels.txt", type=click.File())
@click.option("--onsets", default="etc/onsets.txt", type=click.File())
@click.option("--output_dir", type=click.Path())
@click.argument("input_files", nargs=-1, required=True, type=click.Path(exists=True))
def main(phoneset, vowels, onsets, output_dir, input_files):
    phoneset = set(e for e in phoneset.read().split() if e)
    vowels = set(e for e in vowels.read().split() if e)
    onsets = set(e for e in onsets.read().split() if e)
    consonants = set(ph for ph in phoneset if not ph in vowels)

    vwls_re = re.compile("|".join(vowels))
    onst = "|".join("-" + o for o in onsets)
    ofst = "|".join("-" + c for c in consonants)
    cons_re = re.compile(f"((?:{ofst})*?)((?:{onst}){{0,1}})-$")

    sylf = partial(syllabify,
                   vowels=vowels,
                   vwls_re=vwls_re,
                   cons_re=cons_re)

    print(f"INFO: Processing {len(input_files)} input files...", file=sys.stderr)
    for i, fpath in enumerate(input_files):
        if (i + 1) % 100 == 0:
            print(f"INFO: Processed {i + 1} files...", file=sys.stderr)
        tiers, _ = sl.Utterance.readTextgrid(fpath, maintier=MAINTIER)
        syltier = segs_to_tier(syllabify_textgrid(tiers["words"], tiers["phones"], phoneset, sylf))
        tiers["syllables"] = syltier + [[tiers["phones"][-1][0], EMPTY_SEGMENT]]
        if output_dir is not None:
            outfname = os.path.join(output_dir, os.path.basename(fpath))
            sl.Utterance.writeTextgrid(outfname, tiers)


if __name__ == "__main__":
    main()
