import numpy as np
from spectral_cube import SpectralCube
from uvcombine import (feather_simple, spectral_regrid,
                       spectral_smooth_and_downsample, fourier_combine_cubes)
from astropy import units as u
from astropy import log

singledish_fn = 'CSO_c20kms_hnco.fits'
feathered_fn = 'Feathered.hnco.image.fits'
interferometer_fn = 'SMA_c20kms.hnco.image.fits'


tpoutfn = 'CSO_TP_regridded.fits'
outfilename = 'CSO_plus_SMA_feather_test.fits'

# intcube = interferometer cube
intcube = SpectralCube.read(interferometer_fn).with_spectral_unit(u.GHz)

# Convert the interferometer cube from Jy/beam to K (common unit with
# singledish data)
if hasattr(intcube, 'beam'):
    jtok = intcube.beam.jtok(intcube.spectral_axis).value
else:
    jtok = np.array([bm.jtok(x).value for bm,x in zip(intcube.beams,
                                                      intcube.spectral_axis)])

intcube_k = intcube.to(u.K, intcube.beam.jtok_equiv(intcube.spectral_axis[:,None,None]))

# for cropping
minghz, maxghz = intcube.spectral_extrema

# tpcube = total power cube
tpcube = SpectralCube.read(singledish_fn).with_spectral_unit(u.GHz)

crop_channels = sorted((tpcube.closest_spectral_channel(minghz),
                        tpcube.closest_spectral_channel(maxghz)))
crop_channels[0] = crop_channels[0]-1 if crop_channels[0] > 0 else 0
crop_channels[1] = crop_channels[1]+1
tpcube = tpcube[crop_channels[0]:crop_channels[1]]
log.debug("Read tp freq")
tpcube_k = tpcube.to(u.K, tpcube.beam.jtok_equiv(tpcube.spectral_axis[:,None,None]))
log.debug("Converted TP to K")
# Smooth the total power cube
# determine smooth factor kw = kernel width
kw = np.abs((intcube.spectral_axis.diff().mean() / tpcube_k.spectral_axis.diff().mean()).decompose().value)
log.debug("determined kernel kw={0}".format(kw))

tpcube_k_ds_hdu = spectral_smooth_and_downsample(tpcube_k, kw)

tpdscube = SpectralCube.read(tpcube_k_ds_hdu)
tpkrg = spectral_regrid(tpdscube, intcube.spectral_axis)
log.debug("done regridding")

cube_tpkrg = SpectralCube.read(tpkrg)
cube_tpkrg.with_spectral_unit(u.km/u.s,
                              rest_value=intcube.wcs.wcs.restfrq*u.Hz,
                              velocity_convention='radio').write(tpoutfn,
                                                                 overwrite=True)
print("Single dish beam = {0}".format(cube_tpkrg.beam))

# intermediate work: test that a single frame has been properly combined
frq = intcube.wcs.wcs.restfrq*u.Hz * (1-13/3e5) # approximately 13 kms
closestchan = intcube.closest_spectral_channel(frq)
im = intcube[closestchan] * jtok[closestchan]
sdim = cube_tpkrg[cube_tpkrg.closest_spectral_channel(frq)]
im.write('singleframe_cubek_13kms.fits', overwrite=True)
sdim.write('singleframe_tpcube_k_rg_13kms.fits', overwrite=True)
combohdu, hdu2 = feather_simple(im.hdu, sdim.hdu, return_regridded_lores=True, return_hdu=True)
combohdu.writeto('singleframe_TP_7m_12m_feather_65kms.fits', clobber=True)
hdu2.writeto('singleframe_tpcube_k_spatialandspectralregrid_65kms.fits', clobber=True)


# "feather" the cubes together based on the low-resolution beam size
combhdu = fourier_combine_cubes(intcube_k, cube_tpkrg, return_hdu=True,
                                lowresfwhm=cube_tpkrg.beam.major)
log.info("Fourier combination completed.")
# restore all of the NaN values from the interferometer data back to NaN
combhdu.data[intcube.mask.exclude()] = np.nan
combhdu.writeto(outfilename, clobber=True)
log.info("Wrote file to {0}".format(outfilename))

# convert the cube spectral axis to km/s (...probably unnecessary now)
combcube = SpectralCube.read(combhdu).with_spectral_unit(u.km/u.s,
                                                         velocity_convention='radio')
combcube.write(outfilename, overwrite=True)
