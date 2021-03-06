from typing import Any
from pycosmo.cosmology.cosmo import Cosmology, CosmologyError
from pycosmo.cosmology.cosmo import PowerSpectrumType, MassFunctionType, LinearBiasType

class Cosmology_wMDM(Cosmology):
    r"""
    A wMDM cosmology model with mixed dark-matter and constant equation of state dark-energy.

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
    w: float, optional
        Equation of state parameter for dark-energy. Its default value is -1.
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

    def __init__(
                    self, h: float, Om0: float, Ob0: float, sigma8: float, ns: float, flat: bool = True, 
                    relspecies: bool = False, Ode0: float = None, Omnu0: float = 0, Nmnu: float = None, 
                    Tcmb0: float = 2.725, w: float = -1, Nnu: float = 3, 
                    power_spectrum: PowerSpectrumType = None, filter: str = 'tophat', 
                    mass_function: MassFunctionType = 'tinker08', linear_bias: LinearBiasType = 'tinker10'
                ) -> None:

        super().__init__(
                            h, Om0, Ob0, sigma8, ns, flat, relspecies, Ode0, Omnu0, Nmnu, Tcmb0, w, Nnu, 
                            power_spectrum, filter, mass_function, linear_bias, 
                            wa = 0
                        )

class Cosmology_flat_wMDM(Cosmology_wMDM):
    r"""
    A flat wMDM cosmology model.

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
    relspecies: bool, optional
        Tells if the model contains relativistic species or radiation (default is false).
    Omnu0: float, optional
        Present density of *massive* neutrinos in units of critical density. Must be non-negative. Default 
        value is 0, means no massive neutrinos.
    Nmnu: float, optional
        Number of massive neutrino species. Must be a non-zero, positive value, and it is required when there 
        is massive neutrinos.
    Tcmb0: float, optional
        Present temperature of the CMB in kelvin (default 2.275K).
    w: float, optional
        Equation of state parameter for dark-energy. Its default value is -1.
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

    def __init__(
                    self, h: float, Om0: float, Ob0: float, sigma8: float, ns: float, relspecies: bool = False, 
                    Omnu0: float = 0, Nmnu: float = None, Tcmb0: float = 2.725, w: float = -1, Nnu: float = 3, 
                    power_spectrum: PowerSpectrumType = None, filter: str = 'tophat', 
                    mass_function: MassFunctionType = 'tinker08', linear_bias: LinearBiasType = 'tinker10'
                ) -> None:

        super().__init__(
                            h, Om0, Ob0, sigma8, ns, relspecies, Omnu0, Nmnu, Tcmb0, w, Nnu, 
                            power_spectrum, filter, mass_function, linear_bias, 
                            flat = True, Ode0 = None
                        )

class Cosmology_wCDM(Cosmology_wMDM):
    r"""
    A wCDM cosmology model with constant equation of state dark-energy and cold dark-matter.

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
    Tcmb0: float, optional
        Present temperature of the CMB in kelvin (default 2.275K).
    w: float, optional
        Equation of state parameter for dark-energy. Its default value is -1.
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

    def __init__(
                    self, h: float, Om0: float, Ob0: float, sigma8: float, ns: float, flat: bool = True, 
                    relspecies: bool = False, Ode0: float = None, Tcmb0: float = 2.725, w: float = -1, Nnu: float = 3, 
                    power_spectrum: PowerSpectrumType = None, filter: str = 'tophat', 
                    mass_function: MassFunctionType = 'tinker08', linear_bias: LinearBiasType = 'tinker10'
                ) -> None:

        super().__init__(
                            h, Om0, Ob0, sigma8, ns, flat, relspecies, Ode0, Tcmb0, w, Nnu, 
                            power_spectrum, filter, mass_function, linear_bias, 
                            Omnu0 = 0, Nmnu = None
                        )

class Cosmology_LambdaCDM(Cosmology_wCDM):
    r"""
    A :math:`\Lambda`-CDM cosmology model with cosmological constant and cold dark-matter.

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
    Tcmb0: float, optional
        Present temperature of the CMB in kelvin (default 2.275K).
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

    def __init__(
                    self, h: float, Om0: float, Ob0: float, sigma8: float, ns: float, flat: bool = True, 
                    relspecies: bool = False, Ode0: float = None, Tcmb0: float = 2.725, Nnu: float = 3, 
                    power_spectrum: PowerSpectrumType = None, filter: str = 'tophat', 
                    mass_function: MassFunctionType = 'tinker08', linear_bias: LinearBiasType = 'tinker10'
                ) -> None:

        super().__init__(
                            h, Om0, Ob0, sigma8, ns, flat, relspecies, Ode0, Tcmb0, Nnu, 
                            power_spectrum, filter, mass_function, linear_bias, 
                            w = -1
                        )

