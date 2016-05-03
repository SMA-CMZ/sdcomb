#
# set up parameters
#

# load some libraries
import re
import shutil
import os
from time import ctime

print 'Script started at ' + ctime()

# set up some variables
LineID = 'CH_3OH'
RestFrequency = '218.44005GHz'      # must be in GHz
SidebandID = 'lsb'
SourceID = 'G1.602+0.018'
Source = 'G1.602'

#SDImage = 'cutout_G0.11-0.08_219to221_bl.fits'
SDImage = 'cutout_G1.63-0.02_217to219_bl.fits'
SourceLocation = 'J2000 17h49m19.125 -27d33m28.766'
ImageSize = [300, 300]
NumberIterations = 10000
CleaningThreshold = '250mJy'

VelocityResolution = '1.1km/s'     # must be in km/s
StartVelocity = '-200km/s'
NumberChannels = 360

CellSize = '1arcsec'

# copy uvfits file into imaging directory

Compact = '../../' + SourceID + '/' + Source + '.c.' + LineID + '.uvfits'
Subcompact = '../../' + SourceID + '/' + Source + '.sc.' + LineID + '.uvfits'
shutil.copy2(Compact, os.getcwd())
shutil.copy2(Subcompact, os.getcwd())

print 'copied ' + Source + '.c.' + LineID + '.uvfits' + ' and ' + Source + '.sc.' + LineID + '.uvfits to imaging directory'

# import uvfits file into CASA

os.system('rm -rf c.' + LineID + '.ms')
os.system('rm -rf sc.' + LineID + '.ms')

importuvfits(fitsfile = Source + '.c.' + LineID + '.uvfits', vis='c.' + LineID + '.ms')
importuvfits(fitsfile = Source + '.sc.' + LineID + '.uvfits', vis='sc.' + LineID + '.ms')

print 'imported uvfits files into CASA'

# merge uvfits files and export

os.system('rm -rf ' + LineID + '.ms')
os.path.exists(LineID + '.uvfits') and os.remove(LineID + '.uvfits')

myfiles=['c.' + LineID + '.ms', 'sc.' + LineID + '.ms']
concat(vis=myfiles, concatvis = LineID + '.ms', timesort=True, freqtol='0.5GHz')
exportuvfits(vis = LineID + '.ms', fitsfile = LineID + '.uvfits')

print 'merged CASA files and exported to uvfits'

# make directories if non existent and move uvfits
uvfits='../data_uv/uv_fits/' + LineID
uvcasa='../data_uv/uv_casa/' + LineID

if not os.path.exists(uvfits): os.makedirs(uvfits)
if not os.path.exists(uvcasa): os.makedirs(uvcasa)

fitsfile = LineID + '.uvfits'
newfile = SourceID + '_' + SidebandID + '.uvfits'
folder = '../data_uv/uv_fits/' + LineID + '/'

if not os.path.exists(folder): os.makedirs(folder)

os.rename(fitsfile, newfile)
print 'renamed ' + fitsfile + ' as ' + newfile

os.path.exists(folder + newfile) and os.remove(folder + newfile)

shutil.move(newfile, folder)

print 'moved ' + newfile + ' to ' + folder

print "set-up done, let's search " + SourceID + ' for ' + LineID + '!'

# set some more variables

SizeSingleDishMeter = 12.
SDEfficiency = 0.75                # main beam efficiency to scale to Jansky
SDCutoffScaleMeter = 6.            # UV cutoff scale for Feather


# some additional conversions
RestFrequencyGHz = float(RestFrequency.replace('GHz', ''))
VelocityResolutionKMS = float(VelocityResolution.replace('km/s', ''))
FrequencyResolution = str(333.564095*VelocityResolutionKMS*(RestFrequencyGHz/100.)) + 'kHz'
CellSizeArcsec = float(CellSize.replace('arcsec', ''))
SingleDishResolutionArcsec = 74.88 / (RestFrequencyGHz/100.) / \
                             (SizeSingleDishMeter/10.)

#
# prepare visibilities
#

# ingest UVFITS file into CASA
UVFileNaming = LineID + '/' + SourceID + '_' + SidebandID
os.system('rm -rf ../data_uv/uv_casa/' + UVFileNaming + '.ms')
importuvfits('../data_uv/uv_fits/' + UVFileNaming + '.uvfits', \
             vis = '../data_uv/uv_casa/' + UVFileNaming + '.ms')

print 'Imported SMA data into CASA'


