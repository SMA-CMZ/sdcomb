import re
import shutil
import os
from time import ctime

LineID = 'CH_3CN'
RestFrequency = '220.74726GHz'      # must be in GHz
SidebandID = 'lsb'
Source = 'G1.602'

SizeSingleDishMeter = 12.
SDCutoffScaleMeter = 6.            # UV cutoff scale for Feather
RestFrequencyGHz = float(RestFrequency.replace('GHz', ''))
SingleDishResolutionArcsec = 74.88 / (RestFrequencyGHz/100.) / \
                             (SizeSingleDishMeter/10.)
JyperKelvin = 0.817 * (RestFrequencyGHz/100.)**2. * \
              (SingleDishResolutionArcsec/10.)**2.

os.system('rm -rf common-beam-sdinput.image')
imsmooth(imagename='deconvolved-sdinput-unmasked.image', kernel='common', outfile='common-beam-sdinput.image')

# feather the data
#

# feather the data
os.system('rm -rf deconvolved-combi.image')
feather(imagename = 'deconvolved-combi.image',
        highres = 'common-beam-sdinput.image',
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
