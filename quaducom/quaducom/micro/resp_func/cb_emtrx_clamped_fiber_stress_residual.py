#---#-------------------------------------------------------------------------------
#
# Copyright (c) 2009, IMB, RWTH Aachen.
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in simvisage/LICENSE.txt and may be redistributed only
# under the conditions described in the aforementioned license.  The license
# is also available online at http://www.simvisage.com/licenses/BSD.txt
#
# Thanks for using Simvisage open source!
#
# Created on Jun 14, 2010 by: rch

from etsproxy.traits.api import \
    Float, Str, implements, Range

import numpy as np

from stats.spirrid.i_rf import \
    IRF

from stats.spirrid.rf import \
    RF

from matplotlib import pyplot as plt

from scipy.stats import weibull_min

def H(x):
    return 0.5 * (np.sign(x) + 1.)

class CBEMClampedFiberStressResidual(RF):
    '''
    Crack bridged by a fiber with constant
    frictional interface to the elastic matrix; clamped fiber end;
    Gives tension.
    '''

    implements(IRF)

    title = Str('crack bridge - clamped fiber with constant friction')

    Pf = Range(0,1,auto_set=False, enter_set=True, input=True,
                distr=['uniform'])
    
    m = Float(5.0, auto_set=False, enter_set=True, input=True,
                distr=['weibull_min', 'uniform'], desc = 'filament Weibull shape parameter')
    
    s0 = Float(.02, auto_set=False, enter_set=True, input=True,
                distr=['weibull_min', 'uniform'], desc = 'filament Weibull scale parameter at l = 10 mm')

    tau = Float(2.5, auto_set=False, enter_set=True, input=True,
                distr=['uniform', 'norm'])

    l = Float(10.0, auto_set=False, enter_set=True, input=True,
              distr=['uniform'], desc='free length')

    r = Float(0.013, auto_set=False, input=True,
              enter_set=True, desc='fiber radius in mm')

    E_f = Float(72e3, auto_set=False, enter_set=True, input=True,
                  distr=['uniform'])

    E_m = Float(30e3, auto_set=False, enter_set=True, input=True,
                  distr=['uniform'])

    V_f = Float(0.0175, auto_set=False, enter_set=True, input=True,
              distr=['uniform'])

    theta = Float(0.01, auto_set=False, enter_set=True, input=True,
                  distr=['uniform', 'norm'], desc='slack')

    phi = Float(1., auto_set=False, enter_set=True, input=True,
                  distr=['uniform', 'norm'], desc='bond quality')

    Ll = Float(1., auto_set=False, enter_set=True, input=True,
              distr=['uniform'], desc='embedded length - left',
               ctrl_range=(0.0, 1.0, 10))

    Lr = Float(.5, auto_set=False, enter_set=True, input=True,
              distr=['uniform'], desc='embedded length - right',
               ctrl_range=(0.0, 1.0, 10))

    w = Float(auto_set=False, enter_set=True, input=True,
               distr=['uniform'], desc='crack width',
               ctrl_range=(0.0, 1.0, 10))

    x = Float(auto_set=False, enter_set=True, input=True,
               distr=['uniform'], desc='crack width',
               ctrl_range=(0.0, 1.0, 10))

    x_label = Str('crack opening [mm]')
    y_label = Str('force [N]')

    C_code = Str('')
    
    def crackbridge(self, w, l, T , Kf, Km, V_f):
        #Phase A : Both sides debonding .
        Kc = Kf + Km
        c = Kc * T * l/2.
        q0 = (np.sqrt(c**2 + w*Kf*Km*Kc*T) - c)/Km
        return q0/V_f

    def pullout(self, w, l, T, Kf, Km, V_f, Lmin, Lmax):
        #Phase B : Debonding of shorter side is finished
        Kc = Kf + Km
        c = Kc*T*(Lmin + l)
        f = T**2*Lmin**2*Kc**2
        q1 = (np.sqrt(c ** 2. + f + 2*w*Kc*T*Kf*Km) - c)/Km
        return q1/V_f

    def linel(self, w, l, T, Kf, Km, V_f, Lmax, Lmin):
        #Phase C: Both sides debonded - linear elastic behavior.
        Kc = Kf + Km
        q2 = (2.*w*Kf*Km + T*Kc*(Lmin**2+Lmax**2))/(2.*Km *(Lmax + l + Lmin))
        return q2/V_f

    def eps_n(self, q, tau, x, E_f, E_m, V_f, r, l, theta):
        q = q.reshape(tuple(list(q.shape)+[1]))
        x = x.reshape(tuple((len(q.shape) - 1)*[1]+[len(x)]))
        q = q * np.ones_like(q*x)
        x = x * np.ones_like(q)
        T = 2. * tau * V_f / r            
        #stress in the free length
        l = l * (1 + theta)
        q_l = q * H(l / 2 - abs(x))
        #stress in the part, where fiber transmits stress to the matrix
        q_e = (q - T/V_f * (abs(x) - l / 2.)) * H(abs(x) - l / 2.)
        
        #far field stress
        E_c = E_m * (1-V_f) + E_f * V_f
        q_const = q * V_f * E_f / E_c
        
        #putting all parts together
        q_x = q_l + q_e
        q_x = np.maximum(q_x, q_const)
        return q_x/E_f

    def CDF_n(self,s0,m,n_eps):
        return weibull_min(m, scale = s0).cdf(n_eps)

    def __call__(self, w, tau, l, E_f, E_m, theta, Pf, phi, Ll, Lr, V_f, r, s0, m):
        np.random.seed(10)
        #assigning short and long embedded length
        Lmin = np.minimum(Ll, Lr)
        Lmax = np.maximum(Ll, Lr)
        
        Lmin = np.maximum(Lmin - l / 2., 1e-15)
        Lmax = np.maximum(Lmax - l / 2., 1e-15)

        #maximum condition for free length
        l = np.minimum(l / 2., Lr) + np.minimum(l / 2., Ll)
        
        #defining variables
        w = w - theta * l
        l = l * (1 + theta)
        w = H(w) * w
        T = 2. * tau * V_f / r
        Km = (1. - V_f) * E_m
        Kf = V_f * E_f
        Kc = Km + Kf
        
        # double sided debonding
        #q0 = self.crackbridge(w, l, T, Kr, Km, Lmin, Lmax)
        q0 = self.crackbridge(w, l, T, Kf, Km, V_f)

        # displacement at which the debonding to the closer clamp is finished
        w0 = (Lmin+l)*Lmin*Kc*T/Kf/Km
        
        # debonding of one side; the other side is clamped
        q1 = self.pullout(w, l, T, Kf, Km, V_f, Lmin, Lmax)
        
        # displacement at which the debonding is finished at both sides
        e1 = Lmax*Kc*T/Km/Kf
        w1 = e1*(l+Lmax/2.)+(e1+e1*Lmin/Lmax)*Lmin/2.
        
        # debonding completed at both sides, response becomes linear elastic
        q2 = self.linel(w , l, T, Kf, Km, V_f, Lmax, Lmin)

        # cut out definition ranges 
        q0 = H(w) * (q0 + 1e-15) * H(w0 - w)
        q1 = H(w - w0) * q1 * H(w1 - w)
        q2 = H(w - w1) * q2
        
        #add all parts
        q = q0 + q1 + q2

        # include breaking strain
        n = (Ll + Lr)/10.
        if n < 1.0:
            n = 1
        else:
            n = int(n)
        # within a crack bridge divide the filament into parts with constant strengths
        x_n = np.linspace(-Ll, Lr, n)
        # create an array of strains along these parts
        eps_n = self.eps_n(q, tau, x_n, E_f, E_m, V_f, r, l, theta)
        # evaluate failure probabilities for these parts
        CDF_n = self.CDF_n(s0,m,eps_n)
        # survival probability of the whole system along x_n
        sf = 1-CDF_n
        chain_sf = sf.prod(axis = len(CDF_n.shape) - 1)
        # compare failure probability of the chain of the chain with Pf of xi
        # index of filament failure
        flat_idx_ult = np.argmin(np.abs(1-chain_sf - Pf))
        idx_ult = np.unravel_index(flat_idx_ult, chain_sf.shape)
        # position of fiber breakage
        rand = np.random.rand(n)
        L_idx = np.argmax(CDF_n[idx_ult]*rand)
        # residual bonded length
        if np.abs(x_n[L_idx]) < l/2.:
            L_res = 0.0
        else:
            L_res = np.abs(x_n[L_idx]) - l/2.
        q = q * H(Pf - (1-chain_sf)) + L_res * T / V_f * H((1-chain_sf) - Pf)
        return q
    
