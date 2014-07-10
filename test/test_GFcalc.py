"""
Unit tests for calculation of lattice Green function for diffusion
"""

__author__ = 'Dallas R. Trinkle'

import unittest
import numpy as np
from scipy import special
import onsager.FCClatt as FCClatt
import onsager.GFcalc as GFcalc

class GreenFuncDerivativeTests(unittest.TestCase):
    """Tests for the construction of D as a fourier transform, and the 2nd and 4th derivatives."""

    def setUp(self):
        self.NNvect = FCClatt.NNvect()
        self.rates = np.array((1,) * np.shape(self.NNvect)[0])
        self.DFT = GFcalc.DFTfunc(self.NNvect, self.rates)  # Fourier transform
        self.D2 = GFcalc.D2(self.NNvect, self.rates)  # - 2nd deriv. of FT (>0)
        self.D4 = GFcalc.D4(self.NNvect, self.rates)  # + 4th deriv. of FT (>0)

    def testFTisfunc(self):
        """Do we get a function as DFT?"""
        self.assertTrue(callable(self.DFT))

    def testFTfuncZero(self):
        """Is the FT zero at gamma?"""
        q = np.array((0, 0, 0))
        self.assertEqual(self.DFT(q), 0)

    def testFTfuncZeroRLV(self):
        """Is the FT zero for reciprocal lattice vectors?"""
        q = np.array((2 * np.pi, 0, 0))
        self.assertEqual(self.DFT(q), 0)
        q = np.array((2 * np.pi, 2 * np.pi, 0))
        self.assertEqual(self.DFT(q), 0)
        q = np.array((2 * np.pi, 2 * np.pi, 2 * np.pi))
        self.assertEqual(self.DFT(q), 0)

    def testFTfuncValues(self):
        """Do we match some specific values?
        Testing that we're negative, and "by hand" evaluation of a few cases.
        Note: equality here doesn't quite work due to roundoff error at the 15th digit"""
        q = np.array((1, 0, 0))
        self.assertTrue(self.DFT(q) < 0)  # negative everywhere...
        self.assertAlmostEqual(self.DFT(q), 8 * (np.cos(1) - 1))
        q = np.array((1, 1, 0))
        self.assertTrue(self.DFT(q) < 0)
        self.assertAlmostEqual(self.DFT(q), 2 * (np.cos(2) - 1) + 8 * (np.cos(1) - 1))
        q = np.array((1, 1, 1))
        self.assertTrue(self.DFT(q) < 0)
        self.assertAlmostEqual(self.DFT(q), 6 * (np.cos(2) - 1))

    def testFTfuncSymmetry(self):
        """Does our FT obey basic cubic symmetry operations?"""
        q = np.array((1, 0, 0))
        q2 = np.array((-1, 0, 0))
        self.assertEqual(self.DFT(q), self.DFT(q2))
        q2 = np.array((0, 1, 0))
        self.assertEqual(self.DFT(q), self.DFT(q2))
        q2 = np.array((0, 0, 1))
        self.assertEqual(self.DFT(q), self.DFT(q2))

    def testFTdim(self):
        """Do we have the correct dimensionality for our second and fourth derivatives?"""
        self.assertTrue(np.shape(self.D2) == (3, 3))
        self.assertTrue(np.shape(self.D4) == (3, 3, 3, 3))

    def testFTDiffSymmetry(self):
        """Do we obey basic symmetry for these values?
        That means that D2 should be symmetric, and that any permutation of [abcd]
        should give the same value in D4."""
        self.assertTrue(np.all(self.D2 == self.D2.T))
        self.assertEqual(self.D2[0, 0], self.D2[1, 1])
        self.assertEqual(self.D2[0, 0], self.D2[2, 2])
        for ind in [(a, b, c, d)
                    for a in xrange(3)
                    for b in xrange(3)
                    for c in xrange(3)
                    for d in xrange(3)]:
            inds = tuple(sorted(ind))
            self.assertEqual(self.D4[ind], self.D4[inds],
                             msg="{} vs {}".format(ind, inds))

    def testEval2(self):
        """Does eval2(q,D) give qDq?"""
        qvec = np.array((0.5, 0.75, -0.25))
        self.assertAlmostEqual(np.dot(qvec, np.dot(qvec, self.D2)),
                               GFcalc.eval2(qvec, self.D2))

    def testEval4(self):
        """Does eval4(q,D) gives qqDqq?"""
        qvec = np.array((0.5, 0.75, -0.25))
        self.assertAlmostEqual(np.dot(qvec, np.dot(qvec, np.dot(qvec, np.dot(qvec, self.D4)))),
                               GFcalc.eval4(qvec, self.D4))

    def testFTDiffValue(self):
        """Do the 2nd derivatives behave as expected, by doing a finite difference evaluation.
        Requires using a threshold value.
        """
        # Remember: D2 is negative of the second derivative (to make it positive def.)
        delta = 2.e-4
        eps = 1e-5
        qsmall = np.array((delta, 0, 0))
        D0 = self.DFT(qsmall)
        D2 = GFcalc.eval2(qsmall, self.D2)
        self.assertTrue(abs(D0 + D2) < eps * (delta ** 2))
        self.assertFalse(abs(D0) < eps * (delta ** 2))

        qsmall = np.array((delta, delta, 0))
        D0 = self.DFT(qsmall)
        D2 = GFcalc.eval2(qsmall, self.D2)
        self.assertTrue(abs(D0 + D2) < eps * (delta ** 2))
        self.assertFalse(abs(D0) < eps * (delta ** 2))

        qsmall = np.array((delta, delta, delta))
        D0 = self.DFT(qsmall)
        D2 = GFcalc.eval2(qsmall, self.D2)
        self.assertTrue(abs(D0 + D2) < eps * (delta ** 2))
        self.assertFalse(abs(D0) < eps * (delta ** 2))

    def testFTDiff4Value(self):
        """Do the 4th derivatives behave as expected, by doing a finite difference evaluation.
        Requires using a threshold value.
        """
        # Remember: D2 is negative of the second derivative (to make it positive def.)
        delta = 1e-1
        eps = 1e-1
        qsmall = np.array((delta, 0, 0))
        D = self.DFT(qsmall)
        D2 = GFcalc.eval2(qsmall, self.D2)
        D4 = GFcalc.eval4(qsmall, self.D4)
        self.assertTrue(abs(D + D2 - D4) < eps * (delta ** 4))
        self.assertFalse(abs(D + D2) < eps * (delta ** 4))

        qsmall = np.array((delta, delta, 0))
        D = self.DFT(qsmall)
        D2 = GFcalc.eval2(qsmall, self.D2)
        D4 = GFcalc.eval4(qsmall, self.D4)
        self.assertTrue(abs(D + D2 - D4) < eps * (delta ** 4))
        self.assertFalse(abs(D + D2) < eps * (delta ** 4))

        qsmall = np.array((delta, delta, delta))
        D = self.DFT(qsmall)
        D2 = GFcalc.eval2(qsmall, self.D2)
        D4 = GFcalc.eval4(qsmall, self.D4)
        self.assertTrue(abs(D + D2 - D4) < eps * (delta ** 4))
        self.assertFalse(abs(D + D2) < eps * (delta ** 4))


