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

import zogy

"""
obsDir is the directory where images to process are to be found
obsList is a list of (image, dqmask) pairs
template is the name of the template file
configDir is the directory of config files (sex.config, etc) for ZOGY
"""
def zogyDrive(obsDir, obsList, template, templateDQ, configDir):
    # if template MEF hasn't already been split into obsDir/Template, do so
    try:
        templateDir = path.join(obsDir,'Template')
        os.makedirs(templateDir)
    except OSError:
        pass

    if prepMEF(templateDir, template, templateDir):
        print 'Can\'t process template file ', template
        return

    if prepMEF(templateDir, templateDQ, templateDir):
        print 'Can\'t process template DQ file ', templateDQ
        return

    tempDir = path.join(obsDir,'tmp')
    try:
        os.mkdir(tempDir)
    except OSError:
        pass
    
    for obs in obsList:
        # MEFsplit obs and dq image into tempDir
        # move each individual obs and dq image into appropriate ccd_nn subdirectory
        # run zogy.optimal_subtraction() on each image/dq ccd pair
        # copy fits headers into S.fits and rename S_nn.fits (and for other images)
        # MEFjoin the S_nn.fits images (and similar)
        image = obs[0]
        dq = obs[1]
#        imageID = re.xxx
        if prepMEF(obsDir, image, tempDir):
            print 'Error processing image ', image

        if prepMEF(obsDir, dq, tempDir):
           print 'Error processing dq image ', dq 

    return

def prepMEF(srcDir, imageName, destDir):

    imagePath = path.join(srcDir, imageName)
    if not path.isfile(imagePath):
        print 'Image file not found'
        return True
    
    indx = imageName.rindex('.fits')
    imageRoot = imageName[0:indx]
    imageFilePat = re.compile(imageRoot + r'_\d+.fits')

    imageList = os.listdir(srcDir)
    matched = False
    for t in imageList:
        if imageFilePat.match(t):
            matched = True
            break

    if not matched:
        MEFsplit(imagePath, destDir)

    return False
        
def MEFsplit(MEFname, outputDir):
    hdulist = pf.open(MEFname)
    priHeader = hdulist[0].header
    numext = priHeader['NEXTEND']
    print numext

    MEFfileName = path.basename(MEFname)
    MEFfileBase = MEFfileName.replace('.fits','')
    for n in range(numext):
        # use CCDNUM in name, not n
        hdu = hdulist[n+1]
        header = hdu.header
        data = hdu.data
        ccdnum = header['CCDNUM']
        outName = '%s/%s_%d.fits' % (outputDir, MEFfileBase, ccdnum)
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

def headerReplace(sourceImage, destImage):
    sourceHduList = pf.open(sourceImage)
    sourceHeader = sourceHduList[0].header

    destHduList = pf.open(destImage, mode='update')
    destData = destHduList[0].data
    pf.update(destImage, destData, sourceHeader)

    sourceHduList.close()

    return
