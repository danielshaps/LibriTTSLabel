#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Slice potentially large wave files given a TextGrid...
"""

__author__ = "Daniel van Niekerk"
__email__ = "dvn.demitasse@gmail.com"
__date__ = "2011-10"

import os, sys; sys.path.append(os.environ.get("PYTTS_PYTHONPATH"))
###

import wave

import speechlabels as sl

NONE_LABEL = ""


def tg2labelsampleranges(tg, tier, samplerate, prefix):
    chunks = []
    starttime = 0.0
    for i, entry in enumerate(tg.tiers[tier]):
        if entry[1] != NONE_LABEL: #nonempty
            chunks.append(("_".join([prefix, str(i).zfill(4), entry[1]]), int(starttime*samplerate), int(float(entry[0])*samplerate)))
        starttime = float(entry[0])
    return chunks


def basename(fn):
    return ".".join(os.path.basename(fn).split(".")[:-1])


if __name__ == "__main__":
    wavfn = sys.argv[1]
    tgfn = sys.argv[2]
    outd = sys.argv[3]
    tier = sys.argv[4]
    
    #open wavfile
    wavfh = wave.open(wavfn)
    wavparms = wavfh.getparams()
    samplerate = wavparms[2]
    #open textgrid
    tg = sl.Utterance(tgfn, tier)
    
    chunks = tg2labelsampleranges(tg, tier, samplerate, prefix=basename(tgfn))

    for label, startsample, endsample in chunks:
        print("SAVING:", label)
        wavfh.setpos(startsample)
        chunk = wavfh.readframes(endsample - startsample)
        outwavfh = wave.open(os.path.join(outd, label + ".wav"), "w")
        outwavfh.setparams(wavparms)
        outwavfh.writeframes(chunk)
        outwavfh.close()
