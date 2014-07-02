"""
Unit tests for star, double-star and vector-star generation and indexing
"""

__author__ = 'Dallas R. Trinkle'

#

import unittest
import FCClatt
import KPTmesh
import numpy as np
import stars


# Setup for orthorhombic, simple cubic, and FCC cells:
def setuportho():
    lattice = np.array([[3, 0, 0],
                        [0, 2, 0],
                        [0, 0, 1]], dtype=float)
    NNvect = np.array([[3, 0, 0], [-3, 0, 0],
                       [0, 2, 0], [0, -2, 0],
                       [0, 0, 1], [0, 0, -1]], dtype=float)
    groupops = KPTmesh.KPTmesh(lattice).groupops
    star = stars.StarSet(NNvect, groupops)
    return lattice, NNvect, groupops, star

def orthorates():
    return np.array([3, 3, 2, 2, 1, 1], dtype=float)

def setupcubic():
    lattice = np.array([[1, 0, 0],
                        [0, 1, 0],
                        [0, 0, 1]], dtype=float)
    NNvect = np.array([[1, 0, 0], [-1, 0, 0],
                       [0, 1, 0], [0, -1, 0],
                       [0, 0, 1], [0, 0, -1]], dtype=float)
    groupops = KPTmesh.KPTmesh(lattice).groupops
    star = stars.StarSet(NNvect, groupops)
    return lattice, NNvect, groupops, star

def cubicrates():
    return np.array([1./6.,]*6, dtype=float)

def setupFCC():
    lattice = FCClatt.lattice()
    NNvect = FCClatt.NNvect()
    groupops = KPTmesh.KPTmesh(lattice).groupops
    star = stars.StarSet(NNvect, groupops)
    return lattice, NNvect, groupops, star

def FCCrates():
    return np.array([1./12.,]*12, dtype=float)


class StarTests(unittest.TestCase):
    """Set of tests that our star code is behaving correctly for a general materials"""

    def setUp(self):
        self.lattice, self.NNvect, self.groupops, self.star = setuportho()

    def isclosed(self, s, groupops, threshold=1e-8):
        """
        Evaluate if star s is closed against group operations.

        Parameters
        ----------
        s : list of vectors
            star

        groupops : list (or array) of 3x3 matrices
            all group operations

        threshold : float, optional
            threshold for equality in comparison

        Returns
        -------
        True if every pair of vectors in star are related by a group operation;
        False otherwise
        """
        for v1 in s:
            for v2 in s:
                if not any([all(abs(v1 - np.dot(g, v2)) < threshold) for g in groupops]):
                    return False
        return True


    def testStarConsistent(self):
        """Check that the counts (Npts, Nstars) make sense, with Nshells = 1..4"""
        for n in xrange(1,5):
            self.star.generate(n)
            self.assertEqual(self.star.Npts, sum([len(s) for s in self.star.stars]))
            for s in self.star.stars:
                self.assertTrue(self.isclosed(s, self.groupops))

    def testStarindices(self):
        """Check that our indexing is correct."""
        self.star.generate(4)
        for ns, s in enumerate(self.star.stars):
            for v in s:
                self.assertEqual(ns, self.star.starindex(v))
        self.assertEqual(-1, self.star.starindex(np.zeros(3)))
        for i, v in enumerate(self.star.pts):
            self.assertEqual(i, self.star.pointindex(v))
        self.assertEqual(-1, self.star.pointindex(np.zeros(3)))

    def assertEqualStars(self, s1, s2):
        """Asserts that two stars are equal."""
        self.assertEqual(s1.Npts, s2.Npts,
                         msg='Number of points in two star sets are not equal: {} != {}'.format(
                             s1.Npts, s2.Npts
                         ))
        self.assertEqual(s1.Nshells, s2.Nshells,
                         msg='Number of shells in two star sets are not equal: {} != {}'.format(
                             s1.Nshells, s2.Nshells
                         ))
        self.assertEqual(s1.Nstars, s2.Nstars,
                         msg='Number of stars in two star sets are not equal: {} != {}'.format(
                             s1.Nstars, s2.Nstars
                         ))
        for s in s1.stars:
            ind = s2.starindex(s[0])
            self.assertNotEqual(ind, -1,
                                msg='Could not find {} from s1 in s2'.format(
                                    s[0]
                                ))
            for R in s:
                self.assertEqual(ind, s2.starindex(R),
                                 msg='Point {} and {} from star in s1 belong to different stars in s2'.format(
                                     s[0], R
                                 ))
        for s in s2.stars:
            ind = s1.starindex(s[0])
            self.assertNotEqual(ind, -1,
                                msg='Could not find {} from s2 in s1'.format(
                                    s[0]
                                ))
            for R in s:
                self.assertEqual(ind, s1.starindex(R),
                                 msg='Point {} and {} from star in s2 belong to different stars in s1'.format(
                                     s[0], R
                                 ))

    def testStarCombine(self):
        """Check that we can combine two stars and get what we expect."""
        s1 = stars.StarSet(self.NNvect, self.groupops)
        s2 = stars.StarSet(self.NNvect, self.groupops)
        s3 = stars.StarSet(self.NNvect, self.groupops)
        s4 = stars.StarSet(self.NNvect, self.groupops)
        s1.generate(1)
        s2.generate(1)
        s3.combine(s1, s2)
        s4.generate(2)
        # s3 = s1 + s2, should equal s4
        self.assertEqualStars(s1, s2)
        self.assertEqualStars(s3, s4)


