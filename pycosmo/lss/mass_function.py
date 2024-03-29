#!/usr/bin/python3
r"""

Halo Massfunction Module
========================

to do
"""

import warnings
import numpy as np
import pycosmo.lss.overdensity as od
from pycosmo.lss._flags import *
from typing import Any, Tuple, Union, TypeVar 
from abc import ABC, abstractmethod

Cosmology = TypeVar('Cosmology')

class HaloMassFunctionError(Exception):
    r"""
    Base class of exceptions used by halo mass function objects.
    """

class HaloMassFunction(ABC):
    r"""
    An abstract halo mass-function class. The halo mass-function gives the number density of halos of a specific 
    mass.

    .. math::
        \frac{ {\rm d}n }{ {\rm d}\ln M } 
            = f(\sigma) \frac{\bar\rho_m}{M^2} \frac{ {\rm d}\ln \sigma^{-1} }{ {\rm d}\ln M }

    where, :math:`f(\sigma)` is a fitting function modelling the mass function, :math:`\bar\rho_m` is the 
    mean matter density and :math:`\sigma` is the RMS deviation of fluctuations in the matter field.

    Parameters
    ----------
    cm: Cosmology
        Cosmology model object to use.
    
    """

    def __init__(self, cm: Cosmology) -> None:

        # if not isinstance( cm, Cosmology ):
        #     raise HaloMassFunctionError("argument must be a 'Cosmology' object")
        self.cosmology = cm

        # flags destribing the mass-function properties
        self.flags     = 0
    
    @property
    def zDependent(self) -> bool:
        """
        Whether the model is redshift-dependent?
        """

        return bool( self.flags & Z_DEPENDENT )
    
    @property
    def cosmoDependent(self) -> bool:
        """
        Whether the model is cosmology dependent?
        """

        return bool( self.flags & COSMO_DEPENDENT )

    @property
    def mdefs(self) -> Tuple[str]:
        """
        Valid mass definitions/overdensities.
        """

        mdefs = []
        if self.flags & FOF_OVERDENSITY:
            mdefs.append( 'fof' )
        if self.flags & SO_OVERDENSITY:
            mdefs.append( 'so' )
        return tuple( mdefs )

    @abstractmethod
    def f(self, sigma: Any, z: float = 0, overdensity: Union[int, str, od.OverDensity] = None) -> Any:
        r"""
        Fitting function for the mass-function.

        Parameters
        ----------
        sigma: array_like
            Density field fluctuation variance.
        z: float, optional
            Redshift (default is 0).
        overdensity: str, int, OverDensity, optional
            Value of the overdensity. For FoF type halos, its default value is `fof` and for spherical overdensity 
            (SO) halos, it is 200.

        Returns
        -------
        f: array_like
            Halo mass function values.
        """
        ...

    def massFunction(self, m: Any, z: float = 0, overdensity: Union[int, str, od.OverDensity] = None, out: str = 'dndlnm') -> Any:
        r"""
        Compute the halo mass-function and return the value in a specified format.

        Parameters
        ----------
        m: array_like
            Mass of the halo in Msun/h.
        z: float, optional
            Redshift (default is 0).
        overdensity: str, int, OverDensity, optional
            Value of the overdensity. It could be an integer value of overdensity w.r.to the mean background density, 
            a string indicating the value such as `200m`, `vir` etc., or an :class:`OverDensity` object. For FoF type 
            halos, its default value is `fof` and for spherical overdensity (SO) halos, it is 200.
        out: str, optional
            Output format for the mass function. Must be either of `f`, `dndm`, `dndlnm` (default) or `dndlog10m`.

        Returns
        -------
        mf: array_like
            Halo mass-function in specified format.

        """

        mdefs = self.mdefs
        if overdensity is None:
            if 'fof' in mdefs:
                overdensity = 'fof'
            if 'so' in mdefs:
                overdensity = '200m'

            if len( mdefs ) > 1:
                warnings.warn(f"mass-function '{ self.model }' accepts multiple overdensities, using '{ overdensity }'")
        
        m = np.asfarray( m )

        if np.ndim( z ):
            raise TypeError("z must be a scalar")
        elif z + 1 < 0:
            raise ValueError("z must be greater than -1")

        r        = self.cosmology.lagrangianR( m )
        sigma    = np.sqrt( self.cosmology.variance( r, z ) )
        dlnsdlnm = self.cosmology.dlnsdlnm( r, z )

        f = self.f( sigma, z, overdensity )

        if out == 'f':
            return f

        dndlnM = f * ( self.cosmology.rho_m( z ) / m ) * ( -dlnsdlnm )
        
        if out == 'dndlnm':
            return dndlnM
        if out == 'dndlog10m':
            return dndlnM * 2.302585092994046 # log(M) = ln(M) / ln(10)
        if out == 'dndm':
            return dndlnM / m

        raise HaloMassFunctionError(f"invalid output mode: '{ out }")

        