# code that does Fourier transforms
class GreenFuncFourierTransformPoleTests(unittest.TestCase):
    """Tests for code involved in the Fourier transform of the second-order pole."""

    def setUp(self):
        # di0/ei0 are the "original" eigenvalues / eigenvectors, and di/ei are the
        # calculated versions
        self.di0 = np.array([0.5, 1., 2.])
        self.ei0 = np.array([[np.sqrt(0.5), np.sqrt(0.5), 0],
                             [np.sqrt(1. / 6.), -np.sqrt(1. / 6.), np.sqrt(2. / 3.)],
                             [np.sqrt(1. / 3.), -np.sqrt(1. / 3.), -np.sqrt(1. / 3.)]])
        self.D2 = np.dot(self.ei0.T, np.dot(np.diag(self.di0), self.ei0))
        self.GF2_0 = np.dot(self.ei0.T, np.dot(np.diag(1. / self.di0), self.ei0))
        self.di, self.ei_vect = GFcalc.calcDE(self.D2)
        self.GF2 = GFcalc.invertD2(self.D2)

    def testEigendim(self):
        """Correct dimensionality of eigenvalues and vectors?"""
        self.assertTrue(np.shape(self.di) == (3,))
        self.assertTrue(np.shape(self.ei_vect) == (3, 3))

    def testEigenvalueVect(self):
        """Test that the eigenvalues and vectors by direct comparison with thresholds."""
        # a little painful, due to thresholds (and possible negative eigenvectors)
        eps = 1e-8
        for eig in self.di0: self.assertTrue(any(abs(self.di - eig) < eps))
        for vec in self.ei0: self.assertTrue(any(abs(np.dot(x, vec)) > (1 - eps) for x in self.ei_vect))

    def testInverse(self):
        """Check the evaluation of the inverse."""
        for a in xrange(3):
            for b in xrange(3):
                self.assertAlmostEqual(self.GF2_0[a, b], self.GF2[a, b])

    def testCalcUnorm(self):
        """Test the normalized u vector and magnitude; ui = (x.ei)/sqrt(di), including the handling of x=0."""
        # Graceful handling of 0?
        x = np.zeros(3)
        ui, umagn = GFcalc.unorm(self.di, self.ei_vect, x)
        self.assertEqual(umagn, 0)
        self.assertTrue(all(ui == 0))

        # "arbitrary" vector
        x = np.array([0.5, 0.25, -1])
        ui, umagn = GFcalc.unorm(self.di, self.ei_vect, x)
        self.assertAlmostEqual(np.dot(ui, ui), 1)
        self.assertAlmostEqual(umagn, np.sqrt(GFcalc.eval2(x, self.GF2)))
        for a in xrange(3):
            self.assertAlmostEqual(ui[a] * umagn,
                                   np.dot(x, self.ei_vect[a, :]) / np.sqrt(self.di[a]))

    def testCalcPnorm(self):
        """Test the normalized p vector and magnitude; pi = (q.ei)*sqrt(di), including the handling of q=0."""
        # Graceful handling of 0?
        q = np.zeros(3)
        pi, pmagn = GFcalc.pnorm(self.di, self.ei_vect, q)
        self.assertEqual(pmagn, 0)
        self.assertTrue(all(pi == 0))

        # "arbitrary" vector
        q = np.array([0.5, 0.25, -1])
        pi, pmagn = GFcalc.pnorm(self.di, self.ei_vect, q)
        self.assertAlmostEqual(np.dot(pi, pi), 1)
        self.assertAlmostEqual(pmagn, np.sqrt(GFcalc.eval2(q, self.D2)))
        for a in xrange(3):
            self.assertAlmostEqual(pi[a] * pmagn,
                                   np.dot(q, self.ei_vect[a, :]) * np.sqrt(self.di[a]))

    def testPoleFT(self):
        """Test the evaluation of the fourier transform of the second-order pole, including at 0."""
        # Graceful handling of 0?
        pm = 0.5  # arbitrary at this point...
        x = np.zeros(3)
        ui, umagn = GFcalc.unorm(self.di, self.ei_vect, x)
        g = GFcalc.poleFT(self.di, umagn, pm)
        # pm/( sqrt(d1 d2 d3) 4 pi^(3/2) )
        self.assertAlmostEqual(pm * 0.25 / np.sqrt(np.product(self.di * np.pi)), g)

        x = np.array((0.25, 0.5, 1))
        ui, umagn = GFcalc.unorm(self.di, self.ei_vect, x)

        erfupm = 0.125  # just to use the "cached" version
        self.assertNotEqual(GFcalc.poleFT(self.di, umagn, pm),
                            GFcalc.poleFT(self.di, umagn, pm, erfupm))

        g = GFcalc.poleFT(self.di, umagn, pm, erfupm)
        self.assertAlmostEqual(erfupm * 0.25 / (umagn * np.pi * np.sqrt(np.product(self.di))), g)