class CubicStarTests(StarTests):
    """Set of tests that our star code is behaving correctly for cubic materials"""

    def setUp(self):
        self.lattice, self.NNvect, self.groupops, self.star = setupcubic()

    def testStarConsistent(self):
        """Check that the counts (Npts, Nstars) make sense for cubic, with Nshells = 1..4"""
        for n in xrange(1,5):
            self.star.generate(n)
            self.assertEqual(self.star.Npts, sum([len(s) for s in self.star.stars]))
            for s in self.star.stars:
                x = s[0]
                num = (2 ** (3 - list(x).count(0)))
                if x[0] != x[1] and x[1] != x[2]:
                    num *= 6
                elif x[0] != x[1] or x[1] != x[2]:
                    num *= 3
                self.assertEqual(num, len(s))
                self.assertTrue(self.isclosed(s, self.groupops))

    def testStarmembers(self):
        """Are the members correct?"""
        self.star.generate(1)
        s = self.star.stars[0]
        for v in self.NNvect:
            self.assertTrue(any(all(abs(v-v1)<1e-8) for v1 in s))


class FCCStarTests(CubicStarTests):
    """Set of tests that our star code is behaving correctly for FCC"""

    def setUp(self):
        self.lattice, self.NNvect, self.groupops, self.star = setupFCC()

    def testStarCount(self):
        """Check that the counts (Npts, Nstars) make sense for FCC, with Nshells = 1, 2, 3"""
        # 110
        self.star.generate(1)
        self.assertEqual(self.star.Nstars, 1)
        self.assertEqual(self.star.Npts, np.shape(self.NNvect)[0])

        # 110, 200, 211, 220
        self.star.generate(2)
        self.assertEqual(self.star.Nstars, 4)

        # 110, 200, 211, 220, 310, 321, 330, 222
        self.star.generate(3)
        self.assertEqual(self.star.Nstars, 8)


class DoubleStarTests(unittest.TestCase):
    """Set of tests that our DoubleStar class is behaving correctly."""

    def setUp(self):
        self.lattice, self.NNvect, self.groupops, self.star = setupFCC()
        self.dstar = stars.DoubleStarSet()

    def testDoubleStarGeneration(self):
        """Can we generate a double-star?"""
        self.star.generate(1)
        self.dstar.generate(self.star)
        self.assertTrue(self.dstar.Ndstars > 0)
        self.assertTrue(self.dstar.Npairs > 0)

    def testDoubleStarCount(self):
        """Check that the counts (Npts, Nstars) make sense for FCC, with Nshells = 1, 2"""
        # each of the 12 <110> pairs to 101, 10-1, 011, 01-1 = 4, so should be 48 pairs
        # (which includes "double counting": i->j and j->i)
        # but *all* of those 48 are all equivalent to each other by symmetry: one double-star.
        self.star.generate(1)
        self.dstar.generate(self.star)
        self.assertEqual(self.dstar.Npairs, 48)
        self.assertEqual(self.dstar.Ndstars, 1)
        # Now have four stars (110, 200, 211, 220), so this means
        # 12 <110> pairs to 11 (no 000!); 12*11
        # 6 <200> pairs to 110, 101, 1-10, 10-1; 211, 21-1, 2-11, 2-1-1 = 8; 6*8
        # 24 <211> pairs to 110, 101; 200; 112, 121; 202, 220 = 7; 24*7
        # 12 <220> pairs to 110; 12-1, 121, 21-1, 211 = 5; 12*5
        # unique pairs: (110, 101); (110, 200); (110, 211); (110, 220); (200, 211); (211, 112); (211, 220)
        self.star.generate(2)
        self.dstar.generate(self.star)
        self.assertEqual(self.dstar.Npairs, 12*11 + 6*8 + 24*7 + 12*5)
        # for ds in self.dstar.dstars:
        #     print self.star.pts[ds[0][0]], self.star.pts[ds[0][1]]
        self.assertEqual(self.dstar.Ndstars, 4 + 1 + 2)

    def testPairIndices(self):
        """Check that our pair indexing works correctly for Nshell=1..3"""
        for nshells in xrange(1, 4):
            self.star.generate(nshells)
            self.dstar.generate(self.star)
            for pair in self.dstar.pairs:
                self.assertTrue(pair == self.dstar.pairs[self.dstar.pairindex(pair)])

    def testDoubleStarindices(self):
        """Check that our double-star indexing works correctly for Nshell=1..3"""
        for nshells in xrange(1, 4):
            self.star.generate(nshells)
            self.dstar.generate(self.star)
            for pair in self.dstar.pairs:
                self.assertTrue(any(pair == p for p in self.dstar.dstars[self.dstar.dstarindex(pair)]))

