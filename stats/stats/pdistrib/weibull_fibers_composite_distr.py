'''
Created on Jun 6, 2013

@author: rostar
'''

from etsproxy.traits.api import HasTraits, Float
import numpy as np
from math import pi
from scipy.integrate import cumtrapz
from mathkit.mfn.mfn_line.mfn_line import MFnLineArray


def H(x):
    return x >= 0.0


class WeibullFibers(HasTraits):
    '''meta class for the distribution of strength of Weibull fibers'''
    m = Float(5.)
    sV0 = Float(1.)
    V0 = Float(1.)


class fibers_dry(WeibullFibers):
    ''' distribution of strength of brittle fibers with flaws following
        the compound Poisson process.
        input parameters:   m = rate of the Poisson process / Weibull modulus
                            sV0 = scale parameter of flaw strength (in strain per volume unit)
                            V0 = reference volume (default 1.0)
                            r = fiber radius
                            L = fiber length'''

    def cdf(self, e, r, L):
        sV0, m = self.sV0, self.m
        s = (sV0 ** m * self.V0 / (L * r ** 2 * pi)) ** (1./m)
        return 1. - np.exp(- (e/s)**m)
    
    def pdf(self, e, r, L):
        cdf_line = MFnLineArray(xdata=e, ydata=self.cdf(e, r, L))
        return cdf_line.get_diffs(e)


class fibers_CB_rigid(WeibullFibers):
    ''' distribution of strength of brittle fibers-in-composite with flaws following
        the compound Poisson process.
        Single crack bridge with rigid matrix = fibers have strain e at the crack plane
        and 0 at the end of the debonded length a.
        input parameters:   m = rate of the Poisson process / Weibull modulus
                            sV0 = scale parameter of flaw strength (in strain per volume unit)
                            V0 = reference volume (default 1.0)
                            r = fiber radius
                            tau = bond strength
                            Ef = fiber modulus of elasticity'''

    def cdf(self, e, depsf, r):
        '''weibull_fibers_cdf_cb_rigid'''
        sV0, m = self.sV0, self.m
        s = ((depsf*(m+1)*sV0**m*self.V0)/(2.*pi*r**2))**(1./(m+1))
        return 1. - np.exp(-(e/s) ** (m + 1))

    def pdf(self, e, depsf, r):
        cdf_line = MFnLineArray(xdata=e, ydata=self.cdf(e, depsf, r))
        return cdf_line.get_diffs(e)
    

class fibers_CB_elast(WeibullFibers):
    ''' distribution of strength of brittle fibers-in-composite with flaws following
        the compound Poisson process.
        Single crack bridge with elastic matrix = fibers have strain e at the crack plane
        and debond up to the distance a where the fiber strain equals the matrix strain.
        input parameters:   m = rate of the Poisson process / Weibull modulus
                            sV0 = scale parameter of flaw strength (in strain per volume unit)
                            V0 = reference volume (default 1.0)
                            r = fiber radius
                            tau = bond strength
                            Ef = fiber modulus of elasticity
                            a = debonded length'''

    def cdf(self, e, depsf, r, al, ar):
        '''weibull_fibers_cdf_cb_elast'''
        sV0, m = self.sV0, self.m
        s = ((depsf*(m+1.)*sV0**m*self.V0)/(pi*r**2.))**(1./(m+1.))
        a0 = e/depsf
        expL = (e/s) ** (m + 1) * (1.-(1.-al/a0)**(m+1.))
        expR = (e/s) ** (m + 1) * (1.-(1.-ar/a0)**(m+1.))
        return 1. - np.exp(-expL-expR)

    def pdf(self, e, depsf, r, al, ar):
        cdf_line = MFnLineArray(xdata=e, ydata=self.cdf(e, depsf, r, al, ar))
        return cdf_line.get_diffs(e)


