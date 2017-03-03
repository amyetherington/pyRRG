import os as os
import numpy as np
import glob as glob
import astro_tools as at
import pickle as pkl
import measure_moms as measure_moms
import star_galaxy_separation as sgs
import pyfits as py
import calc_shear as cs
import psf_cor as psf
import ipdb as pdb
import plot_shears as plot
import ellipse_to_reg as etr
def main(  infile, hst_filter=None,
            data_dir='./',
            sex_files=None,
            psf_model_dir=None,
            expThresh = 3, 
            noisy=False, 
            nonstop=True, 
            fits_cat=None, 
            mag_cut=[0.,40.], 
            signal_noise_cut=4.4,
            size_cut=[3., 30.],
            min_rad=6.,
            mult=2.):
    '''
    ;PURPOSE : RUN RRG OVER THE GIVEN CLUSTER AND FILTER, CAN TAKE
    ;          IN MULTIPLE EXPOSURES
    ;          
    ;          THEN FILTERS THE CATALOGUE AND USES ONLY THOSE
    ;          GALAXIES WHICH HAVE EXPTHRESH NUMBER OF EXPOSURES
    ;          OVER THEM AND OUTPUTS .RRG FILE WHICH IS THE CAT
    ;          IN X-Y COORDINATESD
    
    ;          AND THEN RUNS ELLCONVERTER WHICH INVOKES THE MASKS
    ;          IN THE DS9 FILE, MASK.REG AND OUTPUTS A .LENSTOOL
    ;          FILE WHICH IS READY TO BE PUT ITO LENSTOOL
    
    
    ;INPUTS : CLUSTER_NAME : THE NAME OF THE CLUSTER
    ;         FILTER : THE HST FILTER USED
    
    ;KEYWORDS : EXPTHRESH : THE MINIMUM NUMBER OF EXPOSURES ONE
    ;                       GALAXY MUST HAVE BEFORE ALLOWED TO
    ;                       BE IN SAMPLE; DEFAULT = 2 TO PREVENT
    ;                       EDGE GALAXIES IN THE DITHER TO BE INCL.
    ;           FILTER2 : THE SECOND FILTER USED TO GET THE RED_SEQUENCE
    ;                     IF NOT SET THEN RED_SEQUENCE IS NOT FOUND
    ;           NOISY : RUN THE SOURCE EXTRACTION USING THE OLD AND
    ;                   NOT THE MATHILDE NEW ONE THAT IS MROE SENSITIVE
    ;           NONSTOP : DO NOT PAUSE FOR CONFIRATION I WANT TO CONTINUE
    ;           FITS_CAT :  MAKE A CATALOGUE THAT IS IN FITS FORMAT
    ;           MAG_CUT : MAGNITUDE CUTS
    

    ;TO DO : 
    ;        2. CHANGE SUCH THAT FUNCTIONS DONT CONSISTENTLY READ
    ;           FITS IMAGES AND SLOW THIGNS DOWN
    
    '''
    if hst_filter is None:
        hst_filter='F814W'
    wavelength=''.join([  s for s in hst_filter if s.isdigit()])
                   
    #SET GLOBAL PARAMETERS TO BE USED FOR ALL
    if sex_files is None:
        sex_files='sex_files/'
        
    if  psf_model_dir is None:
        psf_model_dir='psf_lib/'

        
    dirs = directories(data_dir,  sex_files, psf_model_dir+'/'+str(wavelength)+'/' )

    field=dirs.data_dir+infile

    if not os.path.isfile( field):
        raise ValueError("%s not found" % field)
  
    Exposures = glob.glob( dirs.data_dir+'/j*.fits ')
    nExposures = len(Exposures)
  
    if nExposures  < expThresh:
        expThresh = nExposures
        print 'WARNING: Low number of exposures'
    
  

    # Define survey parameters
    #------------------------------------------
    #Now as keywords

 
    sex_catalogue = field[:-5]+"_sex.cat"
    
    #Find objects and measure their raw shapes
    if not os.path.isfile( sex_catalogue):
        weight_file = infile[:-8]+'wht.fits'
        sources = at.source_extract( infile, weight_file,
                                         outfile=sex_catalogue )
    else:
        sources = py.open( sex_catalogue )[1].data

     
        
    print sex_catalogue
  
  
    uncorrected_moments_cat = field[:-5]+"_uncor.cat"
    
    if not os.path.isfile(uncorrected_moments_cat):
        measure_moms.measure_moms( infile,
                                   sex_catalogue,
                                   uncorrected_moments_cat,
                                    min_rad=min_rad, mult=mult)

    uncorrected_moments = py.open( uncorrected_moments_cat )[1].data
 

    
    galaxies, stars = sgs.star_galaxy_separation( uncorrected_moments,
                                                  savefile='galStar.locus' )

    
    n_stars=len(stars)
  
    corrected_moments_cat = field[:-5]+"_cor.cat"

    #Correct for the PSF
    if not os.path.isfile(corrected_moments_cat):
         psf.psf_cor( uncorrected_moments_cat,
                    corrected_moments_cat,
                    infile, wavelength,
                    mult=1, min_rad=min_rad, chip=1,
                    constantpsf=0, mscale=0, 
                    num_exposures=1, order=3,
                    n_chip=2, dataDir=data_dir)
    

    corrected_moments = py.open( corrected_moments_cat )[1].data

    #Correct zerpoint for the stacked num exposures
  
    sheared_cat = field[:-5]+".shears"
    
    cs.calc_shear( corrected_moments, galaxies,
                   sheared_cat, 
                    min_rad=min_rad, mult=mult,
                    signal_noise_cut=signal_noise_cut,
                    size_cut=size_cut,
                    mag_cut=mag_cut,
                    dataDir=data_dir)
    

    
    plot.plot_shears( sheared_cat )
    etr.ellipse_to_reg( sheared_cat )
    '''
  
  ellconverter, cluster_name, filter



'''

class directories( dict ):

    def __init__( self, data_dir, sex_files, psf_mode_dir):
        self.__dict__['sex_files'] = sex_files
        self.__dict__['data_dir'] = data_dir
        self.__dict__['psf_mode_dir'] = psf_mode_dir
        self.write_dirs()

    def write_dirs( self ):
        file_obj = open('directories.cat',"wb")
        file_obj.write("DATA_DIR: %s \n" %self.data_dir)
        file_obj.write("SEX_FILES: %s \n" %self.sex_files)
        file_obj.write("PSF_MODEL_DIR: %s \n" %self.psf_mode_dir)
      
    def keys(self):
        return self.__dict__.keys()

    def __getitem__(self, key): 
        return self.__dict__[key]
