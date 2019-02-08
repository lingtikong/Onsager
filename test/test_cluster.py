"""
Unit tests for star, double-star and vector-star generation and indexing,
rebuilt to use crystal
"""

__author__ = 'Dallas R. Trinkle'

#

import unittest
import numpy as np
from onsager import crystal, cluster, supercell


class ClusterSiteTests(unittest.TestCase):
    """Tests of the ClusterSite class"""
    longMessage = False

    def testClusterSiteType(self):
        """Can we make cluster sites?"""
        site = cluster.ClusterSite((0,0), np.array([0,0,0]))
        self.assertIsInstance(site, cluster.ClusterSite)

    def testNegation(self):
        """Can we negate (and equate) cluster sites?"""
        s1 = cluster.ClusterSite((0,0), np.array([1,0,0]))
        s2 = cluster.ClusterSite((0,0), np.array([-1,0,0]))
        self.assertNotEqual(s1, s2)
        self.assertEqual(s1, -s2)

    def testAddition(self):
        """Can we add lattice vectors to a site?"""
        s1 = cluster.ClusterSite((0,0), np.array([0,0,0]))
        s2 = cluster.ClusterSite((0,0), np.array([1,0,0]))
        s3 = cluster.ClusterSite((0,0), np.array([-1,0,0]))
        v1 = np.array([1,0,0])
        self.assertNotEqual(s1, s2)
        self.assertNotEqual(s1, s3)
        self.assertEqual(s1+v1, s2)
        self.assertNotEqual(s1-v1, s2)
        self.assertEqual(s1-v1, s3)
        self.assertNotEqual(s1+v1, s3)

