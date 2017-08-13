"""
Run ZOGY for a list of observation numbers in the current directory, which
is assumed to contain observations of a single field and filter.

For each observation, split out the individual CCDs from the MEF, run ZOGY on
each, and put all ZOGY output in ./ccdXX_output

When all CCD's have been processed, build in ./output MEFs for difference image,
significance image, etc.
"""

import numpy as np
import pyfits as pf
import os
import os.path as path
import re

def zogyDrive(obslist, templateMEF, configDir):
    return

def MEFsplit(MEFname, outputDir):
    hdulist = pf.open(MEFname)
    priHeader = hdulist[0].header
    numext = priHeader['NEXTEND']
    print numext

    MEFfileName = path.basename(MEFname)
    MEFfileBase = MEFfileName.replace('.fits','')
    for n in range(numext):
        hdu = hdulist[n+1]
        header = hdu.header
        data = hdu.data
        outName = '%s/%s_%d.fits' % (outputDir, MEFfileBase, n)
        pf.writeto(outName, data, header=header)

    return

def MEFjoin(inputDir, reCCD, outputMEF):
    pat = re.compile(reCCD)
    fileList = os.listdir(inputDir)
    hdulist = pf.HDUList()
    hdulist.append(pf.PrimaryHDU())
    for f in fileList:
        if pat.match(f):
            print f
            hdu = pf.open(path.join(inputDir,f))
            hdulist.append(hdu[0])
    hdulist.writeto(outputMEF)
    return

