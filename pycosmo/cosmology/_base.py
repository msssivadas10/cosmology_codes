import numpy as np
from pycosmo.utils import settings
from pycosmo import constants as const
from pycosmo import power_spectrum as ps, lss
from scipy.integrate import simpson
from typing import Any, Callable, TypeVar


PowerSpectrumType = TypeVar('PowerSpectrumType')
MassFunctionType  = TypeVar('MassFunctionType')
LinearBiasType    = TypeVar('LinearBiasType')
OverDensityType   = TypeVar('OverDensityType')

#################################################################################
# Cosmology model base class
#################################################################################

class CosmologyError(Exception):
    r"""
    Base class of exceptions used by cosmology objects.
    """
    ...

class Cosmology:
    r"""
    A class representing a cosmology model. A cosmology model stores parameters modelling a cosmology and 
    contains special methods related to astrophysical computations, such as power spectra, correlations and 
    halo mass-functions. 
    
    This model uses a generally variable dark-energy model, with the equation of state linearly varying 
    with time, :math:`w(z) = w_0 + w_a \frac{ z }{ z+1 }`. Default model is the *cosmological constant*, 
    :math:`\Lambda`, corresponding to :math:`w_0=-1, w_a=0`. The model can also be configured to include 
    curved geometry, relativistic species and massive neutrinos.

    Parameters
    ----------
    h: float
        Present value of Hubble parameter in 100 km/sec/Mpc.
    Om0: float
        Present density of matter in units of critical density. Must be non-negative.
    Ob0: float
        Present density of baryonic matter in units of critical density. Must be non-negative.
    sigma8: float
        RMS fluctuation of the matter density field at 8 Mpc/h scale. Must be non-negative. 
    ns: float
        Power law index for the early power spectrum.
    flat: bool, optional
        Tells the spatial geometry. Default is a flat geometry.
    relspecies: bool, optional
        Tells if the model contains relativistic species or radiation (default is false).
    Ode0: float, only for non-flat geometry
        Present dark-energy density in units of critical density. Must be non-negative. In a flat space, it 
        is taken as the remaining density after matter.
    Omnu0: float, optional
        Present density of *massive* neutrinos in units of critical density. Must be non-negative. Default 
        value is 0, means no massive neutrinos.
    Nmnu: float, optional
        Number of massive neutrino species. Must be a non-zero, positive value, and it is required when there 
        is massive neutrinos.
    Tcmb0: float, optional
        Present temperature of the CMB in kelvin (default 2.275K).
    w0, wa: float, optional
        Equation of state parametrization for dark-energy. `w0` is the constant part  and `wa` is the time 
        varying part (default is `w0` = -1 and `wa` = 0, correspond to the cosmological constant). 
    Nnu: float, optional
        Total number of neutrinos (massive and relativistic). Default is 3.
    power_spectrum: str, PowerSpectrum, optional 
        Tell the linear matter power spectrum (or, transfer function) model to use. Default model is Eisenstein-
        Hu model without baryon oscillations (`eisenstein98_zb` if no massive neutrino, else `eisenstein98_nu`). 
    filter: str, optional
        Filter used to smooth the density field. Default is a spherical tophat (`tophat`). Other availabe models 
        are Gaussian (`gauss`) and sharp-k (`sharp-k`, not fully implemented).
    mass_function: str, HaloMassFunction, optional
        Tell the halo mass function model to use. Default is the model by Tinker et al (2008), `tinker08`. 
    linear_bias: str, optional
        Tell the linear bias model to use. Default is Tinker et al (2010).

    Raises
    ------
    CosmologyError:
        When the parameter values are incorrect, on failure of colsmological calculations.

    Examples
    --------
    
    """

    __slots__ = (
                    'Om0', 'Ob0', 'Omnu0', 'Oc0', 'Ode0', 'Ok0', 'Or0', 'Oph0', 'Ornu0', 'Tcmb0', 'Tnu0',
                    'h', 'sigma8', 'ns', 'Nmnu', 'Nrnu', 'Mmnu', 'Mrnu', 'Nnu', 'Mnu', 'w0', 'wa', 'flat', 
                    'relspecies', 'power_spectrum', 'mass_function', 'linear_bias',
                )
    
    def __init__(self, h: float, Om0: float, Ob0: float, sigma8: float, ns: float, flat: bool = True, 
                 relspecies: bool = False, Ode0: float = None, Omnu0: float = 0.0, Nmnu: float = None, 
                 Tcmb0: float = 2.725, w0: float = -1.0, wa: float = 0.0, Nnu: float = 3.0,
                 power_spectrum: PowerSpectrumType = None, filter: str = 'tophat', 
                 mass_function: MassFunctionType = 'tinker08', linear_bias: LinearBiasType = 'tinker10') -> None:
        
        # check parameters h, sigma8 and ns
        if h <= 0:
            raise CosmologyError("hubble parameter 'h' cannot be negative or zero")
        elif sigma8 <= 0:
            raise CosmologyError("'sigma8' cannot be negative or zero")
        
        self.h, self.sigma8, self.ns = h, sigma8, ns

        # total neutrino number
        if Nnu < 0:
            raise CosmologyError("total neutrino number cannot be negative")
        self.Nnu  = Nnu
            
        # initialise the matter components
        self._init_matter( Om0, Ob0, Omnu0, Nmnu )    

        self.Nrnu = self.Nnu - self.Nmnu 

        # initialise radiation (CMB + relativistic neutrino)
        if Tcmb0 <= 0:
            raise CosmologyError("CMB temperature 'Tcmb0' cannot be negative or zero")
        self.Tcmb0 = Tcmb0
        self.Tnu0  = 0.7137658555036082 * Tcmb0 # temperature of CnuB, (4/11)^(1/3) * Tcmb0 ( TODO: check this )

        self._init_relspecies( relspecies )

        # initialize dark-energy and curvature
        if flat:
            Ode0 = 1 - self.Om0 - self.Or0
            if Ode0 < 0.0:
                raise CosmologyError("dark energy density cannot be negative, adjust matter density")
            self.Ode0, Ok0 = Ode0, 0.0
        else:
            if Ode0 is None:
                raise CosmologyError("Ode0 is a required argument for non-flat cosmology")
            elif Ode0 < 0.0:
                raise CosmologyError("dark-energy density cannot be negative")
            self.Ode0 = Ode0
            
            # calculate the curvature
            Ok0 = 1 - self.Om0 - self.Or0 - self.Ode0
            if abs( Ok0 ) < 1E-15:
                Ok0, flat = 0.0, True
            
        self.flat, self.Ok0 = flat, Ok0

        # dark-energy equation of state parameterization:
        self.w0, self.wa = w0, wa 

        # initialiing power spectrum
        self.setPowerSpectrum( power_spectrum, filter )

        # initialising mass function
        self.setMassFunction( mass_function )

        # initialising linear bias
        self.setLinearBias( linear_bias )

    def _init_matter(self, Om0: float, Ob0: float, Omnu0: float = 0.0, Nmnu: float = None):
        r"""
        Calculate matter component densities.
        """

        if Om0 < 0:
            raise CosmologyError("matter density cannot be negative")
        elif Ob0 < 0:
            raise CosmologyError("baryon density cannot be negative")

        if Omnu0:
            if Omnu0 < 0:
                raise CosmologyError("neutrino density must be within 0 and matter density")
            if Nmnu is None or Nmnu <= 0:
                raise CosmologyError("number of massive neutrinos density must be within 0 and matter density")
            elif Nmnu > self.Nnu:
                raise CosmologyError("number of massive nuetrinos cannot exceed total nuetrino number")
        else:
            Omnu0, Nmnu = 0.0, 0.0
        
        if Ob0 + Omnu0 > Om0:
            raise CosmologyError("baryon + massive neutrino density cannot exceed total matter density")
        
        self.Om0, self.Ob0    = Om0, Ob0
        self.Omnu0, self.Nmnu = Omnu0, Nmnu
        self.Oc0              = self.Om0 - self.Ob0 - self.Omnu0  # cold dark matter density

        self.Mmnu = 0.0
        if self.Omnu0:
            self.Mmnu = 91.5 * self.Omnu0 / self.Nmnu * self.h**2 # mass of one massive neutrino

    def _init_relspecies(self, value: bool) -> None:
        r"""
        Calculate relaticistic species densities.
        """

        if not value:
            self.relspecies = False

            # set all relativistic species densities to zero
            self.Oph0, self.Ornu0, self.Or0 = 0.0, 0.0, 0.0
            
            self.Mrnu = 0.0 # neutrino mass
            return

        self.relspecies = True
        
        # calculate the photon and neutrino density from cmb temperature:
        # using the stephans law to compute the energy density of the photons and converting it into 
        # mass density using E = mc^2. then, 
        # 
        #   Oph0 = 4 * stephan_boltzmann_const * Tcmb0^4 / c^3 / critical_density
        #
        # i.e., Oph0 = const. * Tcmb^4 / h^2, where the constant is `stephan_boltzmann_const / c^3 / critical_density` 
        # with stephans const. in kg/sec^3/K^4, c in m/sec and critical density in h^2 kg/m^2 
        self.Oph0  = 4.4816066598134054e-07 * self.Tcmb0**4 / self.h**2

        # neutrino density is N * (7/8) * (4/11)^(4/3) * photon density
        self.Ornu0 = self.Nrnu * 0.22710731766023898 * self.Oph0

        # mass of relativistic neutrino
        self.Mrnu  = 0.0
        if self.Ornu0:
            self.Mrnu = 91.5 * self.Ornu0 / self.Nrnu * self.h**2

        # total relativistic species density
        self.Or0   = self.Oph0 + self.Ornu0
        return

    def setPowerSpectrum(self, power_spectrum: PowerSpectrumType = None, filter: str = None) -> None:
        r"""
        Set the linear power spectrum / transfer function model. The model must be a valid string name of a model 
        or a :class:`PowerSpectrum` object. 
        """

        # initialiing power spectrum
        if power_spectrum is None:
            power_spectrum = 'eisenstein98_nu' if self.Omnu0 > 1e-08 else 'eisenstein98_zb'
        if filter is None:
            filter = 'tophat'

        self.power_spectrum = ps.powerSpectrum(model = power_spectrum, cm = self, filter = filter)
        return
        
    def setMassFunction(self, mass_function: MassFunctionType = None) -> None:
        r"""
        Set the halo mass-function model. The model must be a valid string name of a model or a 
        :class:`HaloMassFunction` object. 
        """

        # initialising mass function
        if mass_function is None:
            mass_function = 'tinker08'

        self.mass_function = lss.massFunction(model = mass_function, cm = self)
        return

    def setLinearBias(self, linear_bias: LinearBiasType = None) -> None:
        r"""
        Set the linear halo bias model. The model must be a valid string name of a model or a :class:`LinearBias` 
        object. 
        """

        # initialising linear bias
        if linear_bias is None:
            linear_bias = 'tinker10'

        self.linear_bias = lss.linearBias(model = linear_bias, cm = self)
        return

    def __repr__(self) -> str:

        items = [ f'flat={ self.flat }' , f'h={ self.h }', f'Om0={ self.Om0 }', f'Ob0={ self.Ob0 }', f'Ode0={ self.Ode0 }' ]
        if self.Omnu0:
            items.append( f'Omnu0={ self.Onu0 }' )
        if self.relspecies:
            items.append( f'Or0={ self.Or0 }' )
        items = items + [ f'sigma8={ self.sigma8 }',  f'ns={ self.ns }', f'Tcmb0={ self.Tcmb0 }K', f'w0={ self.w0 }',  f'wa={ self.wa }' ]
        return f'Cosmology({ ", ".join( items ) })'

    def wde(self, z: Any, deriv: bool = False) -> Any:
        r"""
        Evolution of equation of state parameter for dark-energy. In general, the dark-energy model 
        is given as

        .. math::
            w(z) = w_0 + w_a \frac{ z }{ 1+z }

        :math:`w_0 = 1` and :math:`w_a = 0` is the cosmological constant.

        Parameters
        ----------
        z: array_like
            Redshift
        deriv: bool, optional
            If true. returns the derivative. Default is false.

        Returns
        -------
        w: array_like
            Value of the equation of state parameter.
        
        Examples
        -------

        """

        z = np.asfarray( z )
        if deriv:
            return self.wa / ( z + 1 )**2
        return self.w0 + self.wa * z / ( z + 1 )

    # hubble parameter:

    def E(self, z: Any, square: bool = False) -> Any:
        r"""
        Evolution of Hubble parameter. 

        .. math ::
            E( z ) = \frac{H( z )}{H_0} 
                = \sqrt{ \Omega_m (z+1)^3 + \Omega_k (z+1)^2 + \Omega_r (z+1)^4 + \Omega_{de}(z) }

        Parameters
        ----------
        z: array_like
            Redshift.
        square: bool, optional
            If set true, return the squared value (default is false).

        Returns
        -------
        Ez: array_like
            Value of the function. 

        Examples
        --------

        """

        zp1 = np.asfarray( z ) + 1
        res = self.Om0 * zp1**3 + self.Ode0 * zp1**( 3 + 3*self.wde( z ) )
        if not self.flat:
            res = res + self.Ok0 * zp1**2
        if self.relspecies:
            res = res + self.Or0 * zp1**4
        if square:
            return res
        return np.sqrt( res )

    @property
    def H0(self) -> float:
        """
        Present value of the Hubble parameter.
        """

        return self.h * 100.0

    def H(self, z: Any) -> Any:
        r"""
        Evolution of Hubble parameter. 

        Parameters
        ----------
        z: array_like
            Redshift.

        Returns
        -------
        Hz: array_like
            Value of the Hubble parameter. 

        Examples
        --------

        """

        return self.H0 * self.E( z )

    def dlnEdlnzp1(self, z: Any) -> Any:
        r"""
        Logarithmic derivative of Hubble parameter. 

        Parameters
        ----------
        z: array_like
            Redshift.

        Returns
        -------
        y: array_like
            Value of the derivative. 

        Examples
        --------

        """

        zp1 = np.asfarray( z ) + 1

        # add matter contribution to numerator and denominator
        y   = self.Om0 * zp1**3
        y1  = 3*y

        # add curvature contribution (if not flat)
        if not self.flat:
            tmp = self.Ok0 * zp1**2 
            y   = y  + tmp
            y1  = y1 + 2*tmp

        # add radiation contribution
        if self.relspecies:
            tmp = self.Or0 * zp1**4
            y   = y  + tmp
            y1  = y1 + 4*tmp

        # add dark-energy contribution
        b   = 3 + 3*self.wde( z ) 
        tmp = self.Ode0 * zp1**b
        y   = y  + tmp 
        y1  = y1 + tmp * ( 
                            b + ( 3*self.wde( z, deriv = True ) ) * zp1 * np.log( zp1 ) 
                         )

        return ( 0.5 * y1 / y )

    # densities 

    def Om(self, z: Any) -> Any:
        r"""
        Evolution of the density parameter for matter. 

        Parameters
        ----------
        z: array_like
            Redshift.

        Returns
        -------
        y: array_like
            Value of the density parameter. 

        Examples
        --------

        """

        zp1 = np.asfarray( z ) + 1
        res = self.Om0 * zp1**3
        y   = res + self.Ode0 * zp1**( 3 + 3*self.wde( z ) )
        if not self.flat:
            y = y + self.Ok0 * zp1**2
        if self.relspecies:
            y = y + self.Or0 * zp1**4
        return res / y

    def Ob(self, z: Any) -> Any:
        r"""
        Evolution of the density parameter for baryonic matter. 

        Parameters
        ----------
        z: array_like
            Redshift.

        Returns
        -------
        y: array_like
            Value of the density parameter. 

        Examples
        --------

        """

        return self.Om( z ) * ( self.Ob0 / self.Om0 )

    def Oc(self, z: Any) -> Any:
        r"""
        Evolution of the density parameter for cold dark-matter. 

        Parameters
        ----------
        z: array_like
            Redshift.

        Returns
        -------
        y: array_like
            Value of the density parameter. 

        Examples
        --------

        """

        return self.Om( z ) * ( self.Oc0 / self.Om0 )

    def Omnu(self, z: Any) -> Any:
        r"""
        Evolution of the density parameter for warm dark-matter (massive neutrino). 

        Parameters
        ----------
        z: array_like
            Redshift.

        Returns
        -------
        y: array_like
            Value of the density parameter. 

        Examples
        --------

        """

        return self.Om( z ) * ( self.Omnu0 / self.Om0 )

    def Ode(self, z: Any) -> Any:
        r"""
        Evolution of the density parameter for dark-energy. 

        Parameters
        ----------
        z: array_like
            Redshift.

        Returns
        -------
        y: array_like
            Value of the density parameter. 

        Examples
        --------

        """

        zp1 = np.asfarray( z ) + 1
        res = self.Ode0 * zp1**( 3 + 3*self.wde( z ) )
        y   = self.Om0 * zp1**3 + res
        if not self.flat:
            y = y + self.Ok0 * zp1**2
        if self.relspecies:
            y = y + self.Or0 * zp1**4
        return res / y

    def Ok(self, z: Any) -> Any:
        r"""
        Evolution of the density parameter for curvature. 

        Parameters
        ----------
        z: array_like
            Redshift.

        Returns
        -------
        y: array_like
            Value of the density parameter. 

        Examples
        --------

        """

        if self.flat:
            return np.zeros_like( z, dtype = 'float' )

        zp1 = np.asfarray( z ) + 1
        res = self.Ok0 * zp1**2
        y   = res + self.Om0 * zp1**3 + self.Ode0 * zp1**( 3 + 3*self.wde( z ) )
        if self.relspecies:
            y = y + self.Or0 * zp1**4
        return res / y

    def Or(self, z: Any) -> Any:
        r"""
        Evolution of the density parameter for relativistic components. 

        Parameters
        ----------
        z: array_like
            Redshift.

        Returns
        -------
        y: array_like
            Value of the density parameter. 

        Examples
        --------

        """

        if not self.relspecies:
            return np.zeros_like( z, 'float' )
        
        zp1 = np.asfarray( z ) + 1
        res = self.Or0 * zp1**4
        y   = res + self.Om0 * zp1**3 + self.Ode0 * zp1**( 3 + 3*self.wde( z ) )
        if not self.flat:
            y = y + self.Ok0 * zp1**2
        return res / y

    def Oph(self, z: Any) -> Any:
        r"""
        Evolution of the density parameter for photons. 

        Parameters
        ----------
        z: array_like
            Redshift.

        Returns
        -------
        y: array_like
            Value of the density parameter. 

        Examples
        --------

        """

        if not self.relspecies:
            return np.zeros_like( z, 'float' )
        return self.Or( z ) * ( self.Oph0 / self.Or0 )

    def Ornu(self, z: Any) -> Any:
        r"""
        Evolution of the density parameter for relativistic neutrino. 

        Parameters
        ----------
        z: array_like
            Redshift.

        Returns
        -------
        y: array_like
            Value of the density parameter. 

        Examples
        --------

        """

        if not self.relspecies:
            return np.zeros_like( z, 'float' )
        return self.Or( z ) * ( self.Ornu0 / self.Or0 )

    def criticalDensity(self, z: Any) -> Any:
        r"""
        Evolution of the critical density for the universe. Critical density is the density for the 
        universe to be flat.

        .. math::
            \rho_{\rm crit}(z) = \frac{ 3H(z)^2 }{ 8\pi G } 

        Parameters
        ----------
        z: array_like
            Redshift.

        Returns
        -------
        y: Any
            Value of the density. 

        Examples
        --------

        """

        return const.RHO_CRIT0_ASTRO * self.E( z, square = True )

    def rho_m(self, z: Any) -> Any:
        r"""
        Evolution of the density for matter. 

        Parameters
        ----------
        z: array_like
            Redshift.

        Returns
        -------
        y: Any
            Value of the density. 

        Examples
        --------

        """

        zp1 = np.asfarray(z) + 1
        return self.criticalDensity(0) * self.Om0 * zp1**3

    def rho_b(self, z: Any) -> Any:
        r"""
        Evolution of the density for baryonic matter. 

        Parameters
        ----------
        z: array_like
            Redshift.

        Returns
        -------
        y: Any
            Value of the density. 

        Examples
        --------

        """

        return self.rho_m( z ) * ( self.Ob0 / self.Om0 )

    def rho_c(self, z: Any) -> Any:
        r"""
        Evolution of the density for cold dark-matter. 

        Parameters
        ----------
        z: array_like
            Redshift.

        Returns
        -------
        y: Any
            Value of the density. 

        Examples
        --------

        """

        return self.rho_m( z ) * ( self.Oc0 / self.Om0 )

    def rho_mnu(self, z: Any) -> Any:
        r"""
        Evolution of the density for warm dark-matter (massive neutrino). 

        Parameters
        ----------
        z: array_like
            Redshift.

        Returns
        -------
        y: Any
            Value of the density. 

        Examples
        --------

        """

        return self.rho_m( z ) * ( self.Omnu0 / self.Om0 )

    def rho_de(self, z: Any) -> Any:
        r"""
        Evolution of the density for dark-energy. 

        Parameters
        ----------
        z: array_like
            Redshift.

        Returns
        -------
        y: Any
            Value of the density. 

        Examples
        --------

        """

        zp1 = np.asfarray(z) + 1
        return self.criticalDensity(0) * self.Ode0 * zp1**( 3 + 3*self.wde( z ) )
    
    def rho_r(self, z: Any) -> Any:
        r"""
        Evolution of the density for relativistic components. 

        Parameters
        ----------
        z: array_like
            Redshift.

        Returns
        -------
        y: Any
            Value of the density. 

        Examples
        --------

        """

        if not self.relspecies:
            return np.zeros_like( z, 'float' )
        
        zp1 = np.asfarray( z ) + 1
        return self.criticalDensity(0) * self.Or0 * zp1**4

    def rho_ph(self, z: Any) -> Any:
        r"""
        Evolution of the density for photons. 

        Parameters
        ----------
        z: array_like
            Redshift.

        Returns
        -------
        y: Any
            Value of the density. 

        Examples
        --------

        """

        if not self.relspecies:
            return self.rho_r( z )
        return self.rho_r( z ) * ( self.Oph0 / self.Or0 )

    def rho_rnu(self, z: Any) -> Any:
        r"""
        Evolution of the density for relativistic neutrinos. 

        Parameters
        ----------
        z: array_like
            Redshift.

        Returns
        -------
        y: Any
            Value of the density. 

        Examples
        --------

        """

        if not self.relspecies:
            return self.rho_r( z )
        return self.rho_r( z ) * ( self.Ornu0 / self.Or0 )

    # temperature of cmb and cnub:

    def Tcmb(self, z: Any) -> Any:
        r"""
        Evolution of the temperature of cosmic microwave background. 

        Parameters
        ----------
        z: array_like
            Redshift.

        Returns
        -------
        y: array_like
            Value of the temperature in Kelvin. 

        Examples
        --------

        """

        return self.Tcmb0 * ( np.asfarray( z ) + 1 )

    def Tnu(self, z: Any) -> Any:
        r"""
        Evolution of the temperature of cosmic neutrino background. 

        Parameters
        ----------
        z: array_like
            Redshift.

        Returns
        -------
        y: array_like
            Value of the temperature in Kelvin. 

        Examples
        --------

        """

        return self.Tnu0 * ( np.asfarray( z ) + 1 )

    # deceleration parameter

    def q(self, z: Any) -> Any:
        r"""
        Evolution of the deceleration parameter. 

        .. math::
            q( z ) = \frac{ a \ddot{a} }{ \dot{a}^2 }

        Parameters
        ----------
        z: array_like
            Redshift.

        Returns
        -------
        y: array_like
            Value of the deceleration parameter. 

        Examples
        --------

        """

        zp1 = np.asfarray( z )
        return zp1 * self.dlnEdlnzp1( z ) - 1 # TODO: check this eqn.
        
    # z-integrals: integrals of z-functions 

    def zIntegral(self, f: Callable, za: Any, zb: Any) -> Any:
        r"""
        Evaluate the definite integral of a function of redshift.

        .. math::
            I = \int_{ z_a }^{ z_b } f(z) {\rm d}z
        
        Parameters
        ----------
        f: callable
            Function to integrate. Must be a callable python function of single argument.
        za, zb: array_like
            Lower and upper limits of integration. Can be any value greater than -1, including `inf`.

        Returns
        -------
        y: array_like
            Values of the integrals.
        
        Examples
        --------

        """

        za, zb = np.asfarray( za ), np.asfarray( zb )

        if not callable( f ):
            raise TypeError("f must be a callable")
        if np.any( za+1 < 0 ) or np.any( zb+1 < 0 ):
            raise CosmologyError("redshift values must be greater than -1")

        def zfunc(lnzp1: Any) -> Any:
            z = np.exp( lnzp1 ) - 1
            return f( z ) * ( z + 1 )

        subdiv = settings.DEFAULT_SUBDIV
        xa, xb = np.log( za+1 ), np.log( zb+1 )
        npts   = int( 2**subdiv + 1 )

        x, h = np.linspace( xa, xb, npts, retstep = True, axis = -1 )
        y    = zfunc( x )
        return simpson(y, dx = h, axis = -1)

    def zIntegral_zp1_over_Ez3(self, za: Any, zb: Any) -> Any:
        r"""
        Evaluate the integral

        .. math::
            I = \int_{ z_a }^{ z_b } \frac{ z+1 }{ E(z)^3 } {\rm d}z
        
        Parameters
        ----------
        za, zb: array_like
            Lower and upper limits of integration. Can be any value greater than -1, including `inf`.

        Returns
        -------
        y: array_like
            Values of the integrals.
        
        Examples
        --------
        
        """

        def zfunc(z: Any) -> Any:
            return ( z + 1 ) / self.E( z )**3

        return self.zIntegral( zfunc, za, zb )

    def zIntegral_1_over_zp1_Ez(self, za: Any, zb: Any) -> Any:
        r"""
        Evaluate the integral

        .. math::
            I = \int_{ z_a }^{ z_b } \frac{ 1 }{ (z+1)E(z) } {\rm d}z
        
        Parameters
        ----------
        za, zb: array_like
            Lower and upper limits of integration. Can be any value greater than -1, including `inf`.

        Returns
        -------
        y: array_like
            Values of the integrals.
        
        Examples
        --------
        
        """

        def zfunc(z: Any) -> Any:
            return 1.0 / ( self.E( z ) * ( z + 1 ) )
        
        return self.zIntegral( zfunc, za, zb )

    def zIntegral_1_over_Ez(self, za: Any, zb: Any) -> Any:
        r"""
        Evaluate the integral

        .. math::
            I = \int_{ z_a }^{ z_b } \frac{ 1 }{ E(z) } {\rm d}z
        
        Parameters
        ----------
        za, zb: array_like
            Lower and upper limits of integration. Can be any value greater than -1, including `inf`.

        Returns
        -------
        y: array_like
            Values of the integrals.
        
        Examples
        --------
        
        """

        def zfunc(z: Any) -> Any:
            return 1.0 / self.E( z )
        
        return self.zIntegral( zfunc, za, zb )

    # time and distances

    def universeAge(self, z: Any) -> Any:
        r"""
        Return the age of the universe at redshift z.
        
        Parameters
        ----------
        z: array_like
            Redshift.

        Returns
        -------
        y: array_like
            Age in Gyr (giga years).
        
        Examples
        --------
        
        """

        inf = settings.INF
        t0  = self.zIntegral_1_over_zp1_Ez( z, inf ) * self.hubbleTime( 0 )
        return t0 * 1e-09
    
    def lookbackTime(self, z: Any) -> Any:
        r"""
        Return the lookback time at redshift z.
        
        Parameters
        ----------
        z: array_like
            Redshift.

        Returns
        -------
        y: array_like
            lookback time in Gyr.
        
        Examples
        --------
        
        """

        return self.universeAge( 0.0 ) - self.universeAge( z )

    def hubbleTime(self, z: Any) -> Any:
        r"""
        Return the Hubble time (inverse Hubble parameter) at redshift z.
        
        Parameters
        ----------
        z: array_like
            Redshift.

        Returns
        -------
        y: array_like
            Hubble time in Gyr.
        
        Examples
        --------
        
        """

        Hz = self.H( z ) * ( 1000.0 / const.MPC * const.YEAR ) # in 1/yr
        return 1.0 / Hz * 1e-09
    
    def comovingDistance(self, z: Any) -> Any:
        r"""
        Return the comoving distance corresponding to the redshift z.
        
        Parameters
        ----------
        z: array_like
            Redshift.

        Returns
        -------
        y: array_like
            comoving distance in Mpc.
        
        Examples
        --------
        
        """

        fac = const.C_SI / self.H0 / 1000.0 # c/H0 in Mpc
        return self.zIntegral_1_over_Ez( 0.0, z ) * fac

    def comovingCorrdinate(self, z: Any) -> Any:
        r"""
        Return the comving coordinate corresponding to the redshift z.
        
        Parameters
        ----------
        z: array_like
            Redshift.

        Returns
        -------
        y: array_like
           Comving coordinate in Mpc.
        
        Examples
        --------
        
        """

        x = self.comovingDistance( z )
        if self.Ok0:
            K = np.sqrt( abs( self.Ok0 ) ) * ( self.H0 / const.C_SI * 1000 ) 

            if self.Ok0 < 0.0:
                return np.sin( K*x ) / K # k > 0 : closed/spherical
            return np.sinh( K*x ) / K    # k < 0 : open / hyperbolic
        return x
    
    def angularDiamaterDistance(self, z: Any) -> Any:
        r"""
        Return the angular diameter distance corresponding to the redshift z.
        
        Parameters
        ----------
        z: array_like
            Redshift.

        Returns
        -------
        y: array_like
           Angular diameter distnace in Mpc.
        
        Examples
        --------
        
        """

        r = self.comovingCorrdinate( z )
        return r / ( 1 + np.asfarray( z ) )
    
    def luminocityDistance(self, z: Any) -> Any:
        r"""
        Return the luminocity distance corresponding to the redshift z.
        
        Parameters
        ----------
        z: array_like
            Redshift.

        Returns
        -------
        y: array_like
           Luminocity distnace in Mpc.
        
        Examples
        --------
        
        """

        r = self.comovingCorrdinate( z )
        return r * ( 1 + np.asfarray( z ) )
    
    def distanceModulus(self, z: Any) -> Any:
        r"""
        Return the distance modulus, the different between the corrected apparent magnitude (:math:`m`) and 
        the absolute magnitude (:math:`M`).

        .. math::
            \mu( z ) := m - M = 5 \log \frac{ d_L(z) }{ \rm Mpc } - 25

        Parameters
        ----------
        z: array_like
            Redshift.

        Returns
        -------
        y: array_like
           Distnace modulus.
        
        Examples
        --------
        
        """

        return 5*np.log( self.luminocityDistance( z ) ) - 25

    # horizons

    def hubbleHorizon(self, z: Any) -> Any:
        r"""
        Return the Hubble horizon at redshift z.
        
        Parameters
        ----------
        z: array_like
            Redshift.

        Returns
        -------
        y: array_like
           Hubble horizon in Mpc.
        
        Examples
        --------
        
        """

        c = const.C_SI / 1000.0 # speed of light in km/sec
        return c / self.Hz( z ) # Mpc
    
    def eventHorizon(self, z: Any) -> Any:
        r"""
        Return the event horizon at redshift z. Event horizon is the maximum comoving distance at 
        which light emitted now could reach.
        
        Parameters
        ----------
        z: array_like
            Redshift.

        Returns
        -------
        y: array_like
           Event horizon in Mpc.
        
        Examples
        --------
        
        """

        future = -1.0 + 1e-08
        return self.zIntegral_1_over_Ez( future, z )
    
    def particleHorizon(self, z: Any) -> Any:
        r"""
        Return the particle horizon at redshift z. Particle horizon is the maximum comoving distance from 
        which light could reach the observer within a specific time.
        
        Parameters
        ----------
        z: array_like
            Redshift.

        Returns
        -------
        y: array_like
           Particle horizon in Mpc.
        
        Examples
        --------
        
        """

        inf = settings.INF
        return self.zIntegral_1_over_Ez( z, inf )

    # linear growth

    def g(self, z: Any, exact: bool = False) -> Any:
        r"""
        Linear growth factor, suppressed with respect to that of a matter dominated universe. 
        Actual growth factor would be 

        .. math::
            D_+( z ) = \frac{ 1 }{ z+1 } g(z)

        Parameters
        ----------
        z: array_like
            Redshift
        exact: bool, optional
            If true, compute the growth factor exactly by evaluating an integral expression. 
            Otherwise, use the approximate form given by Carroll et al.

        Returns
        -------
        gz: array_like
            Growth factor values.

        Examples
        --------

        """
        
        def gzFit(z: Any) -> Any:
            Om, Ode = self.Om( z ), self.Ode( z )
            return 2.5*Om*(
                            Om**(4./7.) - Ode + ( 1 + Om/2 ) * ( 1 + Ode/70 )
                          )**( -1 )

        def gzExact(z: Any) -> Any:
            z, inf = np.asfarray( z ), settings.INF
            if np.ndim( z ):
                z  = z.flatten()
                
            y = self.zIntegral_zp1_over_Ez3( z, inf )
            return 2.5 * self.Om0 * self.E( z ) * y * ( z + 1 )
            
        return gzExact( z ) if exact else gzFit( z )

    def Dplus(self, z: Any, exact: bool = False, fac: float = None):
        r"""
        Linear growth factor.

        Parameters
        ----------
        z: array_like
            Redshift
        exact: bool, optional
            If true, compute the growth factor exactly by evaluating an integral expression. 
            Otherwise, use the approximate form given by Carroll et al.
        fac: float, optional
            Normalization of the growth factor. If not given, it is found such that the present 
            value is 1.

        Returns
        -------
        Dz: array_like
            Growth factor values.

        Examples
        --------
        
        """

        def _Dplus(z: Any, exact: bool) -> Any:
            gz = self.g( z, exact )
            return gz / ( z + 1 )

        if fac is None:
            fac = 1.0 / _Dplus( 0, exact )
        return _Dplus( z, exact ) * fac

    def f(self, z: Any, exact: bool = False) -> Any:
        r"""
        Logarithmic rate of linear growth factor with respect to scale factor.

        .. math::
            f( z ) = - \frac{ {\rm d}\ln D(z) }{ {\rm d}\ln (z+1) } \approx \Omega_m(z)^{ 0.55 }

        Parameters
        ----------
        z: array_like
            Redshift
        exact: bool, optional
            If true, compute the growth factor exactly by evaluating an integral expression. 
            Otherwise, use the approximate form.

        Returns
        -------
        Dz: array_like
            Growth factor values.

        Examples
        --------
        
        """

        def fzFit(z: Any) -> Any:
            return self.Om( z )**( 5./9 )

        def fzExact(z: Any) -> Any:
            return (
                        2.5*self.Om( z ) / self.g( z, exact = True ) 
                            - self.dlnEdlnzp1( z )
                   )
        
        return fzExact( z ) if exact else fzFit( z )
    
    def _DplusFreeStream(self, q: Any, Dz: Any, include_nu: bool = False) -> Any:
        r"""
        Growth factor in the presence of free streaming.

        Parameters
        ----------
        q: array_like
            Dimnsionless scale. If multi dimensional array, it will be flattened.
        Dz: array_like
            Linear growth factor. If multi dimensional array, it will be flattened.
        include_nu: bool, optional
            If true, returns the growth factor of fluctuations including massive neutrinos. Else, 
            return that of only baryons and cold dark-matter.
        
        Returns
        -------
        Dz: array_like
            Growth factor. If no neutrinos are presnt, then this will be same as the input growth 
            factor. 

        Examples
        --------

        """

        q, Dz = np.asfarray( q ), np.asfarray( Dz )
        if np.ndim( q ):
            q = q.flatten()
        if np.ndim( Dz ):
            Dz = Dz.flatten()[ :, None ]
        
        if not self.Omnu:
            return np.repeat( 
                                Dz, q.shape[0], 
                                axis = 1 if np.ndim( Dz ) else 0 
                            )

        fnu = self.Omnu0 / self.Om0 # fraction of massive neutrino
        fcb = 1 - fnu
        pcb = 0.25*( 5 - np.sqrt( 1 + 24.0*fcb ) )
        yfs = 17.2 * fnu * ( 1 + 0.488*fnu**(-7./6.) ) * ( self.Nmnu*q / fnu )**2
        
        x = ( Dz / ( 1 + yfs ) )**0.7     
        y = fcb**( 0.7 / pcb ) if include_nu else 1.0
        return ( y + x )**( pcb / 0.7 ) * Dz**( 1 - pcb )

    def DplusFreeStream(self, q: Any, z: Any, include_nu: bool = False, exact: bool = False, fac: float = None) -> Any:
        r"""
        Growth factor in the presence of free streaming.

        Parameters
        ----------
        q: array_like
            Dimnsionless scale. If multi dimensional array, it will be flattened.
        z: array_like
            Redshift. If multi dimensional array, it will be flattened.
        include_nu: bool, optional
            If true, returns the growth factor of fluctuations including massive neutrinos. Else, 
            return that of only baryons and cold dark-matter.
        
        Returns
        -------
        Dz: array_like
            Growth factor. If no neutrinos are presnt, then this will be same as the linear growth 
            factor. 

        Examples
        --------
        
        """

        Dz = self.Dplus( z, exact, fac ) # growth without free streaming
        return self._DplusFreeStream( q, Dz, include_nu )

    # power spectrum

    def linearPowerSpectrum(self, k: Any, z: float = 0, dim: bool = True) -> Any:
        r"""
        Compute the linear matter power spectrum. This power spectrum will correspond to the specified 
        transfer function model. 

        Parameters
        ----------
        k: array_like
            Wavenumber in h/Mpc.
        z: float, optional
            Redshift (default is 0).
        dim: bool, optional
            If true (default) return the power spectrum in :math:`h^{-3}/{\rm Mpc}^3`, otherwise gives the 
            dimensionless power spectrum.
        
        Returns
        -------
        pk: array_like
            Values of power spectrum.

        Examples
        --------

        """

        return self.power_spectrum.linearPowerSpectrum( k, z, dim )

    def nonlinearPowerSpectrum(self, k: Any, z: float = 0, dim: bool = True) -> Any:
        r"""
        Compute the non-linear matter power spectrum. This power spectrum will correspond to the specified 
        model. 

        Parameters
        ----------
        k: array_like
            Wavenumber in h/Mpc.
        z: float, optional
            Redshift (default is 0).
        dim: bool, optional
            If true (default) return the power spectrum in :math:`h^{-3}/{\rm Mpc}^3`, otherwise gives the 
            dimensionless power spectrum.
        
        Returns
        -------
        pk: array_like
            Values of power spectrum.

        Examples
        --------
        
        """

        return self.power_spectrum.nonlinearPowerSpectrum( k, z, dim )

    def matterPowerSpectrum(self, k: Any, z: float = 0, dim: bool = True, linear: bool = True) -> Any:
        r"""
        Compute the linear or non-linear matter power spectrum. This power spectrum will correspond to the 
        specified transfer function model. The linear power spectrum is given in terms of the transfer function 
        :math:`T(k)` as

        .. math::
            P_{\rm lin}(k, z) = A k^{ n_s } T(k)^2 D_+(z)^2

        where :math:`A` is the normalization factor. Non-linear power spectrum is modelled as some function of 
        the linear power spectrum. Thes will have units :math:`h^{-3}/{\rm Mpc}^3`. The dimensionless power 
        spectrum is defined as 

        .. math ::
            \Delta^2(k, z) = \frac{ k^3 P(k, z) }{ 2\pi^2 }

        Parameters
        ----------
        k: array_like
            Wavenumber in h/Mpc.
        z: float, optional
            Redshift (default is 0).
        dim: bool, optional
            If true (default) return the power spectrum in :math:`h^{-3}/{\rm Mpc}^3`, otherwise gives the 
            dimensionless power spectrum.
        linear: bool, optional
            If true (default) return the linear model, else non-linear.
        
        Returns
        -------
        pk: array_like
            Values of power spectrum.

        Examples
        --------
        
        """

        return self.power_spectrum.matterPowerSpectrum( k, z, dim, linear )

    def matterCorreleation(self, r: Any, z: float = 0, linear: bool = True) -> Any:
        r"""
        Compute the two-point correlation function for matter.

        .. math::
            \xi(r, z) = \int_0^\infty \Delta^2(k, z) \frac{ \sin kr }{ kr } {\rm d}\ln k

        Parameters
        ----------
        r: array_like
           Seperation between two spacial points in Mpc/h.
        z: float, optional
            Redshift (default is 0).
        linear: bool, optional
            If true (default) return the linear model, else non-linear.
        
        Returns
        -------
        xi: array_like
            Values of power spectrum.

        Examples
        --------
        
        """

        return self.power_spectrum.matterCorrelation( r, z, linear )

    def variance(self, r: Any, z: float = 0, linear: bool = True, j: int = 0) -> Any:
        r"""
        Compute the variance of matter fluctuations, smoothed at radius :math:`r` using a filter function,
        :math:`w (kr )`, such as a spherical top-hat. 

        .. math::
            \\sigma^2(r, z) = \int_0^\infty \Delta^2(k, z) w( kr )^2 {\rm d}\ln k

        Parameters
        ----------
        r: array_like
           Seperation between two spacial points in Mpc/h.
        z: float, optional
            Redshift (default is 0).
        linear: bool, optional
            If true (default) return the linear model, else non-linear.
        j: int, optional
            Indicates the moment, j = 0 (default) moment is the variance.
        
        Returns
        -------
        var: array_like
            Values of variance.

        Examples
        --------
        
        """

        return self.power_spectrum.variance(r, z, linear, j)
    
    def radius(self, sigma: Any, z: float = 0, linear: bool = True) -> Any:
        r"""
        Invert the variance to find the smoothing radius.

        Parameters
        ----------
        sigma: array_like
            Variance values (linear or non-linear, specified by `linear` argument), to be exact, their 
            square roots.
        z: float, optional
            Redshift (default is 0).
        linear: bool, optional
            If true (default) use the linear variance, else the non-linear variance.
        
        Returns
        -------
        r: array_like
            Smoothing radius in Mpc/h.

        Examples
        --------

        """

        return self.power_spectrum.radius( sigma, z, linear )
    
    def dlnsdlnr(self, r: Any, z: float = 0, linear: bool = True) -> Any:
        r"""
        Compute the first logarithmic derivative of smoothed variance.

        Parameters
        ----------
        r: array_like
           Seperation between two spacial points in Mpc/h.
        z: float, optional
            Redshift (default is 0).
        linear: bool, optional
            If true (default) return the linear model, else non-linear.
        
        Returns
        -------
        y: array_like
            Values of derivative of variance.

        Examples
        --------
        
        """

        return self.power_spectrum.dlnsdlnr( r, z, linear )
    
    def dlnsdlnm(self, r: Any, z: float = 0, linear: bool = True) -> Any:
        r"""
        Compute the first logarithmic derivative of matter fluctuations variance w.r.to mass.

        Parameters
        ----------
        m: array_like
            Smoothing radius in Mpc/h, corresponding to the mass.
        z: float, optional
            Redshift (default is 0).
        linear: bool, optional
            If true (default) return the value for linear variance, else for non-linear variance.
        
        Returns
        -------
        y: array_like
            Values of the derivative.

        Examples
        --------

        """

        return self.dlnsdlnr( r, z, linear ) / 3.0

    def d2lnsdlnr2(self, r: Any, z: float = 0, linear: bool = True) -> Any:
        r"""
        Compute the second logarithmic derivative of smoothed variance.

        Parameters
        ----------
        r: array_like
           Seperation between two spacial points in Mpc/h.
        z: float, optional
            Redshift (default is 0).
        linear: bool, optional
            If true (default) return the linear model, else non-linear.
        
        Returns
        -------
        y: array_like
            Values of derivative of variance.

        Examples
        --------
        
        """

        return self.power_spectrum.d2lnsdlnr2( r, z, linear )

    def effectiveIndex(self, k: Any, z: float = 0, linear: bool = True) -> Any:
        r"""
        Compute the effective slope or index of the power spectrum.

        .. math::
            n_{\rm eff}(k, z) = \frac{ {\rm d}\ln P(k,z) }{ {\rm d}\ln k }

        Parameters
        ----------
        k: array_like
            Wavenumber in h/Mpc.
        z: float, optional
            Redshift (default is 0).
        linear: bool, optional
            If true (default) return the slope for linear model, else non-linear.

        Returns
        -------
        neff: array_like
            Effective slope at given wavenumber.

        Examples
        --------

        """

        return self.power_spectrum.effectiveIndex( k, z, linear )

    def nonlineark(self, k: Any, z: float = 0) -> Any:
        r"""
        Compute the non-linear wavenumber corresponding to a linear one.

        Parameters
        ----------
        k: array_like
            linear wavenumber in h/Mpc.
        z: float, optional
            Redshift (default is 0).

        Returns
        -------
        knl: array_like
            Non-linear wavenumber in h/Mpc.

        Examples
        --------
        
        """

        return self.power_spectrum.nonlineark( k, z )
        
    # halo mass function, bias and related calculations

    def lagrangianR(self, m: Any) -> Any:
        r"""
        Compute the Lagrangian radius corresponding to a mass.

        Parameters
        ----------
        m: array_like
            Mass in Msun/h.

        Returns
        -------
        r: array_like
            Lagrangian radius in Mpc/h.

        Examples
        --------

        """

        m = np.asfarray( m ) # Msun/h
        return np.cbrt( 0.75*m / ( np.pi * self.rho_m( 0 ) ) )

    def lagrangianM(self, r: Any) -> Any:
        r"""
        Compute the mass corresponding to a Lagrangian radius.

        Parameters
        ----------
        r: array_like
            Lagrangian radius in Mpc/h.
        
        Returns
        -------
        m: array_like
            Mass in Msun/h.

        Examples
        --------
        
        """

        r = np.asfarray( r ) # Mpc/h
        return ( 4*np.pi / 3.0 ) * r**3 * self.rho_m( 0 )

    def collapseOverdensity(self, z: Any) -> float:
        """
        Critical value for the spherical collapse overdensity. It's value is approximately 1.686.

        Parameters
        ----------
        z: array_like
            Redshift. In general, it has a very small redshift dependence. But, here it is taken as a 
            constant in time. So, value of this argument is unused, except the shape.

        Returns
        -------
        delta_c: array_like
            Value of the collapse overdensity.

        Examples
        --------

        """

        return const.DELTA_C * np.ones_like( z, 'float' )

    def massFunction(self, m: Any, z: float = 0, overdensity: OverDensityType = None, out: str = 'dndlnm') -> Any:
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

        Examples
        --------

        """

        return self.mass_function.massFunction( m, z, overdensity, out )
    
    def peakHeight(self, m: Any, z: float = 0) -> Any:
        r"""
        Return the peak height :math:`\nu = \delta_c / \sigma(M)`.

        Parameters
        ----------
        m: array_like
            Mass of the overdensity/halo in Msun/h.
        z: float, optional
            Redshift (default is 0).

        Returns
        -------
        nu: array_like
            Peak height

        Examples
        --------
        
        """

        m  = np.asfarray( m )
        r  = self.lagrangianR( m )
        nu = self.collapseOverdensity( z ) / np.sqrt( self.variance( r, z ) )
        return nu

    def linearBias(self, m: Any, z: float = 0, overdensity: OverDensityType = None) -> Any:
        r"""
        Compute the linear halo bias of a given model.

        Parameters
        ----------
        m: array_like
            Mass of the halo in Msun/h.
        z: float, optional
            Redshift (default is 0).
        overdensity: str, int, OverDensity, optional
            Value of the overdensity. It could be an integer value of overdensity w.r.to the mean background density, 
            a string indicating the value such as `200m`, `vir` etc., or an :class:`OverDensity` object. For FoF type 
            halos, its default value is None (not used) and for spherical overdensity (SO) halos, it is 200.

        Returns
        -------
        bias: array_like
            Linear halo bias values.
        
        Examples
        --------

        """

        nu = self.peakHeight( m, z )
        return self.linear_bias.b( nu, z, overdensity )