class VectorStarTests(unittest.TestCase):
    """Set of tests that our VectorStar class is behaving correctly"""
    def setUp(self):
        self.lattice, self.NNvect, self.groupops, self.star = setuportho()
        self.vecstar = stars.VectorStarSet(self.star)

    def testVectorStarGenerate(self):
        """Can we generate star-vectors that make sense?"""
        self.star.generate(1)
        self.vecstar.generate(self.star)
        self.assertTrue(self.vecstar.Nvstars>0)

    def VectorStarConsistent(self, nshells):
        """Do the star vectors obey the definition?"""
        self.star.generate(nshells)
        self.vecstar.generate(self.star)
        for s, vec in zip(self.vecstar.vecpos, self.vecstar.vecvec):
            for R, v in zip(s, vec):
                for g in self.groupops:
                    Rrot = np.dot(g, R)
                    vrot = np.dot(g, v)
                    for R1, v1 in zip(s, vec):
                        if (abs(R1 - Rrot) < 1e-8).all():
                            self.assertTrue((abs(v1 - vrot) < 1e-8).all())

    def VectorStarOrthonormal(self, nshells):
        """Are the star vectors orthonormal?"""
        self.star.generate(nshells)
        self.vecstar.generate(self.star)
        for s1, v1 in zip(self.vecstar.vecpos, self.vecstar.vecvec):
            for s2, v2 in zip(self.vecstar.vecpos, self.vecstar.vecvec):
                if (s1[0] == s2[0]).all():
                    dp = 0
                    for vv1, vv2 in zip(v1, v2):
                        dp += np.dot(vv1, vv2)
                    if (v1[0] == v2[0]).all():
                        self.assertAlmostEqual(1., dp,
                                               msg='Failed normality for {}/{} and {}/{}'.format(
                                                   s1[0], v1[0], s2[0], v2[0]
                                               ))
                    else:
                        self.assertAlmostEqual(0., dp,
                                               msg='Failed orthogonality for {}/{} and {}/{}'.format(
                                                   s1[0], v1[0], s2[0], v2[0]
                                               ))

    def testVectorStarConsistent(self):
        """Do the star vectors obey the definition?"""
        self.VectorStarConsistent(2)

    def testVectorStarOrthonormal(self):
        self.VectorStarOrthonormal(2)

    def testVectorStarCount(self):
        """Does our star vector count make any sense?"""
        self.star.generate(1)
        self.vecstar.generate(self.star)
        self.assertEqual(self.vecstar.Nvstars, 3)

    def testVectorStarOuterProduct(self):
        """Do we generate the correct outer products for our star-vectors?"""
        self.star.generate(1)
        self.vecstar.generate(self.star)
        for outer in self.vecstar.outer:
            self.assertAlmostEqual(np.trace(outer), 1)
            # should also be symmetric:
            for g in self.groupops:
                g_out_gT = np.dot(g, np.dot(outer, g.T))
                self.assertTrue((abs(outer - g_out_gT) < 1e-8).all())