class GreenFuncFourierTransformDiscTests(unittest.TestCase):
    """Tests for the fourier transform of the discontinuity correction (4th derivative)."""

    def setUp(self):
        pass

    def testPowerExpansion(self):
        """Check that there are (a) 15 entries, (b) all non-negative, (c) summing to 4, (d) uniquely in our power expansion."""
        self.assertEqual(np.shape(GFcalc.PowerExpansion), (15, 3))
        self.assertTrue(np.all(GFcalc.PowerExpansion >= 0))
        for i in xrange(15):
            self.assertEqual(GFcalc.PowerExpansion[i].sum(), 4)
            for j in xrange(i):
                self.assertFalse(all(GFcalc.PowerExpansion[i] == GFcalc.PowerExpansion[j]))

    def testExpToIndex(self):
        """Checks that ExpToIndex is correctly constructed."""
        for n1 in xrange(5):
            for n2 in xrange(5):
                for n3 in xrange(5):
                    if (n1 + n2 + n3 != 4):
                        self.assertEqual(GFcalc.ExpToIndex[n1, n2, n3], 15,
                                         msg="index {}{}{}".format(n1, n2, n3))
                    else:
                        ind = GFcalc.ExpToIndex[n1, n2, n3]
                        self.assertNotEqual(ind, 15,
                                            msg="index {}".format(ind))
                        self.assertTrue(all(GFcalc.PowerExpansion[ind] == (n1, n2, n3)),
                                        msg="index {}{}{}".format(n1, n2, n3))

    def testPowerEval(self):
        """Test the powereval(u) function that returns the 15 vector of powers of u."""
        u = np.array((0.5, -1. / 3., 7))
        u15 = GFcalc.powereval(u)
        for n1 in xrange(3):
            for n2 in xrange(3):
                for n3 in xrange(3):
                    if (n1 + n2 + n3) == 4:
                        self.assertAlmostEqual((u[0] ** n1) * (u[1] ** n2) * (u[2] ** n3),
                                               u15[GFcalc.ExpToIndex[n1, n2, n3]],
                                               msg="index {}{}{}".format(n1, n2, n3))

    def testConvD4toNNN(self):
        """Tests conversion of the 4th-rank 4th derivative into power expansion."""
        D4 = np.zeros((3, 3, 3, 3))
        D4[0, 0, 0, 0] = 1
        D15 = GFcalc.D4toNNN(D4)
        self.assertEqual(np.shape(D15), (15,))
        self.assertEqual(D15[GFcalc.ExpToIndex[4, 0, 0]], 1)
        for ind in xrange(15):
            if ind != GFcalc.ExpToIndex[4, 0, 0]:
                self.assertEqual(D15[ind], 0)

        D4 = np.zeros((3, 3, 3, 3))
        D4[1, 1, 1, 1] = 1
        D15 = GFcalc.D4toNNN(D4)
        self.assertEqual(np.shape(D15), (15,))
        self.assertEqual(D15[GFcalc.ExpToIndex[0, 4, 0]], 1)
        for ind in xrange(15):
            if ind != GFcalc.ExpToIndex[0, 4, 0]:
                self.assertEqual(D15[ind], 0)

        D4 = np.zeros((3, 3, 3, 3))
        D4[0, 0, 0, 1] = 1
        D4[0, 0, 1, 0] = 1
        D4[0, 1, 0, 0] = 1
        D4[1, 0, 0, 0] = 1
        D15 = GFcalc.D4toNNN(D4)
        self.assertEqual(np.shape(D15), (15,))
        self.assertEqual(D15[GFcalc.ExpToIndex[3, 1, 0]], 4)
        for ind in xrange(15):
            if ind != GFcalc.ExpToIndex[3, 1, 0]:
                self.assertEqual(D15[ind], 0)

        D4 = np.zeros((3, 3, 3, 3))
        for a in xrange(3):
            for b in xrange(3):
                for c in xrange(3):
                    for d in xrange(3):
                        D4[a, b, c, d] = 2 + a + 3 * b + 9 * c + 27 * d
        D15 = GFcalc.D4toNNN(D4)
        x = np.array((0.23454, -1.24, 2.03))
        self.assertAlmostEqual(np.dot(D15, GFcalc.powereval(x)),
                               GFcalc.eval4(x, D4))

    def testRotateD4(self):
        """Tests the rotation of D4 with the eigenvalues/vectors of D.
        Checks that the eigenvectors input give what you expect, and also checks
        equality for some arbitrary vector.
        """
        di = np.array([0.5, 1., 2.])
        ei = np.array([[np.sqrt(0.5), np.sqrt(0.5), 0],
                       [np.sqrt(1. / 6.), -np.sqrt(1. / 6.), np.sqrt(2. / 3.)],
                       [np.sqrt(1. / 3.), -np.sqrt(1. / 3.), -np.sqrt(1. / 3.)]])

        D4 = np.zeros((3, 3, 3, 3))
        D4[0, 0, 0, 0] = 1
        Drot4 = GFcalc.RotateD4(D4, di, ei)
        self.assertEqual(np.shape(Drot4), (3, 3, 3, 3))
        for a in xrange(3):
            self.assertAlmostEqual(Drot4[a, a, a, a],
                                   GFcalc.eval4(ei[a] / np.sqrt(di[a]), D4))
        q = np.array([1, -0.5, -0.25])
        pi, pnorm = GFcalc.pnorm(di, ei, q)
        self.assertAlmostEqual(GFcalc.eval4(pi, Drot4) * (pnorm ** 4),
                               GFcalc.eval4(q, D4))

        D4 = np.zeros((3, 3, 3, 3))
        D4[0, 0, 0, 1] = 0.25
        D4[0, 0, 1, 0] = 0.25
        D4[0, 1, 0, 0] = 0.25
        D4[1, 0, 0, 0] = 0.25
        D4[2, 2, 2, 2] = -4
        Drot4 = GFcalc.RotateD4(D4, di, ei)
        self.assertEqual(np.shape(Drot4), (3, 3, 3, 3))
        for a in xrange(3):
            self.assertAlmostEqual(Drot4[a, a, a, a],
                                   GFcalc.eval4(ei[a] / np.sqrt(di[a]), D4),
                                   msg="index {}".format(a))
        self.assertAlmostEqual(GFcalc.eval4(pi, Drot4) * (pnorm ** 4),
                               GFcalc.eval4(q, D4))

    def test15x15FourierSymmetries(self):
        """Tests that the 3x15x15 matrix has the symmetries we'd expect corresponding to powers."""
        self.assertEqual(np.shape(GFcalc.PowerFT), (3, 15, 15))
        # The sum of the 3 15x15 matrices must be the identity matrix
        for i in xrange(15):
            for j in xrange(15):
                if i == j:
                    self.assertAlmostEqual(sum(GFcalc.PowerFT[:, i, j]), 1,
                                           msg="Checking {},{}".format(i, j))
                else:
                    self.assertAlmostEqual(sum(GFcalc.PowerFT[:, i, j]), 0,
                                           msg="Checking {},{}".format(i, j))

        for i in xrange(15):
            if tuple(GFcalc.PowerExpansion[i]).count(1) > 0:
                # No l=0 entries for any indices containing 1
                self.assertTrue(np.all(GFcalc.PowerFT[0, :, i] == 0),
                                msg="Checking {}".format(i))
                self.assertTrue(np.all(GFcalc.PowerFT[0, i, :] == 0),
                                msg="Checking {}".format(i))
                for j in xrange(15):
                    if tuple(GFcalc.PowerExpansion[j]).count(1) == 0:
                        self.assertTrue(np.all(GFcalc.PowerFT[:, i, j] == 0),
                                        msg="Checking {},{}".format(i, j))
                        self.assertTrue(np.all(GFcalc.PowerFT[:, j, i] == 0),
                                        msg="Checking {},{}".format(i, j))
            else:
                for j in xrange(15):
                    # No mixing between those containing 1 and those not,
                    # but full for those without any 1's.
                    if tuple(GFcalc.PowerExpansion[j]).count(1) > 0:
                        self.assertTrue(np.all(GFcalc.PowerFT[:, i, j] == 0),
                                        msg="Checking {},{}".format(i, j))
                        self.assertTrue(np.all(GFcalc.PowerFT[:, j, i] == 0),
                                        msg="Checking {},{}".format(i, j))
                    else:
                        self.assertFalse(np.any(GFcalc.PowerFT[:, i, j] == 0),
                                         msg="Checking {},{}".format(i, j))
                        self.assertFalse(np.any(GFcalc.PowerFT[:, j, i] == 0),
                                         msg="Checking {},{}".format(i, j))
        # check against mixing between the <013>/<031>/<211>
        for v1 in ( (0, 1, 3), (0, 3, 1), (2, 1, 1) ):
            for s1 in xrange(3):
                in1 = GFcalc.ExpToIndex[GFcalc.rotatetuple(v1, s1)]
                for v2 in ( (0, 1, 3), (0, 3, 1), (2, 1, 1) ):
                    for s2 in xrange(s1):
                        in2 = GFcalc.ExpToIndex[GFcalc.rotatetuple(v2, s2)]
                        for l in xrange(3):
                            self.assertEqual(0, GFcalc.PowerFT[l, in1, in2],
                                             msg="Checking {} {},{} {}".format(v1, s1, v2, s2))

    def test15x15FourierIsotropic(self):
        """Tests that the 3x15x15 matrix has the values we'd expect, above and beyond the symmetries.
        First case is isotropic; should come out isotropic (only l=0 term).
        """
        D15 = np.zeros(15)
        D15[GFcalc.ExpToIndex[4, 0, 0]] = 1
        D15[GFcalc.ExpToIndex[0, 4, 0]] = 1
        D15[GFcalc.ExpToIndex[0, 0, 4]] = 1
        D15[GFcalc.ExpToIndex[0, 2, 2]] = 2
        D15[GFcalc.ExpToIndex[2, 0, 2]] = 2
        D15[GFcalc.ExpToIndex[2, 2, 0]] = 2

        D15_0 = np.dot(GFcalc.PowerFT[0], D15)
        D15_2 = np.dot(GFcalc.PowerFT[1], D15)
        D15_4 = np.dot(GFcalc.PowerFT[2], D15)
        for i in xrange(15):
            self.assertAlmostEqual(D15_0[i], D15[i])
            self.assertAlmostEqual(D15_2[i], 0)
            self.assertAlmostEqual(D15_4[i], 0)

    def test15x15FourierValues(self):
        """Tests that the 3x15x15 matrix has the values we'd expect, above and beyond the symmetries."""
        D15 = np.zeros(15)
        D15[GFcalc.ExpToIndex[0, 0, 4]] = 1
        D15[GFcalc.ExpToIndex[0, 4, 0]] = 2
        D15[GFcalc.ExpToIndex[4, 0, 0]] = 3
        D15[GFcalc.ExpToIndex[2, 2, 0]] = 4
        D15[GFcalc.ExpToIndex[2, 0, 2]] = 5
        D15[GFcalc.ExpToIndex[0, 2, 2]] = 6

        D15[GFcalc.ExpToIndex[0, 1, 3]] = 7
        D15[GFcalc.ExpToIndex[0, 3, 1]] = 8
        D15[GFcalc.ExpToIndex[2, 1, 1]] = 9

        D15[GFcalc.ExpToIndex[1, 0, 3]] = 10
        D15[GFcalc.ExpToIndex[3, 0, 1]] = 11
        D15[GFcalc.ExpToIndex[1, 2, 1]] = 12

        D15[GFcalc.ExpToIndex[1, 3, 0]] = 13
        D15[GFcalc.ExpToIndex[3, 1, 0]] = 14
        D15[GFcalc.ExpToIndex[1, 1, 2]] = 15

        # result, from Mathematica (l=0)
        #{ 11/5, 11/5, 11/5,
        #  22/5, 22/5, 22/5,
        #  0,0,0, 0,0,0, 0,0,0 }
        D15_test = np.zeros(15)
        D15_test[GFcalc.ExpToIndex[0, 0, 4]] = 11. / 5.
        D15_test[GFcalc.ExpToIndex[0, 4, 0]] = 11. / 5.
        D15_test[GFcalc.ExpToIndex[4, 0, 0]] = 11. / 5.
        D15_test[GFcalc.ExpToIndex[2, 2, 0]] = 22. / 5.
        D15_test[GFcalc.ExpToIndex[2, 0, 2]] = 22. / 5.
        D15_test[GFcalc.ExpToIndex[0, 2, 2]] = 22. / 5.

        D15_0 = np.dot(GFcalc.PowerFT[0], D15)
        for i in xrange(15):
            self.assertAlmostEqual(D15_0[i], D15_test[i], msg="index {}".format(i))

        # result, from Mathematica (l=2)
        #{ -5/7, 0, 5/7,
        #   5/7, 0, -5/7,
        #   54/7, 54/7, 54/7,
        #   75/7, 75/7, 75/7,
        #   96/7, 96/7, 96/7}
        D15_test = np.zeros(15)
        D15_test[GFcalc.ExpToIndex[0, 0, 4]] = -5. / 7.
        D15_test[GFcalc.ExpToIndex[0, 4, 0]] = 0.
        D15_test[GFcalc.ExpToIndex[4, 0, 0]] = 5. / 7.
        D15_test[GFcalc.ExpToIndex[2, 2, 0]] = 5. / 7.
        D15_test[GFcalc.ExpToIndex[2, 0, 2]] = 0
        D15_test[GFcalc.ExpToIndex[0, 2, 2]] = -5. / 7.

        D15_test[GFcalc.ExpToIndex[0, 1, 3]] = 54. / 7.
        D15_test[GFcalc.ExpToIndex[0, 3, 1]] = 54. / 7.
        D15_test[GFcalc.ExpToIndex[2, 1, 1]] = 54. / 7.

        D15_test[GFcalc.ExpToIndex[1, 0, 3]] = 75. / 7.
        D15_test[GFcalc.ExpToIndex[3, 0, 1]] = 75. / 7.
        D15_test[GFcalc.ExpToIndex[1, 2, 1]] = 75. / 7.

        D15_test[GFcalc.ExpToIndex[1, 3, 0]] = 96. / 7.
        D15_test[GFcalc.ExpToIndex[3, 1, 0]] = 96. / 7.
        D15_test[GFcalc.ExpToIndex[1, 1, 2]] = 96. / 7.

        D15_2 = np.dot(GFcalc.PowerFT[1], D15)
        for i in xrange(15):
            self.assertAlmostEqual(D15_2[i], D15_test[i], msg="index {}".format(i))

        # result, from Mathematica (l=4)
        # {-17/35, -1/5, 3/35,
        #  -39/35, 3/5, 81/35,
        #  -5/7, 2/7, 9/7,
        #  -5/7, 2/7, 9/7,
        #  -5/7, 2/7, 9/7}
        D15_test = np.zeros(15)
        D15_test[GFcalc.ExpToIndex[0, 0, 4]] = -17. / 35.
        D15_test[GFcalc.ExpToIndex[0, 4, 0]] = -1. / 5.
        D15_test[GFcalc.ExpToIndex[4, 0, 0]] = 3 / 35.
        D15_test[GFcalc.ExpToIndex[2, 2, 0]] = -39. / 35.
        D15_test[GFcalc.ExpToIndex[2, 0, 2]] = 3. / 5.
        D15_test[GFcalc.ExpToIndex[0, 2, 2]] = 81. / 35.

        D15_test[GFcalc.ExpToIndex[0, 1, 3]] = -5. / 7.
        D15_test[GFcalc.ExpToIndex[0, 3, 1]] = 2. / 7.
        D15_test[GFcalc.ExpToIndex[2, 1, 1]] = 9. / 7.

        D15_test[GFcalc.ExpToIndex[1, 0, 3]] = -5. / 7.
        D15_test[GFcalc.ExpToIndex[3, 0, 1]] = 2. / 7.
        D15_test[GFcalc.ExpToIndex[1, 2, 1]] = 9. / 7.

        D15_test[GFcalc.ExpToIndex[1, 3, 0]] = -5. / 7.
        D15_test[GFcalc.ExpToIndex[3, 1, 0]] = 2. / 7.
        D15_test[GFcalc.ExpToIndex[1, 1, 2]] = 9. / 7.

        D15_4 = np.dot(GFcalc.PowerFT[2], D15)
        for i in xrange(15):
            self.assertAlmostEqual(D15_4[i], D15_test[i], msg="index {}".format(i))

    def testFourierIntergrals(self):
        """Tests for the three Fourier integrals, f0 f2 f4, that we'll use to construct the full FT."""
        di = np.array((1, 1, 1))
        ei = np.eye(3)
        pm = 0.5

        x = np.zeros(3)
        ui, umagn = GFcalc.unorm(di, ei, x)
        fi = GFcalc.discFT(di, umagn, pm)
        self.assertEqual(np.shape(fi), (3,))
        self.assertListEqual(list(fi), [0, 0, 0])

        # Results using HyperGeometric functions:
        # 1/(pi^3/2 * u^3 * (d1 d2 d3)^1/2) (z/2)^(3+l) 1F1(3/2 + l/2, 3/2+l, -(z/2)^2)
        umagn = 1.
        fi = GFcalc.discFT(di, umagn, pm)
        zhalf = 0.5 * umagn * pm
        zhalf2 = zhalf * zhalf
        fi_0 = (1. / (umagn * umagn * umagn * np.sqrt(np.product(np.pi * di))) *
                np.array((zhalf ** (3 + 0) * special.hyp1f1(0.5 * (3 + 0), 0.5 * (3 + 2 * 0), -zhalf2),
                          -zhalf ** (3 + 2) * special.hyp1f1(0.5 * (3 + 2), 0.5 * (3 + 2 * 2), -zhalf2),
                          zhalf ** (3 + 4) * special.hyp1f1(0.5 * (3 + 4), 0.5 * (3 + 2 * 4), -zhalf2)
                )))
        for l in xrange(3):
            self.assertAlmostEqual(fi[l], fi_0[l])

        di = np.array([0.91231, 1.123, 2.1231])
        ei = np.array([[np.sqrt(0.5), np.sqrt(0.5), 0],
                       [np.sqrt(1. / 6.), -np.sqrt(1. / 6.), np.sqrt(2. / 3.)],
                       [np.sqrt(1. / 3.), -np.sqrt(1. / 3.), -np.sqrt(1. / 3.)]])
        x = np.array([0.12, -0.51, 0.9123])
        ui, umagn = GFcalc.unorm(di, ei, x)
        fi = GFcalc.discFT(di, umagn, pm)
        zhalf = 0.5 * umagn * pm
        zhalf2 = zhalf * zhalf
        fi_0 = (1. / (umagn * umagn * umagn * np.sqrt(np.product(np.pi * di))) *
                np.array((zhalf ** (3 + 0) * special.hyp1f1(0.5 * (3 + 0), 0.5 * (3 + 2 * 0), -zhalf2),
                          -zhalf ** (3 + 2) * special.hyp1f1(0.5 * (3 + 2), 0.5 * (3 + 2 * 2), -zhalf2),
                          zhalf ** (3 + 4) * special.hyp1f1(0.5 * (3 + 4), 0.5 * (3 + 2 * 4), -zhalf2)
                )))
        for l in xrange(3):
            self.assertAlmostEqual(fi[l], fi_0[l])



