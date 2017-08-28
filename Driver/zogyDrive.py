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
def zogyDrive(obsDir, obsList, template, templateDQ, configDir, filterName):
    
    # if template MEF hasn't already been split into obsDir/Template, do so
    try:
        templateDir = path.join(obsDir,'Template')
        os.makedirs(templateDir)
    except OSError:
        pass

    if prepMEF(templateDir, template, templateDir, GAIN=4.0, RDNOISE=5.0, PIXSCALE=0.263, SEEING=1.0, FILTNAME=filterName):
        print 'Can\'t process template file ', template
        return

    if prepMEF(templateDir, templateDQ, templateDir, GAIN=4.0, RDNOISE=5.0, PIXSCALE=0.263, SEEING=1.0, FILTNAME=filterName):
        print 'Can\'t process template DQ file ', templateDQ
        return

    tempDir = path.join(obsDir,'tmp')
    mkdirNoSquawk(tempDir)
    
    for obs in obsList:
        # MEFsplit obs and dq image into tempDir
        # move each individual obs and dq image into appropriate ccd_nn subdirectory
        # run zogy.optimal_subtraction() on each image/dq ccd pair
        # copy fits headers into S.fits and rename S_nn.fits (and for other images)
        # MEFjoin the S_nn.fits images (and similar)
        image = obs[0]
        dq = obs[1]

        indx = image.rindex('.fits')
        imageID = image[0:indx]
        indx = template.rindex('.fits')
        templateID = template[0:indx]
        indx = templateDQ.rindex('.fits')
        templateDqID = templateDQ[0:indx]
        indx = dq.rindex('.fits')
        dqID = dq[0:indx]
        
        mkdirNoSquawk(path.join(obsDir,imageID))
        if prepMEF(obsDir, image, tempDir, GAIN=4.0, RDNOISE=5.0, PIXSCALE=0.263, SEEING=1.0, FILTNAME=filterName):
            print 'Error processing image ', image

        imagePat = re.compile(imageID + r'_(\d+).fits')
        imageList = os.listdir(tempDir)
        for i in imageList:
            mtch = imagePat.match(i)
            if mtch:
                ccdID = mtch.group(1)
                imageDestDir = path.join(obsDir, imageID, 'ccd_'+ccdID)
                mkdirNoSquawk(imageDestDir)
                os.renames(path.join(tempDir,i), path.join(imageDestDir, i))

        mkdirNoSquawk(tempDir)
        if prepMEF(obsDir, dq, tempDir, GAIN=4.0, RDNOISE=5.0, PIXSCALE=0.263, SEEING=1.0, FILTNAME=filterName):
           print 'Error processing dq image ', dq

        imagePat = re.compile(dqID + r'_(\d+).fits')
        imageList = os.listdir(tempDir)
        for i in imageList:
            mtch = imagePat.match(i)
            if mtch:
                ccdID = mtch.group(1)
                imageDestDir = path.join(obsDir, imageID, 'ccd_'+ccdID)
                mkdirNoSquawk(imageDestDir)
                os.renames(path.join(tempDir,i), path.join(imageDestDir, i))

        imageDirList = os.listdir(path.join(obsDir,imageID))
        for d in imageDirList:
            imageList = os.listdir(path.join(obsDir,imageID,d))
            newPat = re.compile(imageID + r'_(\d+).fits')
            newDqPat = re.compile(dqID + r'_(\d+).fits')

            for i in imageList:
                mtch = newPat.match(i)
                mtchDq = newDqPat.match(i)
                if mtch:
                    ccdID = mtch.group(1)
                    basePath = path.join(obsDir, imageID, 'ccd_'+ccdID)
                    newImage = path.join(basePath,i)
                    templateImage = templateID + '_' + ccdID + '.fits'
                    templateDqImage = templateDqID + '_' + ccdID + '.fits'
                    refImage = path.join(templateDir, templateImage)
                    refDqImage = path.join(templateDir, templateDqImage)
                    print newImage, refImage, refDqImage
                elif mtchDq:
                    ccdID = mtchDq.group(1)
                    basePath = path.join(obsDir, imageID, 'ccd_'+ccdID)
                    newDqImage = path.join(basePath,i)
                    print newDqImage
            if newImage is not None and refImage is not None and newDqImage is not None and refDqImage is not None:
                zogy.optimal_subtraction(newImage, refImage, use_existing_wcs=True, new_mask=newDqImage, ref_mask=refDqImage, telescope='Decam')

    return

def mkdirNoSquawk(dir):
    try:
        os.mkdir(dir)
    except OSError:
        pass
    
def prepMEF(srcDir, imageName, destDir, **kwargs):

    imagePath = path.join(srcDir, imageName)
    if not path.isfile(imagePath):
        print 'Image file not found'
        return True
    
    indx = imageName.rindex('.fits')
    imageRoot = imageName[0:indx]
    imageFilePat = re.compile(imageRoot + r'_\d+.fits')

    imageList = os.listdir(destDir)
    matched = False
    for t in imageList:
        if imageFilePat.match(t):
            matched = True
            break

    if not matched:
        MEFsplit(imagePath, destDir, **kwargs)

    return False
        
def MEFsplit(MEFname, outputDir, **kwargs):
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
        header.update(priHeader)
        data = hdu.data
        ccdnum = header['CCDNUM']
        outName = '%s/%s_%d.fits' % (outputDir, MEFfileBase, ccdnum)
        if kwargs is not None:
            for kw, value in kwargs.iteritems():
                header[kw] = value
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