class fibers_MC(WeibullFibers):
    ''' distribution of strength of brittle fibers-in-composite with flaws following
        the compound Poisson process.
        Multiple cracking is considered. In the analysed crack bridge, fibers have symmetry
        condition from left Ll and right Lr. Fiber strain beyond these conditions is assumed
        to be periodical.
        input parameters:   m = rate of the Poisson process / Weibull modulus
                            sV0 = scale parameter of flaw strength (in strain per volume unit)
                            V0 = reference volume (default 1.0)
                            r = fiber radius
                            tau = bond strength
                            Ef = fiber modulus of elasticity
                            Ll = symmetry condition left
                            Lr = symmetry condition right'''

    Ll = Float(1e10)
    Lr = Float(1e10)

    def cdf(self, e, depsf, r, al, ar):
        '''weibull_fibers_cdf_mc'''
        Ll, Lr, m, sV0 = self.Ll, self.Lr, self.m, self.sV0
        s = ((depsf*(m+1.)*sV0**m*self.V0)/(pi*r**2.))**(1./(m+1.))
        a0 = (e+1e-15)/depsf
        expLfree = (e/s) ** (m + 1) * (1.-(1.-al/a0)**(m+1.))
        expLfixed = a0 / Ll * (e/s) ** (m + 1) * (1.-(1.-Ll/a0)**(m+1.))
        maskL = al < Ll
        expL = expLfree * maskL + expLfixed * (maskL == False)
        expRfree = (e/s) ** (m + 1) * (1.-(1.-ar/a0)**(m+1.))
        expRfixed = a0 / Lr * (e/s) ** (m + 1) * (1.-(1.-Lr/a0)**(m+1.))
        maskR = ar < Lr
        expR = expRfree * maskR + expRfixed * (maskR == False)
        return 1. - np.exp(- expL - expR)

    def cdf2(self, e, depsf, r):
        lm, m, sV0 = 2*self.Ll, self.m, self.sV0
        #scale parameter with respect to a reference volume
        s = ((depsf**2 * (m+1) * sV0**m * lm)/(4. * pi * r ** 2))**(1./(m+2))
        a = e / depsf
        return 1. - np.exp(-(e/s)**(m+2) * (1.-(1.-lm/2./a)**(m+1)))

    def pdf(self, e, depsf, r, al, ar):
        cdf_line = MFnLineArray(xdata=e, ydata=self.cdf(e, depsf, r, al, ar))
        return cdf_line.get_diffs(e)

    def pdf2(self, e, depsf, r):
        lm, m, sV0 = 2*self.Ll, self.m, self.sV0
        #scale parameter with respect to a reference volume
        s = ((depsf**2 * (m+1) * sV0**m * lm)/(4. * pi * r ** 2))**(1./(m+2))
        a = e / depsf
        return 1. - np.exp(-(e/s)**(m+2) * (1.-(1.-lm/2./a)**(m+1)))
    
    def cdf_exact(self, e, depsf, r):
        CDF = []
        m, sV0 = self.m, self.sV0
        for ei in e:
            ai = ei / depsf
            z = np.linspace(0.0, ai, 5000)
            mask = np.sin(pi / self.Ll * z) > 0.0
            depsfi = depsf * mask - depsf * (mask == False)
            f = np.hstack((0.0, cumtrapz(depsfi, z)))
            f = ei - f
            CDFi = 1. - np.exp(- pi * r ** 2 / sV0 ** m * 2.0 * np.trapz(f**m, z))
            CDF.append(CDFi)
        return np.array(CDF)


if __name__ == '__main__':
    from matplotlib import pyplot as plt
    from scipy.integrate import cumtrapz
    r = 0.00345
    tau = 0.1
    Ef = 200e3
    m = 3.0
    sV0 = 0.0026
    e = np.linspace(0.001, 0.1, 100)
    a = e * Ef / (2. * tau / r)
    L = 10.0
    rat = 2.*a/L
    wfd = fibers_dry(m=m, sV0=sV0)
    CDF = wfd.cdf(e, r, 2*a)
    #plt.plot(rat, CDF, label='Phoenix 1992')
    plt.plot(np.log(rat), np.log(-np.log(1.0 - CDF)), label='Phoenix 1992')
    #wfcbe = fibers_CB_elast(m=m, sV0=sV0)
    #CDF = wfcbe.cdf(e, 2*tau/Ef/r, r, 0.1 * a, 0.1 * a)
    #plt.plot(e, CDF, label='CB')
    wfcbr = fibers_CB_rigid(m=m, sV0=sV0)
    CDF = wfcbr.cdf(e, 2*tau/Ef/r, r)
    #plt.plot(rat, CDF, label='CB rigid')
    plt.plot(np.log(rat), np.log(-np.log(1.0 - CDF)), label='CB rigid')
    wfmc = fibers_MC(m=m, sV0=sV0, Ll=L, Lr=L)
    CDFexct = wfmc.cdf_exact(e, 2*tau/Ef/r, r)
    CDF = wfmc.cdf(e, 2*tau/Ef/r, r, a, a)
    #CDF2 = wfmc.cdf2(e, 2*tau/Ef/r, r)
    plt.plot(np.log(rat), np.log(-np.log(1.0 - CDF)), label='MC')
    plt.plot(np.log(rat), np.log(-np.log(1.0 - CDFexct)), label='exact')
    #plt.plot(rat, CDF, label='MC')
    #plt.plot(rat, CDFexct, label='exact')
    #plt.ylim(0)
    plt.legend(loc='best')
    plt.show()


