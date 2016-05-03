import os

print 'Source IDs: G0.068=0, G0.106=1, G0.145=1, G1.602=3'

ID=input('Enter Source ID: ')

Source=['G0.068','G0.106','G0.145','G1.602']
Source=Source[ID]

os.system('rm -rf ' + str(Source) + '_dust*')

Vis=['G0.068.cont.V1.ms', 'G0.106.cont.V2.ms', 'G0.145.cont.V2.ms', 'G1.602.cont.V2.ms']
Vis=Vis[ID]

Imagename=str(Source) + '_dust_sma_mg'

Threshold=['7mJy', '16mJy', '14mJy', '10mJy']
Threshold=Threshold[ID]

Phasecenter=['J2000, 17h46m05, -28d55m00', 'J2000, 17h46m11, -28d53m15', 'J2000, 17h46m18, -28d51m30', 'J2000, 17h49m20, -27d33m30']
Phasecenter=Phasecenter[ID]

clean(vis=Vis,
      imagename=Imagename,
      multiscale=[0,4,12],
      uvrange='',
      field='',
      spw='',
      niter=10000,
      gain=0.2,
      threshold=Threshold,
      psfmode='clark',
      imagermode='mosaic',
      scaletype='SAULT',
      ftmachine='mosaic',
      interactive=True,
      npercycle=20,
      imsize=360,
      cell='1.0arcsec',
      minpb=0.1,
      pbcor=False,
      weighting='natural',
      stokes='I',
      chaniter=False,
      phasecenter=Phasecenter)

beta=['1.75', '2.00', '2.25']
Factor=[0.52908, 0.50763, 0.48732]
Lowres=['CMZ_ring_1.1mm_J2000.image', 'CMZ_ring_1.1mm_J2000.image', 'CMZ_ring_1.1mm_J2000.image', '1.6deg_J2000.image']

feather(imagename=Source + '_dust_beta=1.75_mg.image', highres=Source + '_dust_sma_mg.image', lowres=Lowres[ID], sdfactor=Factor[0])

feather(imagename=Source + '_dust_final_mg.image', highres=Source + '_dust_sma_mg.image', lowres=Lowres[ID], sdfactor=Factor[1])

feather(imagename=Source + '_dust_beta=2.25_mg.image', highres=Source + '_dust_sma_mg.image', lowres=Lowres[ID], sdfactor=Factor[2])

imregrid(imagename=Source + '_dust_beta=1.75_mg.image', template='GALACTIC', output=Source + '_dust_beta=1.75_mg_gal.image')

imregrid(imagename=Source + '_dust_final_mg.image', template='GALACTIC', output=Source + '_dust_final_mg_gal.image')

imregrid(imagename=Source + '_dust_beta=2.25_mg.image', template='GALACTIC', output=Source + '_dust_beta=2.25_mg_gal.image')

exportfits(imagename=Source + '_dust_beta=1.75_mg.image', fitsimage=Source + '_dust_beta=1.75_mg.fits')

exportfits(imagename=Source + '_dust_final_mg.image', fitsimage=Source + '_dust_final_mg.fits')

exportfits(imagename=Source + '_dust_beta=2.25_mg.image', fitsimage=Source + '_dust_beta=2.25_mg.fits')

exportfits(imagename=Source + '_dust_beta=1.75_mg_gal.image', fitsimage=Source + '_dust_beta=1.75_mg_gal.fits')

exportfits(imagename=Source + '_dust_final_mg_gal.image', fitsimage=Source + '_dust_final_mg_gal.fits')

exportfits(imagename=Source + '_dust_beta=2.25_mg_gal.image', fitsimage=Source + '_dust_beta=2.25_mg_gal.fits')