class ClusterTests(unittest.TestCase):
    """Tests of the Cluster class"""
    longMessage = False

    def testMakeCluster(self):
        """Can we make a cluster?"""
        s = cluster.ClusterSite((0,0), np.array([0,0,0]))
        cl = cluster.Cluster([s])
        self.assertIsInstance(cl, cluster.Cluster)
        Rlist = [np.array([0,0,0]), np.array([1,0,0]), np.array([-1,0,0])]
        cl = cluster.Cluster(cluster.ClusterSite((0, n), R)
                             for n, R in enumerate(Rlist))
        self.assertIsInstance(cl, cluster.Cluster)

    def testEquality(self):
        """Equality tests"""
        s1 = cluster.ClusterSite((0,0), np.array([0,0,0]))
        s2 = cluster.ClusterSite((0,0), np.array([1,0,0]))
        c1 = cluster.Cluster([s1])
        c2 = cluster.Cluster([s2])
        c3 = cluster.Cluster([s1, s2])
        c4 = cluster.Cluster([s2, s1])
        self.assertEqual(c1, c2)
        self.assertNotEqual(c1, c3)
        self.assertEqual(c3, c4)

    def testAddition(self):
        """Making a cluster via addition"""
        s1 = cluster.ClusterSite((0,0), np.array([0,0,0]))
        s2 = cluster.ClusterSite((0,0), np.array([1,0,0]))
        c1 = cluster.Cluster([s1])
        c2 = c1 + s2
        c3 = cluster.Cluster([s2, s1])
        self.assertEqual(c2, c3)

    def testSubtraction(self):
        """Removal of a state via subtraction"""
        s1 = cluster.ClusterSite((0,0), np.array([0,0,0]))
        s2 = cluster.ClusterSite((0,0), np.array([1,0,0]))
        s3 = cluster.ClusterSite((0,0), np.array([0,1,0]))
        c1 = cluster.Cluster([s1])
        c2 = cluster.Cluster([s1, s2])
        c3 = cluster.Cluster([s1, s2, s3])
        self.assertEqual([], c1-s1)
        # we can subtract a cluster site then "add" it back in.
        for cl in [c2, c3]:
            for cs in cl:
                cs0 = cluster.ClusterSite(ci=cs.ci, R=np.zeros(3, dtype=int))
                self.assertEqual(cl, cluster.Cluster((cl - cs) + [cs0]))
        with self.assertRaises(ArithmeticError):
            lis = c2 - s3

    def testHash(self):
        """Can we make a set of clusters?"""
        s1 = cluster.ClusterSite((0,0), np.array([0,0,0]))
        s2 = cluster.ClusterSite((0,0), np.array([1,0,0]))
        c1 = cluster.Cluster([s1])
        c2 = cluster.Cluster([s2])
        c3 = c1 + s2
        set1 = set([c1])
        set2 = set([c1, c2])
        set3 = set([c1, c3])
        set4 = set([c2, c3])
        self.assertEqual(set1, set2)
        self.assertNotEqual(set1, set3)
        self.assertEqual(set3, set4)

    def testTS(self):
        """Test the creation of transition state clusters"""
        s1 = cluster.ClusterSite((0,0), np.array([0,0,0]))
        s2 = cluster.ClusterSite((0,0), np.array([1,0,0]))
        s3 = cluster.ClusterSite((0,0), np.array([0,1,0]))
        c0 = cluster.Cluster([s1, s2, s3])
        c1 = cluster.Cluster([s1, s2, s3], transition=True)
        c2 = cluster.Cluster([s2, s1, s3], transition=True)
        c3 = cluster.Cluster([s1, s3, s2], transition=True)
        self.assertNotEqual(c0, c1, msg='Clusters should not be equal:\n{} ==\n{}'.format(c0, c1))
        self.assertEqual(c1, c2, msg='Clusters should be equal:\n{} !=\n{}'.format(c1, c2))
        self.assertNotEqual(c1, c3, msg='Clusters should not be equal:\n{} ==\n{}'.format(c1, c3))
        # check TS and indexing...
        self.assertEqual(1, len(c1))
        self.assertEqual(1, c1.Norder)
        self.assertEqual((s1, s2), c1.transitionstate())
        l = [site for site in c1]
        self.assertEqual(1, len(l))
        self.assertEqual([s3], l)
        self.assertEqual(s3, c1[0])
        self.assertEqual(s3, c1[-1])

        self.assertEqual((s1, s3), c3.transitionstate())
        l = [site for site in c3]
        self.assertEqual(1, len(l))
        self.assertEqual([s2], l)
        self.assertEqual(s2, c3[0])
        self.assertEqual(s2, c3[-1])

    def testHCPGroupOp(self):
        """Testing group operations on our clusters (HCP)"""
        HCP = crystal.Crystal.HCP(1., chemistry='HCP')
        s1 = cluster.ClusterSite((0, 0), np.array([0, 0, 0]))
        s2 = cluster.ClusterSite((0, 1), np.array([0, 0, 0]))
        s3 = cluster.ClusterSite((0, 0), np.array([1, 0, 0]))

        cl = cluster.Cluster([s1])
        clusterset = set([cl.g(HCP, g) for g in HCP.G])
        self.assertEqual(len(clusterset), 2)

        cl = cluster.Cluster([s1, s2])
        clusterset = set([cl.g(HCP, g) for g in HCP.G])
        self.assertEqual(len(clusterset), 6)

        cl = cluster.Cluster([s1, s3])
        clusterset = set([cl.g(HCP, g) for g in HCP.G])
        self.assertEqual(len(clusterset), 6)

    def testFCCGroupOp(self):
        """Testing group operations on our clusters (FCC)"""
        FCC = crystal.Crystal.FCC(1., chemistry='FCC')
        s1 = cluster.ClusterSite.fromcryscart(FCC, np.array([0, 0, 0]))
        s2 = cluster.ClusterSite.fromcryscart(FCC, np.array([0., 0.5, 0.5]))
        s3 = cluster.ClusterSite.fromcryscart(FCC, np.array([0.5, 0., 0.5]))
        s4 = cluster.ClusterSite.fromcryscart(FCC, np.array([0.5, 0.5, 0.]))
        s5 = cluster.ClusterSite.fromcryscart(FCC, np.array([0., 0.5, -0.5]))

        # only one way to make a single site:
        cl = cluster.Cluster([s1])
        clusterset = set([cl.g(FCC, g) for g in FCC.G])
        self.assertEqual(1, len(clusterset), msg='Failure on single site')

        # six ways to make a NN pair: multiplicity of <110>, divided by 2
        cl = cluster.Cluster([s1, s2])
        clusterset = set([cl.g(FCC, g) for g in FCC.G])
        self.assertEqual(6, len(clusterset), msg='Failure on NN pair')

        # eight ways to make a NN triplet: multiplicity of <111> (the plane normal of the face)
        cl = cluster.Cluster([s1, s2, s3])
        clusterset = set([cl.g(FCC, g) for g in FCC.G])
        self.assertEqual(8, len(clusterset), msg='Failure on NN triplet')

        # twelve ways to make a "wide" triplet: multiplicity of <100> times two
        cl = cluster.Cluster([s1, s2, s5])
        clusterset = set([cl.g(FCC, g) for g in FCC.G])
        self.assertEqual(12, len(clusterset), msg='Failure on wide NN triplet')

        # two ways to make our tetrahedron
        cl = cluster.Cluster([s1, s2, s3, s4])
        clusterset = set([cl.g(FCC, g) for g in FCC.G])
        self.assertEqual(2, len(clusterset), msg='Failure on NN quad')

        # test out transition state cluster:
        # [110] transition, with two neighbors occupied... 6 different directions x 2 pairs
        # as 110 is a 2-fold rotation axis
        cl = cluster.Cluster([s1, s2, s3, s4], transition=True)
        clusterset = set([cl.g(FCC, g) for g in FCC.G])
        self.assertEqual(12, len(clusterset), msg='Failure on transition state cluster')

    def testmakeclustersFCC(self):
        """Does makeclusters perform as expected? FCC"""
        FCC = crystal.Crystal.FCC(1., chemistry='FCC')
        clusterexp = cluster.makeclusters(FCC, 0.8, 4)
        self.assertEqual(4, len(clusterexp))
        self.assertEqual([1, 6, 8, 2], [len(clset) for clset in clusterexp])

    def testmakeclustersB2(self):
        """Does makeclusters perform as expected? B2"""
        B2 = crystal.Crystal(np.eye(3), [[np.zeros(3)], [0.5*np.ones(3)]], chemistry=['A', 'B'])
        clusterexp = cluster.makeclusters(B2, 1.01, 4)
        # now, we should have the following types of clusters:
        # 2 1st order (A, B)
        # 3 2nd order (AA, BB, AB)
        # 2 3rd order (AAB, BBA)
        # 1 4th order (AABB)
        self.assertEqual(2+3+2+1, len(clusterexp))
        for clset in clusterexp[0:2]:
            self.assertEqual(1, len(clset))
        for clset in clusterexp[2:5]:
            cl = next(iter(clset))
            if cl[0].ci == cl[1].ci:
                self.assertEqual(3, len(clset))
            else:
                self.assertEqual(8, len(clset))
        for clset in clusterexp[5:7]:
            self.assertEqual(12, len(clset))
        for clset in clusterexp[7:8]:
            self.assertEqual(12, len(clset))

    def testmakeTSclustersFCC(self):
        """Does makeTSclusters perform as expected? FCC"""
        FCC = crystal.Crystal.FCC(1., chemistry='FCC')
        clusterexp = cluster.makeclusters(FCC, 0.8, 4)
        chem = 0
        jumpnetwork = FCC.jumpnetwork(chem, 0.8)
        TSclusterexp = cluster.makeTSclusters(FCC, chem, jumpnetwork, clusterexp)
        self.assertEqual(3, len(TSclusterexp))
        self.assertEqual([6, 24, 12], [len(csset) for csset in TSclusterexp])
        for TSclustset in TSclusterexp:
            for TSclust in TSclustset:
                self.assertTrue(np.all(np.zeros(3, dtype=int)==TSclust.transitionstate()[0].R))

    def testmakeTSclustersB2(self):
        """Does makeTSclusters perform as expected? B2"""
        B2 = crystal.Crystal(np.eye(3), [[np.zeros(3)], [0.5*np.ones(3)]], chemistry=['A', 'B'])
        clusterexp = cluster.makeclusters(B2, 1.01, 4)
        chem = 0
        jumpnetwork = B2.jumpnetwork(chem, 1.01)
        TSclusterexp = cluster.makeTSclusters(B2, chem, jumpnetwork, clusterexp)
        self.assertEqual(3, len(TSclusterexp))
        self.assertEqual([3, 12, 12], [len(csset) for csset in TSclusterexp])
        for TSclustset in TSclusterexp:
            for TSclust in TSclustset:
                self.assertTrue(np.all(np.zeros(3, dtype=int)==TSclust.transitionstate()[0].R))