###################################################################################
# pre-defined models
###################################################################################


class Press74(HaloMassFunction):
    r"""
    Mass function model by Press & Schechter (1974)[1]_. This model is based on the assumption that the matter density 
    fluctuations are normally distributed and halos are formed by spherical collapse of overdense regions of the 
    field. This gives

    .. math ::

        f(\sigma) = \sqrt{ \frac{2}{\pi} } \nu \exp \left( -\frac{\nu^2}{2} \right)

    where :math:`\nu = \delta_c / \sigma(M)` and :math:`delta_c \approx 1.686` is the critical over-density for 
    spherical collapse.

    Parameters
    ----------
    cm: Cosmology
        Cosmology model.

    References
    ----------

    .. [1] Houjun Mo, Frank van den Bosch, Simon White. Galaxy Formation and Evolution, Cambridge University Press, (2010). 
    """

    def __init__(self, cm: Cosmology) -> None:
        super().__init__(cm)

        self.flags = FOF_OVERDENSITY
        self.model = 'press74'

    def f(self, sigma: Any, z: float = 0, overdensity: Union[int, str, od.OverDensity] = 'fof') -> Any:
        
        # create the overdensity object
        overdensity = od.overDensity( overdensity )
        if overdensity != od.fof:
            warnings.warn(f"'{ self.model }' mass function is defined for FoF halos")

        nu = self.cosmology.collapseOverdensity( z ) / np.asfarray( sigma )
        f  = np.sqrt( 2 / np.pi ) * nu * np.exp( -0.5 * nu**2 )
        return f

class Sheth01(HaloMassFunction):
    r"""
    Halo mass-function by Sheth et al (2001) [1]_. It is based on ellipsolidal collapse.

    Parameters
    ----------
    cm: Cosmology
        Cosmology model.

    References
    ----------

    .. [1] Ravi K. Sheth, H. J. Mo & Giuseppe Tormen. Ellipsoidal collapse and an improved model for the number and 
            spatial distribution of dark matter haloes. <http://arXiv.org/abs/astro-ph/9907024v1>
    """

    def __init__(self, cm: Cosmology) -> None:
        super().__init__(cm)

        self.flags = FOF_OVERDENSITY
        self.model = 'sheth01'

    def f(self, sigma: Any, z: float = 0, overdensity: Union[int, str, od.OverDensity] = 'fof') -> Any:

        # create the overdensity object
        overdensity = od.overDensity( overdensity )
        if overdensity != od.fof:
            warnings.warn(f"'{ self.model }' mass function is defined for FoF halos")

        A = 0.3222
        a = 0.707
        p = 0.3
        nu = self.cosmology.collapseOverdensity( z ) / np.asarray( sigma )
        f = A * np.sqrt( 2*a / np.pi ) * nu * np.exp( -0.5 * a * nu**2 ) * ( 1.0 + ( nu**2 / a )**-p )
        return f

