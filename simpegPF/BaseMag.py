from SimPEG import Maps, Survey, Utils, np, sp
from scipy.constants import mu_0


class BaseMagSurvey(Survey.BaseSurvey):
    """Base Magnetics Survey"""

    rxLoc = None #: receiver locations
    rxType = None #: receiver type

    def __init__(self, **kwargs):
        Survey.BaseSurvey.__init__(self, **kwargs)


    def setBackgroundField(self, Inc, Dec, Btot):

        Bx = Btot*np.cos(Inc/180.*np.pi)*np.sin(Dec/180.*np.pi)
        By = Btot*np.cos(Inc/180.*np.pi)*np.cos(Dec/180.*np.pi)
        Bz = -Btot*np.sin(Inc/180.*np.pi)

        self.B0 = np.r_[Bx,By,Bz]

    @property
    def Qfx(self):
        if getattr(self, '_Qfx', None) is None:
            self._Qfx = self.prob.mesh.getInterpolationMat(self.rxLoc,'Fx')
        return self._Qfx

    @property
    def Qfy(self):
        if getattr(self, '_Qfy', None) is None:
            self._Qfy = self.prob.mesh.getInterpolationMat(self.rxLoc,'Fy')
        return self._Qfy

    @property
    def Qfz(self):
        if getattr(self, '_Qfz', None) is None:
            self._Qfz = self.prob.mesh.getInterpolationMat(self.rxLoc,'Fz')
        return self._Qfz

    def projectFields(self, u):
        """
            This function projects the fields onto the data space.

            Especially, here for we use total magnetic intensity (TMI) data,
            which is common in practice.

            First we project our B on to data location

            .. math::

                \mathbf{B}_{rec} = \mathbf{P} \mathbf{B}

            then we take the dot product between B and b_0

            .. math ::

                \\text{TMI} = \\vec{B}_s \cdot \hat{B}_0

        """
        #TODO: There can be some different tyes of data like |B| or B

        bfx = self.Qfx*u['B']
        bfy = self.Qfy*u['B']
        bfz = self.Qfz*u['B']

        # Generate unit vector
        B0 = self.prob.survey.B0
        Bot = np.sqrt(B0[0]**2+B0[1]**2+B0[2]**2)
        box = B0[0]/Bot
        boy = B0[1]/Bot
        boz = B0[2]/Bot

        # return bfx*box + bfx*boy + bfx*boz
        return bfx*box + bfy*boy + bfz*boz


    @Utils.count
    def projectFieldsDeriv(self, B):
        """
            This function projects the fields onto the data space.

            .. math::

                \\frac{\partial d_\\text{pred}}{\partial \mathbf{B}} = \mathbf{P}

            Especially, this function is for TMI data type

        """
        # Generate unit vector
        B0 = self.prob.survey.B0
        Bot = np.sqrt(B0[0]**2+B0[1]**2+B0[2]**2)
        box = B0[0]/Bot
        boy = B0[1]/Bot
        boz = B0[2]/Bot

        return self.Qfx*box+self.Qfy*boy+self.Qfz*boz


    def projectFieldsAsVector(self, B):

        bfx = self.Qfx*B
        bfy = self.Qfy*B
        bfz = self.Qfz*B

        return np.r_[bfx, bfy, bfz]

class MagSurveyBx(object):
    """docstring for MagSurveyBx"""
    def __init__(self, **kwargs):
        Survey.BaseData.__init__(self, **kwargs)

    def projectFields(self, B):
        bfx = self.Qfx*B
        return bfx


class BaseMagMap(Maps.IdentityMap):
    """BaseMagMap"""

    def __init__(self, mesh, **kwargs):
        Maps.IdentityMap.__init__(self, mesh)

    def _transform(self, m):

        return mu_0*(1 + m)

    def deriv(self, m):

        return mu_0*sp.identity(self.nP)

class WeightMap(Maps.IdentityMap):
    """Weighted Map for distributed parameters"""

    def __init__(self, mesh, weight, **kwargs):
        Maps.IdentityMap.__init__(self, mesh)
        self.mesh = mesh
        self.weight = weight

    def _transform(self, m):        
        return m*self.weight

    def deriv(self, m):
        return Utils.sdiag(self.weight)    


    

def readUBCmagObs(obs_file):
    
    """
    Read and write UBC mag file format
    
    INPUT:
    :param fileName, path to the UBC obs mag file
    
    OUTPUT:
    :param dobs, observation in (x y z [data] [wd])
    :param B, primary field information (BI, BD, B0)
    :param M, magnetization orentiaton (MI, MD)
    
    """

    fid = open(obs_file,'r') 

    # First line has the inclination,declination and amplitude of B0
    line = fid.readline()
    B = np.array(line.split(),dtype=float)

    # Second line has the magnetization orientation and a flag 
    line = fid.readline()
    M = np.array(line.split(),dtype=float)

    # Third line has the number of rows
    line = fid.readline()
    ndat = np.array(line.split(),dtype=int)

    # Pre-allocate space for obsx, obsy, obsz, data, uncert
    line = fid.readline()
    temp = np.array(line.split(),dtype=float) 
        
    dobs = np.zeros((ndat,len(temp)), dtype=float)
    
    
    for ii in range(ndat):
        
        dobs[ii,:] = np.array(line.split(),dtype=float) 
        line = fid.readline()
        
    return B, M, dobs