class VectorStarFCCTests(VectorStarTests):
    """Set of tests that our VectorStar class is behaving correctly, for FCC"""
    def setUp(self):
        self.lattice, self.NNvect, self.groupops, self.star = setupFCC()
        self.vecstar = stars.VectorStarSet(self.star)

    def testVectorStarCount(self):
        """Does our star vector count make any sense?"""
        self.star.generate(2)
        self.vecstar.generate(self.star)
        # nn + nn = 4 stars, and that should make 5 star-vectors!
        self.assertEqual(self.vecstar.Nvstars, 5)

    def testVectorStarConsistent(self):
        """Do the star vectors obey the definition?"""
        self.VectorStarConsistent(2)

    def testVectorStarOuterProductMore(self):
        """Do we generate the correct outer products for our star-vectors?"""
        self.star.generate(2)
        self.vecstar.generate(self.star)
        # with cubic symmetry, these all have to equal 1/3 * identity
        testouter = 1./3.*np.eye(3)
        for outer in self.vecstar.outer:
            self.assertTrue((abs(outer - testouter) < 1e-8).all())

import GFcalc


class VectorStarGFlinearTests(unittest.TestCase):
    """Set of tests that make sure we can construct the GF matrix as a linear combination"""
    def setUp(self):
        self.lattice, self.NNvect, self.groupops, self.star = setuportho()
        self.star2 = stars.StarSet(self.NNvect, self.groupops)
        self.vecstar = stars.VectorStarSet(self.star)
        self.rates = orthorates()
        self.GF = GFcalc.GFcalc(self.lattice, self.NNvect, self.rates)

    def ConstructGF(self, nshells):
        self.star.generate(nshells)
        self.star2.generate(2*nshells)
        self.vecstar.generate(self.star)
        GFexpand = self.vecstar.GFexpansion(self.star2)
        self.assertEqual(np.shape(GFexpand),
                         (self.vecstar.Nvstars, self.vecstar.Nvstars, self.star2.Nstars + 1))
        gexpand = np.zeros(self.star2.Nstars + 1)
        gexpand[0] = self.GF.GF(np.zeros(3))
        for i in xrange(self.star2.Nstars):
            gexpand[i + 1] = self.GF.GF(self.star2.stars[i][0])
        for i in xrange(self.vecstar.Nvstars):
            for j in xrange(self.vecstar.Nvstars):
                # test the construction
                self.assertAlmostEqual(sum(GFexpand[i, j, :]), 0)
                g = 0
                for Ri, vi in zip(self.vecstar.vecpos[i], self.vecstar.vecvec[i]):
                    for Rj, vj in zip(self.vecstar.vecpos[j], self.vecstar.vecvec[j]):
                        g += np.dot(vi, vj)*self.GF.GF(Ri - Rj)
                self.assertAlmostEqual(g, np.dot(GFexpand[i, j, :], gexpand))
        # print(np.dot(GFexpand, gexpand))

    def testConstructGF(self):
        """Test the construction of the GF using double-nn shell"""
        self.ConstructGF(2)

class VectorStarGFFCClinearTests(VectorStarGFlinearTests):
    """Set of tests that make sure we can construct the GF matrix as a linear combination for FCC"""
    def setUp(self):
        self.lattice, self.NNvect, self.groupops, self.star = setupFCC()
        self.star2 = stars.StarSet(self.NNvect, self.groupops)
        self.vecstar = stars.VectorStarSet(self.star)
        self.rates = FCCrates()
        self.GF = GFcalc.GFcalc(self.lattice, self.NNvect, self.rates)

    def testConstructGF(self):
        """Test the construction of the GF using double-nn shell"""
        self.ConstructGF(2)