class GFcalcFunctionTests(unittest.TestCase):
    def setUp(self):
        self.NNvect = FCClatt.NNvect()
        self.rates = np.array((1,) * np.shape(self.NNvect)[0])
        self.DFT = GFcalc.DFTfunc(self.NNvect, self.rates)  # Fourier transform
        self.D2 = GFcalc.D2(self.NNvect, self.rates)  # - 2nd deriv. of FT (>0)
        self.di, self.ei = GFcalc.calcDE(self.D2)
        self.D4 = GFcalc.D4(self.NNvect, self.rates)  # + 4th deriv. of FT (>0)
        self.D15 = GFcalc.D4toNNN(
            GFcalc.RotateD4(self.D4, self.di, self.ei))

    def testSemiContinuum(self):
        """Does our semicontinuum function go as q^2 for small q?"""
        klist = [np.array((0.1, 0, 0)),
                 np.array((0.05, 0, 0))]
        pilist = [GFcalc.pnorm(self.di, self.ei, k)[0] for k in klist]
        pmlist = [GFcalc.pnorm(self.di, self.ei, k)[1] for k in klist]
        # pmax = pmlist[0]*100
        pmax = 1e10
        Glist = np.array([1./self.DFT(k) for k in klist])
        # fc = np.array([np.exp(-(pmagn/pmax)**2) for pmagn in pmlist])
        fc = np.array([1, 1])
        G2 = fc*np.array([1./pmagn**2 for pmagn in pmlist])
        Gdc = fc*np.array([np.dot(self.D15, GFcalc.powereval(pi)) for pi in pilist])
        Gsc = Glist + G2 + Gdc
        self.assertAlmostEqual((Gsc[1] + 1./pmax**2)/(Gsc[0] + 1./pmax**2),
                               0.25, delta=1e-4)