class Jenkins01(HaloMassFunction):
    r"""
    Halo mass function by Jenkins et al (2001). It is valid over the range :math:`-1.2 \le \ln \sigma^{-1} \le 1.05` 
    [1]_.

    Parameters
    ----------
    cm: Cosmology
        Cosmology model.

    References
    ----------

    .. [1] A. Jenkins et al. The mass function of dark matter halos. <http://arxiv.org/abs/astro-ph/0005260v2>
    """

    def __init__(self, cm: Cosmology) -> None:
        super().__init__(cm)

        self.flags = FOF_OVERDENSITY
        self.model = 'jenkins01'

    def f(self, sigma: Any, z: float = 0, overdensity: Union[int, str, od.OverDensity] = 'fof') -> Any:
        
        # create the overdensity object
        overdensity = od.overDensity( overdensity )
        if overdensity != od.fof:
            warnings.warn(f"'{ self.model }' mass function is defined for FoF halos")

        sigma = np.asfarray( sigma )
        f     = 0.315*( -np.abs( np.log( sigma**-1 ) + 0.61 )**3.8 )
        return f

class Reed03(Sheth01):
    r"""
    Halo mass function by Reed et al (2003) [1]_.

    Parameters
    ----------
    cm: Cosmology
        Cosmology model.

    References
    ----------

    .. [1] Zarija Lukić et al. The halo mass function: high-redshift evolution and universality. 
            <http://arXiv.org/abs/astro-ph/0702360v2>.
    """

    def __init__(self, cm: Cosmology) -> None:
        super().__init__(cm)

        self.flags = FOF_OVERDENSITY
        self.model = 'reed03'

    def f(self, sigma: Any, z: float = 0, overdensity: Union[int, str, od.OverDensity] = 'fof') -> Any:

        # create the overdensity object
        overdensity = od.overDensity( overdensity )
        if overdensity != od.fof:
            warnings.warn(f"'{ self.model }' mass function is defined for FoF halos")

        sigma = np.asfarray( sigma )
        f     = super().f(sigma, z, overdensity) * np.exp( -0.7 / ( sigma * np.cosh( 2*sigma )**5 ) )
        return f

class Warren06(HaloMassFunction):
    r"""
    Halo mass function by Warren et al (2006) [1]_.

    Parameters
    ----------
    cm: Cosmology
        Cosmology model.

    References
    ----------

    .. [1] Zarija Lukić et al. The halo mass function: high-redshift evolution and universality. 
            <http://arXiv.org/abs/astro-ph/0702360v2>.
    """

    def __init__(self, cm: Cosmology) -> None:
        super().__init__(cm)

        self.flags = FOF_OVERDENSITY
        self.model = 'warren06'

    def f(self, sigma: Any, z: float = 0, overdensity: Union[int, str, od.OverDensity] = '200m') -> Any:

        # create the overdensity object
        overdensity = od.overDensity( overdensity )
        if overdensity != od.fof:
            warnings.warn(f"'{ self.model }' mass function is defined for FoF halos")


        A, a, b, c = 0.7234, 1.625, 0.2538, 1.1982

        sigma = np.asfarray( sigma )
        f     = A * ( sigma**-a + b ) * np.exp( -c / sigma**2 )
        return f

class Reed07(HaloMassFunction):
    r"""
    Halo mass function by Reed et al (2007) [1]_. This model depends on redshift and the specific cosmology model.

    Parameters
    ----------
    cm: Cosmology
        Cosmology model.

    References
    ----------

    .. [1] Reed et al. The halo mass function from the dark ages through the present day. Mon. Not. R. Astron. Soc. 374, 
            2-15 (2007)
    """

    def __init__(self, cm: Cosmology) -> None:
        super().__init__(cm)

        self.flags = FOF_OVERDENSITY | Z_DEPENDENT | COSMO_DEPENDENT
        self.model = 'reed07'

    def f(self, sigma: Any, z: float = 0, overdensity: Union[int, str, od.OverDensity] = 'fof') -> Any:

        # create the overdensity object
        overdensity = od.overDensity( overdensity )
        if overdensity != od.fof:
            warnings.warn(f"'{ self.model }' mass function is defined for FoF halos")

        cm = self.cosmology

        A, c, ca, p = 0.310, 1.08, 0.764, 0.3

        sigma = np.asfarray( sigma )
        omega = np.sqrt( ca ) * cm.collapseOverdensity( z ) / sigma

        G1    = np.exp( -0.5*( np.log( omega ) - 0.788 )**2 / 0.6**2 )
        G2    = np.exp( -0.5*( np.log( omega ) - 1.138 )**2 / 0.2**2 )

        r     = cm.radius( sigma, z )
        neff  = -6.0*cm.dlnsdlnm( r, 0.0 ) - 3.0
        
        # eqn. 12
        f = (
                A * omega * np.sqrt( 2.0/np.pi ) 
                    * np.exp( -0.5*omega - 0.0325*omega**p / ( neff + 3 )**2 )
                    * ( 1.0 + 1.02*omega**( 2*p ) + 0.6*G1 + 0.4*G2 )
            )
        return f