# create a simple dirty image
os.system('rm -rf deconvolved*')
clean(vis = '../data_uv/uv_casa/' + UVFileNaming + '.ms',
     imagename = 'deconvolved',
     spw='',
     restfreq = RestFrequency,
     imagermode = 'mosaic',
     mode = 'velocity',
     outframe='lsrk',
     width = VelocityResolution,
     start = StartVelocity,
     nchan = NumberChannels,
     interactive = False,
     imsize = ImageSize,
     cell = CellSize,
     phasecenter = SourceLocation,
     weighting = 'natural',
     niter = 0,
     threshold = '20mJy',
     usescratch = True)

print 'Made dirty image of SMA data - "deconvoled.image"'

#
# prepare single-dish data
#

# convert APEX map
importfits(fitsimage = '../data_sd/' + SDImage,
           imagename='apex.image',
           overwrite=True)
imhead('apex.image',
       mode='put',
       hdkey='telescope', hdvalue='ALMA')
imhead('apex.image',
       mode='put',
       hdkey='restfreq', hdvalue=RestFrequency)

print 'Imported APEX data - "apex.image"'


# smooth the velocity axis of the APEX data
SDCellSizeX = str(abs(imhead('apex.image', mode='get', hdkey='cdelt1')['value'] * \
                      180.*3600./pi)) + 'arcsec'
SDCellSizeY = str(abs(imhead('apex.image', mode='get', hdkey='cdelt2')['value'] * \
                      180.*3600./pi)) + 'arcsec'

os.system('rm -rf apex_vsmooth.image')
ia.open('apex.image')
im2 = ia.sepconvolve(outfile='apex_vsmooth.image',
                     axes=[0,1,2], types=['box','box','box'],
                     widths=[SDCellSizeX,SDCellSizeY,FrequencyResolution],
                     overwrite=True)
im2.done()
ia.close()

print 'Smoothed the velocity axis of the APEX data - "apex_vsmooth.image"'


# beat the stokes axis into proper format
os.system('rm -rf apex_vsmooth_stokes.image')
ia.open('apex_vsmooth.image')
im2 = ia.regrid(dropdeg=True)
im3 = im2.adddegaxes(outfile='apex_vsmooth_stokes.image', overwrite=True,
                     stokes='I')
im2.done()
im3.done()
ia.close()

print 'Beaten Stokes axis into the proper format - "apex_vsmooth_stokes.image"'

imhead('apex_vsmooth_stokes.image')

os.system('rm -rf apex_trans.image')
imtrans(imagename='apex_vsmooth_stokes.image',
        outfile='apex_trans.image',
        order='0132')

print 'Reordered image axes - "apex_trans.image"'


# regrid single-dish image
os.system('rm -rf apex_trans_regrid.image')
ReferenceFrame = imregrid('deconvolved.image', template='get')
imregrid(imagename='apex_trans.image',
         template=ReferenceFrame,
         output='apex_trans_regrid.image',
         asvelocity=True,
         interpolation='linear',
         overwrite=True)

print 'Regridded the APEX data - "apex_trans_regrid"'


# flux conversion scaling for single-dish image
JyperKelvin = 0.817 * (RestFrequencyGHz/100.)**2. * \
              (SingleDishResolutionArcsec/10.)**2.
FactorJyperPixel = CellSizeArcsec**2. / \
                   (1.133 * SingleDishResolutionArcsec**2.)
ConversionFactor = JyperKelvin * FactorJyperPixel / SDEfficiency

os.system('rm -rf apex_trans_regrid_scaled.image')
im1 = ia.imagecalc(outfile='apex_trans_regrid_scaled.image',
                   pixels=str(ConversionFactor)+'*apex_trans_regrid.image',
                   overwrite=True)
im1.done()
ia.close()

imhead('apex_trans_regrid_scaled.image',
       mode='put',
       hdkey='bunit', hdvalue='Jy/pixel')

print 'Scaled brightness unit to Jy/pixel - "apex_trans_regrid_scaled.image"'


# correct single-dish image for the primary beam sensitivity
os.system('rm -rf apex_trans_regrid_scaled_pbcor.image')
immath(outfile='apex_trans_regrid_scaled_pbcor.image',
       imagename=['deconvolved.flux',
                  'apex_trans_regrid_scaled.image'],
       mode='evalexpr',expr='IM0*IM1')
imhead('apex_trans_regrid_scaled_pbcor.image',
       mode='put',
       hdkey='bunit', hdvalue='Jy/pixel')
imhead('apex_trans_regrid_scaled_pbcor.image',
       mode='put',
       hdkey='bmaj', hdvalue=str(SingleDishResolutionArcsec)+'arcsec')
imhead('apex_trans_regrid_scaled_pbcor.image',
       mode='put',
       hdkey='bmin', hdvalue=str(SingleDishResolutionArcsec)+'arcsec')