class MonteCarloTests(unittest.TestCase):
    """Tests of the MonteCarloSampler class"""
    longMessage = False

    def setUp(self):
        self.FCC = crystal.Crystal.FCC(1., 'FCC')
        self.superlatt = 4*np.eye(3, dtype=int)
        self.sup = supercell.ClusterSupercell(self.FCC, self.superlatt)
        self.clusterexp = cluster.makeclusters(self.FCC, 0.8, 4)
        self.Evalues = np.random.normal(size=len(self.clusterexp) + 1)
        # self.Evalues = np.zeros(len(self.clusterexp) + 1)
        self.MC = cluster.MonteCarloSampler(self.sup, np.zeros(0), self.clusterexp, self.Evalues)
        self.chem = 0
        self.jumpnetwork = self.FCC.jumpnetwork(self.chem, 0.8)
        self.TSclusterexp = cluster.makeTSclusters(self.FCC, self.chem, self.jumpnetwork, self.clusterexp)
        self.KRAvalues = np.zeros(len(self.jumpnetwork))
        self.TSvalues = np.random.normal(size=len(self.TSclusterexp))
        # self.TSvalues = np.ones(len(self.TSclusterexp))
        # self.TSvalues = np.zeros(len(self.TSclusterexp))
        self.MCjn = cluster.MonteCarloSampler(self.sup, np.zeros(0), self.clusterexp, self.Evalues,
                                              self.chem, self.jumpnetwork, KRAvalues=self.KRAvalues,
                                              TSclusters=self.TSclusterexp, TSvalues=self.TSvalues)

    def testMakeSampler(self):
        """Can we make a MonteCarlo sampler for an FCC lattice?"""
        self.assertIsInstance(self.MC, cluster.MonteCarloSampler)
        with self.assertRaises(ValueError):
            self.MC.transitions()
        self.assertIsInstance(self.MCjn, cluster.MonteCarloSampler)

    def testStart(self):
        """Does start() perform as expected?"""
        for MCsampler in (self.MC, self.MCjn):
            occ = np.random.choice((0, 1), size=self.sup.size)
            MCsampler.start(occ)
            for i, occ_i in enumerate(occ):
                if occ_i == 1:
                    self.assertIn(i, MCsampler.occupied_set)
                    self.assertNotIn(i, MCsampler.unoccupied_set)
                else:
                    self.assertIn(i, MCsampler.unoccupied_set)
                    self.assertNotIn(i, MCsampler.occupied_set)

    def testE(self):
        """Does our energy evaluator perform correctly?"""
        occ = np.random.choice((0,1), size=self.sup.size)
        self.MC.start(occ)
        self.MCjn.start(occ.copy())  # necessary because sampler *does not* make a copy.
        for nchanges in range(16):
            EMC = self.MC.E()
            EMCjn = self.MCjn.E()
            Ecluster = np.dot(self.Evalues, self.sup.evalcluster(occ, np.zeros(0), self.clusterexp))
            self.assertAlmostEqual(Ecluster, EMC, msg='MC evaluation {} != {} cluster evaluation?'.format(EMC, Ecluster))
            self.assertAlmostEqual(EMC, EMCjn, msg='MC evaluation {} != {} MC jn evaluation?'.format(EMC, EMCjn))
            # randomly occupy or unoccupy a site:
            if np.random.choice((True, False)):
                change = [np.random.choice(list(self.MC.unoccupied_set))]
                self.MC.update(change, ())
                self.MCjn.update(change, ())
            else:
                change = [np.random.choice(list(self.MC.occupied_set))]
                self.MC.update((), change)
                self.MCjn.update((), change)

    def testdeltaE(self):
        """Does our trial energy change work?"""
        occ = np.random.choice((0,1), size=self.sup.size)
        self.MC.start(occ)
        self.MCjn.start(occ.copy())  # necessary because sampler *does not* make a copy.
        EMC = self.MC.E()
        EMCjn = self.MCjn.E()
        for nchanges in range(64):
            # select multiple sites to swap (between 1 and 4 sites):
            nswap = np.random.choice(4)+1
            iocc = np.random.choice(list(self.MC.unoccupied_set), size=nswap, replace=False)
            iunocc = np.random.choice(list(self.MC.occupied_set), size=nswap, replace=False)
            dE = self.MC.deltaE_trial(iocc, iunocc)
            dEjn = self.MCjn.deltaE_trial(iocc, iunocc)
            # now, update and see if we correctly computed the change in energy:
            self.MC.update(iocc, iunocc)
            self.MCjn.update(iocc, iunocc)
            EMC_new = self.MC.E()
            EMCjn_new = self.MCjn.E()
            self.assertAlmostEqual(EMC_new - EMC, dE, msg='Trial energy change wrong? {} != {}-{}'.format(dE, EMC_new, EMC))
            self.assertAlmostEqual(EMCjn_new - EMCjn, dEjn, msg='Trial energy change wrong (jn)? {} != {}-{}'.format(dEjn, EMCjn_new, EMCjn))
            self.assertAlmostEqual(dE, dEjn, msg='Trial energy change differs (without/with jn)? {} != {}'.format(dE, dEjn))
            EMC = EMC_new
            EMCjn = EMCjn_new

    def testDetailedBalance(self):
        """Does our jump network evaluator obey detailed balance?"""
        occ = np.random.choice((0,1), size=self.sup.size)
        self.MCjn.start(occ)
        ijlist, Qlist, dxlist = self.MCjn.transitions()
        self.assertEqual(len(ijlist), len(Qlist))
        self.assertEqual(len(ijlist), len(dxlist))
        self.assertLessEqual(len(Qlist), len(self.MCjn.jumps))
        for (i, j), Q, dx in zip(ijlist, Qlist, dxlist):
            dE = self.MCjn.deltaE_trial((j,), (i,))
            # print(i, j, Q, dE, dx)
            self.MCjn.update((j,), (i,)) # select the transition
            ijlistnew, Qlistnew, dxlistnew = self.MCjn.transitions()
            self.assertIn((j, i), ijlistnew)
            self.assertNotIn((i, j), ijlistnew)
            m = ijlistnew.index((j, i))
            self.assertTrue(np.allclose(dxlistnew[m] + dx, 0))
            self.assertAlmostEqual(Q, Qlistnew[m] + dE)
            self.MCjn.update((i,), (j,)) # put state back



if __name__ == '__main__':
    unittest.main()