class GFCalcObjectTestsSC(unittest.TestCase):
    """Set of tests for our GF-calculation class for simple cubic"""

    def setUp(self):
        # cell vectors for SC:
        self.lattice = np.array([[1, 0, 0],
                                 [0, 1, 0],
                                 [0, 0, 1]])
        self.NNvect = np.array([[1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1], [0, 0, -1]])
        self.rates = np.array((1./6.,) * 6)
        self.GF = GFcalc.GFcalc(self.lattice, self.NNvect, self.rates)

    def testGFkR(self):
        """Can we calculate k.R for points?"""
        R = np.array((0, 0, 0))
        coskR = self.GF.calccoskR(R)
        for x in coskR:
            self.assertAlmostEqual(x, 1)
        self.assertAlmostEqual(sum(coskR*self.GF.wts), 1)
        R = self.NNvect[0]
        coskR = self.GF.calccoskR(R)
        self.assertAlmostEqual(sum(coskR*self.GF.wts), 0)

    def testGFclassexists(self):
        """Does it exist?"""
        self.assertIsInstance(self.GF, GFcalc.GFcalc)

    def testGFclasscalc(self):
        """Can we calculate a value for (0, 0, 0) and have it be non-zero?"""
        R = np.array((0, 0, 0))
        g = self.GF.GF(R)
        self.assertNotEqual(g, 0)

    def testGFsymmetry(self):
        """Do we have the basic symmetries we expect?"""
        for R in self.NNvect:
            g0 = self.GF.GF(R)
            for gR in [np.dot(g, R) for g in self.GF.kptmesh.groupops]:
                g1 = self.GF.GF(gR)
                self.assertAlmostEqual(g0, g1,
                                       msg="Symmetry broken between {} and {}; got {} and {}".format(R, gR, g0, g1))

    def testGFdisc0(self):
        """Do we have the correct value for the discontinuity correction at R=0?"""
        # Should be V/((2pi)^3 * sqrt(d1 d2 d3)) * int( exp(-p^2/pm^2) * D4.phat )
        # where we integrate over all space
        Gdc0 = self.GF.volume*self.GF.pmax**3/(8*np.pi**1.5*np.sqrt(np.product(self.GF.di)))*\
               self.GF.D15FT[0, GFcalc.ExpToIndex[4, 0, 0]]
        self.assertAlmostEqual(Gdc0, self.GF.Gdisc0)

    def testGFpseudoinverse(self):
        """Is G the pseudoinverse of D? Check value at origin, and first NN"""
        R0 = np.array((0, 0, 0))
        Rlist = [R0 + R for R in self.NNvect]
        g0 = self.GF.GF(R0)
        glist = [self.GF.GF(R) for R in Rlist]
        self.assertAlmostEqual(sum(self.rates*(glist-g0)), 1, delta=1e-5)

        R1 = self.NNvect[0]
        Rlist = [R1 + R for R in self.NNvect]
        g1 = self.GF.GF(R1)
        glist = [self.GF.GF(R) for R in Rlist]
        self.assertAlmostEqual(sum(self.rates*(glist-g1)), 0, delta=1e-5)

        R2 = self.NNvect[0] + self.NNvect[2]
        Rlist = [R2 + R for R in self.NNvect]
        g2 = self.GF.GF(R2)
        glist = [self.GF.GF(R) for R in Rlist]
        self.assertAlmostEqual(sum(self.rates*(glist-g2)), 0, delta=1e-5)