imhead('apex_trans_regrid_scaled_pbcor.image',
       mode='put',
       hdkey='bpa', hdvalue='0deg')

print 'Corrected APEX data for the primary beam sensitivity - "apex_trans_regrid_scaled_pbcor.image"'


# remove blanking for single-dish data
os.system('rm -rf apex_trans_regrid_scaled_pbcor_unmasked.image')
os.system('cp -r apex_trans_regrid_scaled_pbcor.image ' +
          'apex_trans_regrid_scaled_pbcor_unmasked.image')
ia.open('apex_trans_regrid_scaled_pbcor_unmasked.image')
ia.replacemaskedpixels(0., update=True)
ia.close()

print 'Removed the masked pixels and set to 0 - "apex_trans_regrid_scaled_pbcor_unmasked.image"'


# remove negative values in single-dish image
os.system('rm -rf apex_trans_regrid_scaled_pbcor_unmasked_noneg.image')
immath(outfile='apex_trans_regrid_scaled_pbcor_unmasked_noneg.image',
   imagename=['apex_trans_regrid_scaled_pbcor_unmasked.image'],
   mode='evalexpr',expr='iif(IM0 >= 0.00, IM0, 0.0)')

print 'Removed negative values from APEX data - "apex_trans_regrid_scaled_pbcor_unmasked_noneg.image"'

#
# do the deconvolution via CLEAN
#

# do a coarse cleaning
os.system('rm -rf deconvolved-sdinput*')
clean(vis = '../data_uv/uv_casa/' + UVFileNaming + '.ms',
      modelimage = 'apex_trans_regrid_scaled_pbcor_unmasked_noneg.image',
      imagename = 'deconvolved-sdinput',
      multiscale = [0,5,10,15,20],
      spw='',
      restfreq = RestFrequency,
      imagermode = 'mosaic',
      mode = 'velocity',
      outframe='lsrk',
      width = VelocityResolution,
      start = StartVelocity,
      nchan = NumberChannels,
      interactive = False,
      imsize = ImageSize,
      cell = CellSize,
      phasecenter = SourceLocation,
      weighting = 'natural',
      niter = 10,
      cyclefactor = 5.,
      threshold = CleaningThreshold,
      usescratch = True)

print 'Done initial coarse cleaning, non-interactive - "deconvolved-sdinput"'


# remove negative intensities in model
os.system('mv deconvolved-sdinput.model deconvolved-sdinput-orig.model')
immath(outfile='deconvolved-sdinput.model',
   imagename=['deconvolved-sdinput-orig.model'],
   mode='evalexpr',expr='iif(IM0 >= 0.00, IM0, 0.0)')

print 'Removed negative values in model - "deconvolved-sdinput.model"'


# continue with finer cleaning
clean(vis = '../data_uv/uv_casa/' + UVFileNaming + '.ms',
      imagename = 'deconvolved-sdinput',
      multiscale = [0,5,10,15,20],
      spw='',
      restfreq = RestFrequency,
      imagermode = 'mosaic',
      mode = 'velocity',
      outframe='lsrk',
      width = VelocityResolution,
      start = StartVelocity,
      nchan = NumberChannels,
      interactive = True,
      imsize = ImageSize,
      cell = CellSize,
      phasecenter = SourceLocation,
      weighting = 'natural',
      niter = NumberIterations,
      cyclefactor = 5.,
      threshold = CleaningThreshold,
      usescratch = True)

print 'Continue with finer cleaning, interactive - "deconvolved-sdinput"'


# unmask interferometer data for feathering
os.system('rm -rf deconvolved-sdinput-unmasked.image')
os.system('cp -r deconvolved-sdinput.image deconvolved-sdinput-unmasked.image')
ia.open('deconvolved-sdinput-unmasked.image')
ia.replacemaskedpixels(0., update=True)
ia.close()

print 'Removed the masked pixels and set to 0 - "deconvolved-sdinput-unmasked.image"'

#
# do the deconvolution via CLEAN
#

# do a coarse cleaning
os.system('rm -rf deconvolved-sdinput*')
clean(vis = '../data_uv/uv_casa/' + UVFileNaming + '.ms',
      modelimage = 'apex_trans_regrid_scaled_pbcor_unmasked_noneg.image',
      imagename = 'deconvolved-sdinput',
      multiscale = [0,5,10,15,20],
      spw='',
      restfreq = RestFrequency,
      imagermode = 'mosaic',
      mode = 'velocity',
      outframe='lsrk',
      width = VelocityResolution,
      start = StartVelocity,
      nchan = NumberChannels,
      interactive = False,
      imsize = ImageSize,
      cell = CellSize,
      phasecenter = SourceLocation,
      weighting = 'natural',
      niter = 10,
      cyclefactor = 5.,
      threshold = CleaningThreshold,
      usescratch = True)