class Cosmology_flat_LambdaCDM(Cosmology_LambdaCDM):
    r"""
    A flat :math:`\Lambda`-CDM cosmology model.

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
    relspecies: bool, optional
        Tells if the model contains relativistic species or radiation (default is false).
    Tcmb0: float, optional
        Present temperature of the CMB in kelvin (default 2.275K).
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

    def __init__(
                    self, h: float, Om0: float, Ob0: float, sigma8: float, ns: float, 
                    relspecies: bool = False, Tcmb0: float = 2.725, Nnu: float = 3, 
                    power_spectrum: PowerSpectrumType = None, filter: str = 'tophat', 
                    mass_function: MassFunctionType = 'tinker08', linear_bias: LinearBiasType = 'tinker10'
                ) -> None:

        super().__init__(
                            h, Om0, Ob0, sigma8, ns, relspecies, Tcmb0, Nnu, 
                            power_spectrum, filter, mass_function, linear_bias, 
                            flat = True, Ode0 = None
                        )

class Einstein_deSitter(Cosmology_flat_LambdaCDM):
    r"""
    Einstein - de Sitter cosmology model. It is a model where only dark matter is present and geometry is flat.

    Parameters
    ----------
    h: float
        Present value of Hubble parameter in 100 km/sec/Mpc.
    sigma8: float
        RMS fluctuation of the matter density field at 8 Mpc/h scale. Must be non-negative. 
    ns: float
        Power law index for the early power spectrum.
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

    def __init__(
                    self, h: float, sigma8: float, ns: float, power_spectrum: PowerSpectrumType = None, filter: str = 'tophat', mass_function: MassFunctionType = 'tinker08', linear_bias: LinearBiasType = 'tinker10'
                ) -> None:

        super().__init__(
                            h, Om0 = 1.0, Ob0 = 0.0, sigma8 = sigma8, ns = ns, relspecies = False, Tcmb0 = 2.725, Nnu = 0, 
                            power_spectrum = power_spectrum, filter = filter, mass_function = mass_function, linear_bias = linear_bias
                        )



######################################################################################################

# pre-defines cosmology models 