class CBEMClampedFiberStressResidualSP(CBEMClampedFiberStressResidual):
        '''
        stress profile for a crack bridged by a fiber with constant
        frictional interface to the matrix; clamped fiber end
        '''
        x = Float(0.0, auto_set=False, enter_set=True, input=True,
                  distr=['uniform'], desc='distance from crack')
    
        x_label = Str('position [mm]')
        y_label = Str('force [N]')
    
        C_code = Str('')

        def __call__(self, w, x, tau, l, E_f, E_m, theta, Pf, phi, Ll, Lr, V_f, r, s0, m):
            T = 2. * tau * V_f / r    
            q = super(CBEMClampedFiberStressResidualSP, self).__call__(w, tau, l, E_f, E_m, theta, Pf, phi, Ll, Lr, V_f, r,s0,m)            
            #stress in the free length
            l = l * (1 + theta)  
            q_l = q * H(l / 2 - abs(x))
            #stress in the part, where fiber transmits stress to the matrix
            q_e = (q - T/V_f * (abs(x) - l / 2.)) * H(abs(x) - l / 2.)
            #q_e = q_e * H(x + Ll) * H (Lr - x)
            
            #far field stress
            E_c = E_m * (1-V_f) + E_f * V_f
            q_const = q * V_f * E_f / E_c
            
            #putting all parts together
            q_x = q_l + q_e
            q_x = np.maximum(q_x, q_const)
            return q_x