class VectorStarOmegalinearTests(unittest.TestCase):
    """Set of tests for our expansion of omega_1 in double-stars"""
    def setUp(self):
        self.lattice, self.NNvect, self.groupops, self.star = setuportho()
        self.dstar = stars.DoubleStarSet()
        self.vecstar = stars.VectorStarSet()
        self.rates = orthorates()

    def testConstructOmega1(self):
        self.star.generate(2) # we need at least 2nd nn to even have double-stars to worry about...
        self.dstar.generate(self.star)
        self.vecstar.generate(self.star)
        rate1expand = self.vecstar.rate1expansion(self.dstar)
        self.assertEqual(np.shape(rate1expand),
                         (self.vecstar.Nvstars, self.vecstar.Nvstars, self.dstar.Ndstars))
        om1expand = np.zeros(self.dstar.Ndstars)
        for nd, ds in enumerate(self.dstar.dstars):
            pair = ds[0]
            dv = self.star.pts[pair[0]]-self.star.pts[pair[1]]
            for vec, rate in zip(self.NNvect, self.rates):
                if all(abs(dv - vec) < 1e-8):
                    om1expand[nd] = rate
                    break
        # print om1expand
        for i in xrange(self.vecstar.Nvstars):
            for j in xrange(self.vecstar.Nvstars):
                # test the construction
                om1 = 0
                for Ri, vi in zip(self.vecstar.vecpos[i], self.vecstar.vecvec[i]):
                    for Rj, vj in zip(self.vecstar.vecpos[j], self.vecstar.vecvec[j]):
                        dv = Ri - Rj
                        for vec, rate in zip(self.NNvect, self.rates):
                            if all(abs(dv - vec) < 1e-8):
                                om1 += np.dot(vi, vj) * rate
                                break
                self.assertAlmostEqual(om1, np.dot(rate1expand[i, j, :], om1expand))
        # print(np.dot(rateexpand, om1expand))


class VectorStarFCCOmegalinearTests(VectorStarOmegalinearTests):
    """Set of tests for our expansion of omega_1 in double-stars for FCC"""
    def setUp(self):
        self.lattice, self.NNvect, self.groupops, self.star = setupFCC()
        self.dstar = stars.DoubleStarSet()
        self.vecstar = stars.VectorStarSet()
        self.rates = FCCrates()


class VectorStarOmega2linearTests(unittest.TestCase):
    """Set of tests for our expansion of omega_2 in NN stars"""
    def setUp(self):
        self.lattice, self.NNvect, self.groupops, self.star = setuportho()
        self.NNstar = stars.StarSet(self.NNvect, self.groupops)
        self.vecstar = stars.VectorStarSet()
        self.rates = orthorates()

    def testConstructOmega2(self):
        self.NNstar.generate(1) # we need the NN set of stars for NN jumps
        # construct the set of rates corresponding to the unique stars:
        om2expand = np.zeros(self.NNstar.Nstars)
        for vec, rate in zip(self.NNvect, self.rates):
            om2expand[self.NNstar.starindex(vec)] = rate
        self.star.generate(2) # go ahead and make a "large" set of stars
        self.vecstar.generate(self.star)
        rate2expand = self.vecstar.rate2expansion(self.NNstar)
        self.assertEqual(np.shape(rate2expand),
                         (self.vecstar.Nvstars, self.vecstar.Nvstars, self.NNstar.Nstars))
        for i in xrange(self.vecstar.Nvstars):
            # test the construction
            om2 = 0
            for Ri, vi in zip(self.vecstar.vecpos[i], self.vecstar.vecvec[i]):
                for vec, rate in zip(self.NNvect, self.rates):
                    if (vec == Ri).all():
                        # includes the factor of 2 to account for on-site terms in matrix.
                        om2 += -2. * np.dot(vi, vi) * rate
                        break
            self.assertAlmostEqual(om2, np.dot(rate2expand[i, i, :], om2expand))
            for j in xrange(self.vecstar.Nvstars):
                if j != i:
                    for d in xrange(self.NNstar.Nstars):
                        self.assertAlmostEquals(0, rate2expand[i, j, d])
        # print(np.dot(rate2expand, om2expand))


class VectorStarFCCOmega2linearTests(VectorStarOmega2linearTests):
    """Set of tests for our expansion of omega_2 in NN stars for FCC"""
    def setUp(self):
        self.lattice, self.NNvect, self.groupops, self.star = setupFCC()
        self.NNstar = stars.StarSet(self.NNvect, self.groupops)
        self.vecstar = stars.VectorStarSet()
        self.rates = FCCrates()