class GFCalcObjectTestsFCC(GFCalcObjectTestsSC):
    """Set of tests for our GF-calculation class for FCC"""

    def setUp(self):
        # cell vectors for FCC:
        self.lattice = FCClatt.lattice()
        self.NNvect = FCClatt.NNvect()
        self.rates = np.array((1./12.,) * 12)
        self.GF = GFcalc.GFcalc(self.lattice, self.NNvect, self.rates)

    def testGFanaylticvalue(self):
        """Compare our G(R=0) value against Koiwa and Ishioka, 1983b value"""
        # From Koiwa, M, and Ishioka, S. (1983a) J. Stat. Phys. 30, 477; (1983b) Phil. Mag. A47, 927.
        # The 200 value disagrees by more than the numerical integration error we have;
        # 32^3 vs 24^3 gives a change of 1.57e-7; 32^3 vs. 16^3 gives a a change of 1.5e-6
        # which are consistent with integration errors for this algorithm.
        # This appears to be converging towards -0.2299125
        # self.GF.genmesh([32, 32, 32])
        self.assertAlmostEqual(self.GF.GF(np.array([0, 0, 0])), -1.344661, delta=1e-5)
        self.assertAlmostEqual(self.GF.GF(np.array([1, 1, 0])), -0.344661, delta=1e-5)
        self.assertAlmostEqual(self.GF.GF(np.array([2, 0, 0])), -0.229936, delta=3e-5)