print 'Done initial coarse cleaning, non-interactive - "deconvolved-sdinput"'


# remove negative intensities in model
os.system('mv deconvolved-sdinput.model deconvolved-sdinput-orig.model')
immath(outfile='deconvolved-sdinput.model',
   imagename=['deconvolved-sdinput-orig.model'],
   mode='evalexpr',expr='iif(IM0 >= 0.00, IM0, 0.0)')

print 'Removed negative values in model - "deconvolved-sdinput.model"'


# continue with finer cleaning
clean(vis = '../data_uv/uv_casa/' + UVFileNaming + '.ms',
      imagename = 'deconvolved-sdinput',
      multiscale = [0,5,10,15,20],
      spw='',
      restfreq = RestFrequency,
      imagermode = 'mosaic',
      mode = 'velocity',
      outframe='lsrk',
      width = VelocityResolution,
      start = StartVelocity,
      nchan = NumberChannels,
      interactive = True,
      imsize = ImageSize,
      cell = CellSize,
      phasecenter = SourceLocation,
      weighting = 'natural',
      niter = NumberIterations,
      cyclefactor = 5.,
      threshold = CleaningThreshold,
      usescratch = True)

print 'Continue with finer cleaning, interactive - "deconvolved-sdinput"'


# unmask interferometer data for feathering
os.system('rm -rf deconvolved-sdinput-unmasked.image')
os.system('cp -r deconvolved-sdinput.image deconvolved-sdinput-unmasked.image')
ia.open('deconvolved-sdinput-unmasked.image')
ia.replacemaskedpixels(0., update=True)
ia.close()

print 'Removed the masked pixels and set to 0 - "deconvolved-sdinput-unmasked.image"'

#
# feather the data
#

# feather the data
os.system('rm -rf deconvolved-combi.image')
feather(imagename = 'deconvolved-combi.image',
        highres = 'deconvolved-sdinput-unmasked.image',
        lowres = 'apex_trans_regrid_scaled_pbcor_unmasked.image',
        effdishdiam = SDCutoffScaleMeter,
        lowpassfiltersd = True)

print 'Feathered the data - "deconvolved-combi.image"'


# correct feathered image for primary beam scaling
os.system('rm -rf deconvolved-combi-pbcor.image')
immath(outfile='deconvolved-combi-pbcor.image',
       imagename=['deconvolved-combi.image',
                  'deconvolved-sdinput.flux'],
       mode='evalexpr',expr='IM0/IM1')
ia.open('deconvolved-combi-pbcor.image')
ia.replacemaskedpixels(0., update=True)
ia.close()

print 'Corrected feathered image for primary beam scaling - "deconvolved-combi-pbcor.image"'

#
# steps below only serve checking the data
#

# smooth the resulting image to the single-dish beam
os.system('rm -rf deconvolved-combi-pbcor-smo.image')
imsmooth(imagename = 'deconvolved-combi-pbcor.image',
         outfile = 'deconvolved-combi-pbcor-smo.image',
         kernel = 'gauss',
         major = str(SingleDishResolutionArcsec)+'arcsec',
         minor = str(SingleDishResolutionArcsec)+'arcsec',
         pa = '0deg',
         targetres = True)

print 'Smoothed the resulting image to the single-dish beam - "deconvolved-combi-pbcor-smo.image"'


# convert the smoothed image back to the Kelvin scale
os.system('rm -rf deconvolved-combi-pbcor-smo-Kelvin.image')
immath(outfile='deconvolved-combi-pbcor-smo-Kelvin.image',
       imagename=['deconvolved-combi-pbcor-smo.image'],
       mode='evalexpr',expr='IM0/'+str(JyperKelvin))
imhead('deconvolved-combi-pbcor-smo-Kelvin.image',
       mode='put',
       hdkey='bunit', hdvalue='K')

print 'Converted the smoothed image back to the Kelvin scale - "deconvolved-combi-pbcor-smo-Kelvin.image"'

if not os.path.exists('/data1/mgraham/' + Source + '/' + LineID): os.makedirs('/data1/mgraham/' + Source + '/' + LineID)

print 'All done!'

print "Don't forget to copy the output files to the new location otherwise they will be wiped the next time you run this code!"

print 'New location: /data1/mgraham/' + Source + '/' + LineID

print 'Script finished at ' + ctime()