class VectorStarBias2linearTests(unittest.TestCase):
    """Set of tests for our expansion of bias vector (2) in NN stars"""
    def setUp(self):
        self.lattice, self.NNvect, self.groupops, self.star = setuportho()
        self.NNstar = stars.StarSet(self.NNvect, self.groupops)
        self.vecstar = stars.VectorStarSet()
        self.rates = orthorates()

    def testConstructBias2(self):
        self.NNstar.generate(1) # we need the NN set of stars for NN jumps
        # construct the set of rates corresponding to the unique stars:
        om2expand = np.zeros(self.NNstar.Nstars)
        for vec, rate in zip(self.NNvect, self.rates):
            om2expand[self.NNstar.starindex(vec)] = rate
        self.star.generate(2) # go ahead and make a "large" set of stars
        self.vecstar.generate(self.star)
        bias2expand = self.vecstar.bias2expansion(self.NNstar)
        self.assertEqual(np.shape(bias2expand),
                         (self.vecstar.Nvstars, self.NNstar.Nstars))
        biasvec = np.zeros((self.star.Npts, 3)) # bias vector: only the exchange hops
        for i, pt in enumerate(self.star.pts):
            for vec, rate in zip(self.NNvect, self.rates):
                if (vec == pt).all():
                    biasvec[i, :] += vec*rate
        # construct the same bias vector using our expansion
        biasveccomp = np.zeros((self.star.Npts, 3))
        for om2, svpos, svvec in zip(np.dot(bias2expand, om2expand),
                                     self.vecstar.vecpos,
                                     self.vecstar.vecvec):
            # test the construction
            for Ri, vi in zip(svpos, svvec):
                biasveccomp[self.star.pointindex(Ri), :] = om2*vi
        for i in xrange(self.star.Npts):
            for d in xrange(3):
                self.assertAlmostEqual(biasvec[i, d], biasveccomp[i, d])
        # print(biasvec)
        # print(np.dot(bias2expand, om2expand))


class VectorStarFCCBias2linearTests(VectorStarBias2linearTests):
    """Set of tests for our expansion of bias vector (2) in NN stars for FCC"""
    def setUp(self):
        self.lattice, self.NNvect, self.groupops, self.star = setupFCC()
        self.NNstar = stars.StarSet(self.NNvect, self.groupops)
        self.vecstar = stars.VectorStarSet()
        self.rates = FCCrates()


class VectorStarBias1linearTests(unittest.TestCase):
    """Set of tests for our expansion of bias vector (1) in double + NN stars"""
    def setUp(self):
        self.lattice, self.NNvect, self.groupops, self.star = setuportho()
        self.NNstar = stars.StarSet(self.NNvect, self.groupops)
        self.dstar = stars.DoubleStarSet()
        self.vecstar = stars.VectorStarSet()
        self.rates = orthorates()

    def testConstructBias1(self):
        self.NNstar.generate(1) # we need the NN set of stars for NN jumps
        # construct the set of rates corresponding to the unique stars:
        om0expand = np.zeros(self.NNstar.Nstars)
        for vec, rate in zip(self.NNvect, self.rates):
            om0expand[self.NNstar.starindex(vec)] = rate
        self.star.generate(2) # go ahead and make a "large" set of stars
        self.dstar.generate(self.star)
        om1expand = np.zeros(self.dstar.Ndstars)
        # in this case, we pick up omega_1 from omega_0... maybe not the most interesting case?
        # I think we make up for the "boring" rates here by having unusual probabilities below
        for i, ds in enumerate(self.dstar.dstars):
            p1, p2 = ds[0]
            dv = self.star.pts[p1] - self.star.pts[p2]
            sind = self.NNstar.starindex(dv)
            self.assertNotEqual(sind, -1)
            om1expand[i] = om0expand[sind]
        # print 'om0:', om0expand
        # print 'om1:', om1expand
        self.vecstar.generate(self.star)
        bias1ds, bias1prob, bias1NN = self.vecstar.bias1expansion(self.dstar, self.NNstar)
        self.assertEqual(np.shape(bias1ds),
                         (self.vecstar.Nvstars, self.dstar.Ndstars))
        self.assertEqual(np.shape(bias1prob),
                         (self.vecstar.Nvstars, self.dstar.Ndstars))
        self.assertEqual(np.shape(bias1NN),
                         (self.vecstar.Nvstars, self.NNstar.Nstars))
        self.assertIs(bias1prob.dtype, np.dtype('int64')) # needs to be for indexing
        # make sure that we don't have -1 as our endpoint probability for any ds that are used.
        for b1ds, b1p in zip(bias1ds, bias1prob):
            for ds, p in zip(b1ds, b1p):
                if p == -1:
                    self.assertEqual(ds, 0)
        # construct some fake probabilities for testing, with an "extra" star, set it's probability to 1
        # this is ONLY needed for testing purposes--the expansion should never access it.
        # note: this probability is to be the SQRT of the true probability
        # probsqrt = np.array([1,]*(self.star.Nstars+1)) # very little bias...
        probsqrt = np.sqrt(np.array([1.10**(self.star.Nstars-n) for n in range(self.star.Nstars + 1)]))
        probsqrt[-1] = 1 # this is important, as it represents our baseline "far-field"
        biasvec = np.zeros((self.star.Npts, 3)) # bias vector: all the hops *excluding* exchange
        for i, pt in enumerate(self.star.pts):
            for vec, rate in zip(self.NNvect, self.rates):
                if not all(abs(pt + vec) < 1e-8):
                    # note: starindex returns -1 if not found, which defaults to the final probability of 1.
                    biasvec[i, :] += vec*rate*probsqrt[self.star.starindex(pt + vec)]
        # construct the same bias vector using our expansion
        biasveccomp = np.zeros((self.star.Npts, 3))
        for om1, svpos, svvec in zip(np.dot(bias1ds * probsqrt[bias1prob], om1expand),
                                     self.vecstar.vecpos,
                                     self.vecstar.vecvec):
            # test the construction
            for Ri, vi in zip(svpos, svvec):
                biasveccomp[self.star.pointindex(Ri), :] += om1*vi
        for om0, svpos, svvec in zip(np.dot(bias1NN, om0expand),
                                     self.vecstar.vecpos,
                                     self.vecstar.vecvec):
            for Ri, vi in zip(svpos, svvec):
                biasveccomp[self.star.pointindex(Ri), :] += om0*vi

        for svpos, svvec in zip(self.vecstar.vecpos, self.vecstar.vecvec):
            for Ri, vi in zip(svpos, svvec):
                self.assertAlmostEqual(np.dot(vi, biasvec[self.star.pointindex(Ri)]),
                                       np.dot(vi, biasveccomp[self.star.pointindex(Ri)]),
                                       msg='Did not match dot product for {} along {} where {} != {}'.format(
                                           Ri, vi, biasvec[self.star.pointindex(Ri)],
                                           biasveccomp[self.star.pointindex(Ri)]
                                       ))

        for i, pt in enumerate(self.star.pts):
            for d in xrange(3):
                self.assertAlmostEqual(biasvec[i, d], biasveccomp[i, d],
                                       msg='Did not match point[{}] {} direction {} where {} != {}'.format(
                                           i, pt, d, biasvec[i, d], biasveccomp[i, d]))

        # print(np.dot(bias1ds * probsqrt[bias1prob], om1expand))
        # print(np.dot(bias1NN, om0expand))
        # print 'bias1ds', bias1ds
        # print 'bias1prob', bias1prob
        # print 'bias1NN', bias1NN
        # print 'biasvec, biasveccomp:'
        # for bv, bvc in zip(biasvec, biasveccomp):
        #     print bv, bvc