class GFCalcObjectTestsDistortedSC(GFCalcObjectTestsSC):
    """Set of tests for our GF-calculation class for distorted simple cubic"""

    def setUp(self):
        # cell vectors for SC:
        self.lattice = np.array([[1, 0, 0],
                                 [0, 1, 0],
                                 [0, 0, np.sqrt(0.5)]])
        self.NNvect = np.array([[1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, np.sqrt(0.5)], [0, 0, -np.sqrt(0.5)]])
        self.rates = np.array((1./6.,) * 6)
        self.GF = GFcalc.GFcalc(self.lattice, self.NNvect, self.rates)


# TODO: understand why strain of sqrt(1/2) seems to cause issue with point group determining function...?
# TODO: perhaps change the symmetry operation finding algorithm to take rates into account?
class GFCalcObjectTestsDistortedFCC(GFCalcObjectTestsSC):
    """Set of tests for our GF-calculation class for distorted face-centered cubic"""

    def setUp(self):
        # cell vectors for distorted FCC:
        eps = np.array([
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 0.75]])
        self.lattice = np.dot(eps, FCClatt.lattice())
        self.NNvect = np.array([np.dot(eps, v) for v in FCClatt.NNvect()])
        self.rates = np.array((1./12.,) * 12)
        self.GF = GFcalc.GFcalc(self.lattice, self.NNvect, self.rates)


# DocTests... we use this for the small "utility" functions, rather than writing
# explicit tests; doctests are compatible with unittests, so we're good here.
import doctest

def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(GFcalc))
    return tests