if __name__ == '__main__':

    r = 0.00345
    V_f = 0.0103
    t = .1
    Ef = 200e3
    Em = 25e3
    l = 30.
    theta = 0.
    Pf = 0.5
    phi = 1.
    Ll = 40.
    Lr = 20.
    s0 = 0.02
    m = 5.0
    
    def Pw():
        plt.figure()
        w = np.linspace(0, 1, 300)
        P = CBEMClampedFiberStressResidual()
        q = P(w, t, l, Ef, Em, theta, Pf, phi, Ll, Lr, V_f, r, s0, m) 
        plt.plot(w, q, lw=2, ls='-', color='black', label='CB_emtrx_stress')
        #plt.legend(loc='best')
        plt.ylim(0,)
        plt.ylabel('stress', fontsize=14)
        plt.xlabel('w', fontsize=14)
        plt.title('Pullout Resp Func Clamped Fiber EMTRX')

    def SP():
        plt.figure()
        cbcsp = CBEMClampedFiberStressResidualSP()
        x = np.linspace(-40, 40, 300)
        w = .4
        q = cbcsp(w, x, t, l, Ef, Em, theta, Pf, phi, Ll, Lr, V_f, r, s0,m)
        plt.plot(x, q, lw=2, color='black', label='stress along filament')
        plt.ylabel('stress', fontsize=14)
        plt.xlabel('position', fontsize=14)
        plt.xticks(fontsize=14)
        plt.yticks(fontsize=14)
        plt.title('Stress Along Filament EMTRX at w = %.1f' %w)
        #plt.legend(loc='best')
        plt.ylim(0,)

    Pw()
    SP()
    plt.show()