class Predefined:
    r"""
    Pre-defined cosmology models.
    """

    def plank15(flat: bool = False, relspecies: bool = False, power_spectrum: PowerSpectrumType = None, mass_function: MassFunctionType = None, linear_bias: LinearBiasType = None, filter: str = 'tophat') -> Cosmology:
        r"""
        Return the cosmology with parameters from Plank et al (2015). The returned model will be a :math:`\Lambda`-CDM model. 
        Parameters are from 3-rd column of Table 4 in [1]_.
        
        Parameters
        ----------
        flat: bool, optional
            Tells the spatial geometry. Default is a non-flat geometry.
        relspecies: bool, optional
            Tells if the model contains relativistic species or radiation (default is false).
        power_spectrum: str, PowerSpectrum, optional 
            Tell the linear matter power spectrum (or, transfer function) model to use. Default model is Eisenstein-
            Hu model without baryon oscillations. 
        filter: str, optional
            Filter used to smooth the density field. Default is a spherical tophat (`tophat`). 
        mass_function: str, HaloMassFunction, optional
            Tell the halo mass function model to use. Default is the model by Tinker et al (2008). 
        linear_bias: str, optional
            Tell the linear bias model to use. Default is Tinker et al (2010).

        Returns
        ------
        Cosmology:
            Cosmology model.

        References
        ----------
        .. [1] Plank collaboration. Planck 2015 results. XIII. Cosmological parameters. arXive:1502.01589v3.

        """
        return Cosmology_LambdaCDM( 
                                        h = 0.6790, Om0 = 0.3065, Ob0 = 0.0483, Ode0 = 0.6935, sigma8 = 0.8154, ns = 0.9681, Tcmb0 = 2.7255,
                                        Nnu = 3.046, flat = flat, relspecies = relspecies, power_spectrum = power_spectrum, filter = filter,
                                        mass_function = mass_function, linear_bias = linear_bias
                                  )

    def plank18(flat: bool = False, relspecies: bool = False, power_spectrum: PowerSpectrumType = None, mass_function: MassFunctionType = None, linear_bias: LinearBiasType = None, filter: str = 'tophat') -> Cosmology:
        r"""
        Return the cosmology with parameters from Plank et al (2018). The returned model will be a :math:`\Lambda`-CDM model. 
        Parameters are from 5-th column of Table 2 in [1]_.
        
        Parameters
        ----------
        flat: bool, optional
            Tells the spatial geometry. Default is a non-flat geometry.
        relspecies: bool, optional
            Tells if the model contains relativistic species or radiation (default is false).
        power_spectrum: str, PowerSpectrum, optional 
            Tell the linear matter power spectrum (or, transfer function) model to use. Default model is Eisenstein-
            Hu model without baryon oscillations. 
        filter: str, optional
            Filter used to smooth the density field. Default is a spherical tophat (`tophat`). 
        mass_function: str, HaloMassFunction, optional
            Tell the halo mass function model to use. Default is the model by Tinker et al (2008). 
        linear_bias: str, optional
            Tell the linear bias model to use. Default is Tinker et al (2010).

        Returns
        ------
        Cosmology:
            Cosmology model.

        References
        ----------
        .. [1] Plank collaboration. Planck 2018 results. VI. Cosmological parameters. arXive:1807.06209v3.

        """
        return Cosmology_LambdaCDM( 
                                        h = 0.6736, Om0 = 0.3153, Ob0 = 0.0493, Ode0 = 0.6947, sigma8 = 0.8111, ns = 0.9649, Tcmb0 = 2.7255,
                                        Nnu = 3.046, flat = flat, relspecies = relspecies, power_spectrum = power_spectrum, filter = filter,
                                        mass_function = mass_function, linear_bias = linear_bias
                                  )
    
    def wmap08(flat: bool = False, relspecies: bool = False, power_spectrum: PowerSpectrumType = None, mass_function: MassFunctionType = None, linear_bias: LinearBiasType = None, filter: str = 'tophat') -> Cosmology:
        r"""
        Return the cosmology with parameters from WMAP survay. The returned model will be a :math:`\Lambda`-CDM model. 
        Parameters are from WMAP-only column in Table 7 in [1]_.
        
        Parameters
        ----------
        flat: bool, optional
            Tells the spatial geometry. Default is a non-flat geometry.
        relspecies: bool, optional
            Tells if the model contains relativistic species or radiation (default is false).
        power_spectrum: str, PowerSpectrum, optional 
            Tell the linear matter power spectrum (or, transfer function) model to use. Default model is Eisenstein-
            Hu model without baryon oscillations. 
        filter: str, optional
            Filter used to smooth the density field. Default is a spherical tophat (`tophat`). 
        mass_function: str, HaloMassFunction, optional
            Tell the halo mass function model to use. Default is the model by Tinker et al (2008). 
        linear_bias: str, optional
            Tell the linear bias model to use. Default is Tinker et al (2010).

        Returns
        ------
        Cosmology:
            Cosmology model.

        References
        ----------
        .. [1] G. Hinshaw et al. Five-Year Wilkinson Microwave Anisotropy Probe (WMAP) Observations: Data Processing, 
                Sky Maps, & Basic Results. <http://arXiv.org/abs/0803.0732v2>.

        """
        return Cosmology_LambdaCDM( 
                                        h = 0.719, Om0 = 0.2581, Ob0 = 0.0441, Ode0 = 0.742, sigma8 = 0.796, ns = 0.963, Tcmb0 = 2.7255,
                                        Nnu = 3.046, flat = flat, relspecies = relspecies, power_spectrum = power_spectrum, filter = filter,
                                        mass_function = mass_function, linear_bias = linear_bias
                                  )

    def millanium(power_spectrum: PowerSpectrumType = None, mass_function: MassFunctionType = None, linear_bias: LinearBiasType = None, filter: str = 'tophat') -> Cosmology:
        r"""
        Return the cosmology with parameters of millanium simulation [1]_. The returned model will be a :math:`\Lambda`-CDM model. 
        
        Parameters
        ----------
        power_spectrum: str, PowerSpectrum, optional 
            Tell the linear matter power spectrum (or, transfer function) model to use. Default model is Eisenstein-
            Hu model without baryon oscillations. 
        filter: str, optional
            Filter used to smooth the density field. Default is a spherical tophat (`tophat`). 
        mass_function: str, HaloMassFunction, optional
            Tell the halo mass function model to use. Default is the model by Tinker et al (2008). 
        linear_bias: str, optional
            Tell the linear bias model to use. Default is Tinker et al (2010).

        Returns
        ------
        Cosmology:
            Cosmology model.

        References
        ----------
        .. [1] Volker Springel et al. Simulating the joint evolution of quasars, galaxies and their large-scale distribution.
                <http://arXiv.org/abs/astro-ph/0504097v2>

        """
        return Cosmology_flat_LambdaCDM( 
                                            h = 0.73, Om0 = 0.25, Ob0 = 0.045, sigma8 = 0.9, ns = 1.0, Tcmb0 = 2.7255, 
                                            relspecies = False, power_spectrum = power_spectrum, filter = filter,
                                            mass_function = mass_function, linear_bias = linear_bias
                                       )

        