class Tinker08(HaloMassFunction):
    r"""
    Halo mass function model by Tinker et al (2008) [1]_. This model is redshift dependent.

    Parameters
    ----------
    cm: Cosmology
        Cosmology model.

    References
    ----------

    .. [1] Jeremy Tinker et al. Toward a halo mass function for precision cosmology: The limits of universality. 
            <http://arXiv.org/abs/0803.2706v1> (2008).
    """

    # find interpolated values from 0-redshift parameter table : table 2
    from scipy.interpolate import CubicSpline

    A  = CubicSpline(
                        [200,   300,   400,   600,   800,   1200,  1600,  2400,  3200 ],
                        [0.186, 0.200, 0.212, 0.218, 0.248, 0.255, 0.260, 0.260, 0.260],
                    )
    a  = CubicSpline(
                        [200,   300,   400,   600,   800,   1200,  1600,  2400,  3200 ],
                        [1.47,  1.52,  1.56,  1.61,  1.87,  2.13,  2.30,  2.53,  2.66 ],
                    )
    b  = CubicSpline(
                        [200,   300,   400,   600,   800,   1200,  1600,  2400,  3200 ],
                        [2.57,  2.25,  2.05,  1.87,  1.59,  1.51,  1.46,  1.44,  1.41 ],
                    )
    c  = CubicSpline(
                        [200,   300,   400,   600,   800,   1200,  1600,  2400,  3200 ],
                        [1.19,  1.27,  1.34,  1.45,  1.58,  1.80,  1.97,  2.24,  2.44 ],
                    )
    
    def __init__(self, cm: Cosmology) -> None:
        super().__init__(cm)

        self.flags = SO_OVERDENSITY | Z_DEPENDENT 
        self.model = 'tinker08'

    def f(self, sigma: Any, z: float = 0, overdensity: Union[int, str, od.OverDensity] = '200m') -> Any:
        
        sigma  = np.asarray( sigma )

        if np.ndim( z ):
            raise ValueError("parameter 'z' should be a scalar")
        elif z < -1:
            raise ValueError("redshift 'z' must be greater than -1")

        # create the overdensity object and extranct the value
        overdensity = od.overDensity( overdensity )
        if not isinstance( overdensity, od.SO ):
            warnings.warn(f"'{ self.model }' mass function is defined only for SO halos")
        overdensity = overdensity.value( z, self.cosmology )

        if overdensity < 200 or overdensity > 3200:
            raise ValueError('`overdensity` value is out of bound. must be within 200 and 3200.')

        # redshift evolution of parameters : 
        zp1   = 1 + z
        A     = self.A( overdensity ) / zp1**0.14 # eqn 5
        a     = self.a( overdensity ) / zp1**0.06 # eqn 6  
        alpha = 10.0**( -( 0.75 / np.log10( overdensity/75 ) )**1.2 ) # eqn 8    
        b     = self.b( overdensity ) / zp1**alpha # eqn 7 
        c     = self.c( overdensity )

        f = A * ( 1 + ( b / sigma )**a ) * np.exp( -c / sigma**2 ) # eqn 3
        return f