class VectorStarFCCBias1linearTests(VectorStarBias1linearTests):
    """Set of tests for our expansion of bias vector (1) in double + NN stars for FCC"""
    def setUp(self):
        self.lattice, self.NNvect, self.groupops, self.star = setupFCC()
        self.NNstar = stars.StarSet(self.NNvect, self.groupops)
        self.dstar = stars.DoubleStarSet()
        self.vecstar = stars.VectorStarSet()
        self.rates = FCCrates()


class VectorStarOnsite1linearTests(unittest.TestCase):
    """Set of tests for our expansion of onsite terms of omega (1) in double + NN stars"""
    def setUp(self):
        self.lattice, self.NNvect, self.groupops, self.star = setuportho()
        self.NNstar = stars.StarSet(self.NNvect, self.groupops)
        self.dstar = stars.DoubleStarSet()
        self.vecstar = stars.VectorStarSet()
        self.rates = orthorates()

    def testConstructOnsite1(self):
        self.NNstar.generate(1) # we need the NN set of stars for NN jumps
        # construct the set of rates corresponding to the unique stars:
        om0expand = np.zeros(self.NNstar.Nstars)
        for vec, rate in zip(self.NNvect, self.rates):
            om0expand[self.NNstar.starindex(vec)] = rate
        self.star.generate(2) # go ahead and make a "large" set of stars
        self.dstar.generate(self.star)
        om1expand = np.zeros(self.dstar.Ndstars)
        # in this case, we pick up omega_1 from omega_0... maybe not the most interesting case?
        # I think we make up for the "boring" rates here by having unusual probabilities below
        for i, ds in enumerate(self.dstar.dstars):
            p1, p2 = ds[0]
            dv = self.star.pts[p1] - self.star.pts[p2]
            sind = self.NNstar.starindex(dv)
            self.assertNotEqual(sind, -1)
            om1expand[i] = om0expand[sind]
        # print 'om0:', om0expand
        # print 'om1:', om1expand
        self.vecstar.generate(self.star)
        omega1ds, omega1prob, omega1NN = self.vecstar.rate1onsiteexpansion(self.dstar, self.NNstar)
        self.assertEqual(np.shape(omega1ds),
                         (self.vecstar.Nvstars, self.dstar.Ndstars))
        self.assertEqual(np.shape(omega1prob),
                         (self.vecstar.Nvstars, self.dstar.Ndstars))
        self.assertEqual(np.shape(omega1NN),
                         (self.vecstar.Nvstars, self.NNstar.Nstars))
        self.assertIs(omega1prob.dtype, np.dtype('int64')) # needs to be for indexing
        # make sure that we don't have -1 as our endpoint probability for any ds that are used.
        for b1ds, b1p in zip(omega1ds, omega1prob):
            for ds, p in zip(b1ds, b1p):
                if p == -1:
                    self.assertEqual(ds, 0)
        # construct some fake probabilities for testing, with an "extra" star, set it's probability to 1
        # this is ONLY needed for testing purposes--the expansion should never access it.
        # note: this probability is to be the SQRT of the true probability
        # probsqrt = np.array([1,]*(self.star.Nstars+1)) # very little bias...
        probsqrt = np.sqrt(np.array([1.10**(self.star.Nstars-n) for n in range(self.star.Nstars + 1)]))
        probsqrt[-1] = 1 # this is important, as it represents our baseline "far-field"
        biasvec = np.zeros((self.star.Npts, 3)) # bias vector: all the hops *excluding* exchange
        for i, pt in enumerate(self.star.pts):
            for vec, rate in zip(self.NNvect, self.rates):
                if not all(abs(pt + vec) < 1e-8):
                    # note: starindex returns -1 if not found, which defaults to the final probability of 1.
                    biasvec[i, :] += vec*rate*probsqrt[self.star.starindex(pt + vec)]
        # construct the same bias vector using our expansion
        biasveccomp = np.zeros((self.star.Npts, 3))
        for om1, svpos, svvec in zip(np.dot(omega1ds * probsqrt[omega1prob], om1expand),
                                     self.vecstar.vecpos,
                                     self.vecstar.vecvec):
            # test the construction
            for Ri, vi in zip(svpos, svvec):
                biasveccomp[self.star.pointindex(Ri), :] += om1*vi
        for om0, svpos, svvec in zip(np.dot(omega1NN, om0expand),
                                     self.vecstar.vecpos,
                                     self.vecstar.vecvec):
            for Ri, vi in zip(svpos, svvec):
                biasveccomp[self.star.pointindex(Ri), :] += om0*vi

        for svpos, svvec in zip(self.vecstar.vecpos, self.vecstar.vecvec):
            for Ri, vi in zip(svpos, svvec):
                self.assertAlmostEqual(np.dot(vi, biasvec[self.star.pointindex(Ri)]),
                                       np.dot(vi, biasveccomp[self.star.pointindex(Ri)]),
                                       msg='Did not match dot product for {} along {} where {} != {}'.format(
                                           Ri, vi, biasvec[self.star.pointindex(Ri)],
                                           biasveccomp[self.star.pointindex(Ri)]
                                       ))

        for i, pt in enumerate(self.star.pts):
            for d in xrange(3):
                self.assertAlmostEqual(biasvec[i, d], biasveccomp[i, d],
                                       msg='Did not match point[{}] {} direction {} where {} != {}'.format(
                                           i, pt, d, biasvec[i, d], biasveccomp[i, d]))

        # print(np.dot(omega1ds * probsqrt[omega1prob], om1expand))
        # print(np.dot(omega1NN, om0expand))
        # print 'omega1ds', omega1ds
        # print 'omega1prob', omega1prob
        # print 'omega1NN', omega1NN
        # print 'biasvec, biasveccomp:'
        # for bv, bvc in zip(biasvec, biasveccomp):
        #     print bv, bvc


class VectorStarFCCOnsite1linearTests(VectorStarOnsite1linearTests):
    """Set of tests for our expansion of bias vector (1) in double + NN stars for FCC"""
    def setUp(self):
        self.lattice, self.NNvect, self.groupops, self.star = setupFCC()
        self.NNstar = stars.StarSet(self.NNvect, self.groupops)
        self.dstar = stars.DoubleStarSet()
        self.vecstar = stars.VectorStarSet()
        self.rates = FCCrates()