class Crocce10(HaloMassFunction):
    r"""
    Halo mass function by Crocce et al (2010) [1]_.

    Parameters
    ----------
    cm: Cosmology
        Cosmology model.

    References
    ----------

    .. [1] Martín Crocce et al. Simulating the Universe with MICE : The abundance of massive clusters. 
            <http://arxiv.org/abs/0907.0019v2>
    """

    def __init__(self, cm: Cosmology) -> None:
        super().__init__(cm)

        self.flags = FOF_OVERDENSITY | Z_DEPENDENT
        self.model = 'crocce10'

    def f(self, sigma: Any, z: float = 0, overdensity: Union[int, str, od.OverDensity] = 'fof') -> Any:

        # create the overdensity object
        overdensity = od.overDensity( overdensity )
        if overdensity != od.fof:
            warnings.warn(f"'{ self.model }' mass function is defined for FoF halos")

        if np.ndim( z ):
            raise ValueError("parameter 'z' should be a scalar")
        
        zp1 = z + 1
        if z < -1:
            raise ValueError("redshift 'z' must be greater than -1")

        Az = 0.580 * zp1**-0.130
        az = 1.370 * zp1**-0.150
        bz = 0.300 * zp1**-0.084
        cz = 1.036 * zp1**-0.024
        return Az * ( sigma**-az + bz ) * np.exp( -cz / sigma**2 )

class Courtin10(HaloMassFunction):
    r"""
    Halo mass function by Courtin et al (2010) [1]_.

    Parameters
    ----------
    cm: Cosmology
        Cosmology model.

    References
    ----------

    .. [1] J. Courtin et al. Imprints of dark energy on cosmic structure formation-II. Non-universality of the halo 
            mass function. Mon. Not. R. Astron. Soc. 410, 1911-1931 (2011)
    """

    def __init__(self, cm: Cosmology) -> None:
        super().__init__(cm)

        self.flags = FOF_OVERDENSITY
        self.model = 'courtin10'

    def f(self, sigma: Any, z: float = 0, overdensity: Union[int, str, od.OverDensity] = 'fof') -> Any:

        # create the overdensity object
        overdensity = od.overDensity( overdensity )
        if overdensity != od.fof:
            warnings.warn(f"'{ self.model }' mass function is defined for FoF halos")

        A  = 0.348
        a  = 0.695
        p  = 0.1
        nu = self.cosmology.collapseOverdensity( z ) / np.asarray( sigma )
        f  = A * np.sqrt( 2*a / np.pi ) * nu * np.exp( -0.5 * a * nu**2 ) * ( 1.0 + ( nu**2 / a )**-p )
        return f


available = ['press74', 'sheth01', 'jenkins01', 'reed03', 'warren06', 'reed07', 'tinker08', 'crocce10', 'courtin10']

def massFunction(model: Union[str, HaloMassFunction], cm: Cosmology) -> HaloMassFunction:
    """
    Create a :class:`HaloMassFunction` object of given model.

    Parameters
    ----------
    model: str, HaloMassFunction
        Mass function model to use. See `mass_function.available` for a list of available models. It must be a string name of the model or a :class:`HaloMassFunction` object. 
        in the later case, it returns the object itself.
    cm: Cosmology
        Cosmology model.

    Returns
    -------
    mf: HaloMassFunction
        Halo massfunction object.

    """

    if isinstance(model, HaloMassFunction):
        return model

    if not isinstance(model, str):
        raise TypeError("model must be 'HaloMassFunction' object or 'str'")

    if model == 'press74' : 
        return Press74( cm )
    if model == 'sheth01': 
        return Sheth01( cm )
    if model == 'jenkins01': 
        return Jenkins01( cm )
    if model == 'reed03': 
        return Reed03( cm )
    if model == 'warren06': 
        return Warren06( cm )
    if model == 'reed07': 
        return Reed07( cm )
    if model == 'tinker08': 
        return Tinker08( cm )
    if model == 'crocce10': 
        return Crocce10( cm )
    if model == 'courtin10': 
        return Courtin10( cm )
    
    raise ValueError(f"invalid mass function model '{model}'")