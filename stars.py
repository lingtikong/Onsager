"""
Stars module

Classes to generate stars and double stars; a lot of indexing functionality.
"""

# TODO: need to make sure we can read / write stars for optimal functionality (or pickle?)

__author__ = 'Dallas R. Trinkle'

import numpy as np


class Star:
    """
    A class to construct stars, and be able to efficiently index.
    """
    def __init__(self, NNvect, groupops, Nshells=0):
        """
        Initiates a star-generator for a given set of nearest-neighbor vectors
        and group operations. Explicitly *excludes* the trivial star R=0.

        Parameters
        ----------
        NNvect : array [:, 3]
            set of nearest-neighbor vectors; will also be used to generate indexing

        groupops : array [:, 3, 3]
            point group operations, in Cartesian coordinates

        Nshells : integer, optional
            number of shells to generate
        """
        self.NNvect = NNvect
        self.groupops = groupops
        self.generate(Nshells)

    def generate(self, Nshells, threshold=1e-8):
        """
        Construct the actual points and stars.

        Parameters
        ----------
        Nshells : integer
            number of shells to generate

        threshold : float, optional
            threshold for determining equality with symmetry

        Notes
        -----
        This code is rather similar to what's in KPTmesh.
        """
        if Nshells == 0:
            self.Nshells = 0
            self.Nstars = 0
            self.Npts = 0
            return
        if Nshells == self.Nshells:
            return
        self.Nshells = Nshells
        # list of all vectors to consider
        vectlist = [v for v in self.NNvect]
        lastshell = list(vectlist)
        for i in range(Nshells-1):
            # add all NNvect to last shell produced, always excluding 0
            lastshell = [v1+v2 for v1 in lastshell for v2 in self.NNvect if not all(abs(v1 + v2) < threshold)]
            vectlist += lastshell
        # now to sort our set of vectors (easiest by magnitude, and then reduce down:
        vectlist.sort(key=lambda x: np.vdot(x, x))
        x2_indices = []
        x2old = np.vdot(vectlist[0], vectlist[0])
        for i, x2 in enumerate([np.vdot(x, x) for x in vectlist]):
            if x2 > (x2old + threshold):
                x2_indices.append(i)
                x2old = x2
        x2_indices.append(len(vectlist))
        # x2_indices now contains a list of indices with the same magnitudes
        self.stars = []
        ptlist = []
        xmin = 0
        for xmax in x2_indices:
            complist_stars = [] # for finding unique stars
            complist_pts = []   # for finding unique points
            for x in vectlist[xmin:xmax]:
                # Q1: is this a unique point?
                if any([np.all(abs(x - xcomp) < threshold) for xcomp in complist_pts]):
                    continue
                complist_pts.append(x)
                # Q2: is this a new rep. for a unique star?
                match = False
                for i, s in enumerate(complist_stars):
                    if self.symmatch(x, s[0], threshold):
                        # update star
                        complist_stars[i].append(x)
                        match = True
                        continue
                if not match:
                    # new symmetry point!
                    complist_stars.append([x])
            self.stars += complist_stars
            ptlist += complist_pts
            xmin=xmax
        self.pts = np.array(ptlist)
        self.Nstars = len(self.stars)
        self.Npts = len(self.pts)
        self.index = None

    def generateindices(self):
        """
        Generates the star indices for the set of points, if not already generated
        """
        if self.index != None:
            return
        self.index = np.zeros(self.Npts, dtype=int)
        for i, v in enumerate(self.pts):
            for ns, s in enumerate(self.stars):
                if np.dot(v, v) != np.dot(s[0], s[0]):
                    continue
                if any([all(v == v1) for v1 in s]):
                    self.index[i] = ns

    def starindex(self, x, threshold=1e-8):
        """
        Returns the index for the star to which vector x belongs.

        Parameters
        ----------
        x : array [3]
            vector to check against star

        threshold : float, optional
            threshold for equality

        Returns
        -------
        index corresponding to star; -1 if not found.
        """
        self.generateindices()
        for i, v in enumerate(self.pts):
            if all(abs(x - v) < threshold):
                return self.index[i]
        return -1

    def pointindex(self, x, threshold=1e-8):
        """
        Returns the index corresponding to the point x.

        Parameters
        ----------
        x : array [3]
            vector to check against star

        threshold : float, optional
            threshold for equality

        Returns
        -------
        index corresponding to point; -1 if not found.
        """
        for i, v in enumerate(self.pts):
            if all(abs(x - v) < threshold):
                return i
        return -1

    def symmatch(self, x, xcomp, threshold=1e-8):
        """
        Tells us if x and xcomp are equivalent by a symmetry group

        Parameters
        ----------
        x : array [3]
            vector to be tested
        xcomp : array [3]
            vector to compare
        threshold : double, optional
            threshold to use for "equality"

        Returns
        -------
        True if equivalent by a point group operation, False otherwise
        """
        return any([np.all(abs(x - np.dot(g, xcomp)) < threshold) for g in self.groupops])


class DoubleStar:
    """
    A class to construct double-stars (pairs of sites,
    where each pair is related by a single group op).
    """
    def __init__(self, star=None):
        """
        Initiates a double-star-generator; is designed to work with a given star.

        Parameters
        ----------
        star : Star, optional
            all of our input parameters will come from this, if non-empty
        """
        self.star = None
        self.Ndstars = 0
        self.Npairs = 0
        self.Npts = 0
        if star != None:
            self.NNvect = star.NNvect
            self.groupops = star.groupops
            if self.star.Nshells > 0:
                self.generate(star)

    def generate(self, star, threshold=1e-8):
        """
        Construct the actual double-stars.

        Parameters
        ----------
        star : Star, optional
            all of our input parameters will come from this, if non-empty
        """
        if star.Nshells == 0:
            self.Npairs = 0
            return
        if star == self.star and star.Npts == self.Npts:
            return
        self.star = star
        self.Npts = star.Npts
        self.NNvect = star.NNvect
        self.groupops = star.groupops
        self.pairs = []
        # make the pairs first
        for i1, v1 in enumerate(self.star.pts):
            for dv in self.NNvect:
                v2 = v1 + dv
                i2 = self.star.pointindex(v2)
                # check that i2 is a valid point
                if i2 >= 0:
                    self.pairs.append((i1, i2))
        # sort the pairs
        self.pairs.sort(key=lambda x: max(np.dot(x[0], x[0]), np.dot(x[1], x[1])))
        self.Npairs = len(self.pairs)
        # now to make the unique sets of pairs (double-stars)
        self.dstars = []
        for pair in self.pairs:
            # Q: is this a new rep. for a unique double-star?
            match = False
            for i, ds in enumerate(self.dstars):
                if self.symmatch(pair, ds[0], threshold):
                    # update star
                    self.dstars[i].append(pair)
                    match = True
                    continue
            if not match:
                # new symmetry point!
                self.dstars.append([pair])
        self.Ndstars = len(self.dstars)
        self.index = None

    def generateindices(self):
        """
        Generates the double star indices for the set of points, if not already generated
        """
        if self.index != None:
            return
        self.index = np.zeros(self.Npairs, dtype=int)
        for i, p in enumerate(self.pairs):
            for nds, ds in enumerate(self.dstars):
                if any([p == p1 for p1 in ds]):
                    self.index[i] = nds

    def dstarindex(self, p):
        """
        Returns the index for the double-star to which pair p belongs.

        Parameters
        ----------
        p : two-tuple
            pair to find the double-star for

        Returns
        -------
        index corresponding to double-star; -1 if not found.
        """
        self.generateindices()
        for i, p1 in enumerate(self.pairs):
            if p1 == p:
                return self.index[i]
        return -1

    def pairindex(self, p):
        """
        Returns the index corresponding to the pair p.

        Parameters
        ----------
        p : two-tuple
            pair to index

        Returns
        -------
        index corresponding to pair; -1 if not found.
        """
        for i, v in enumerate(self.pairs):
            if v == p:
                return i
        return -1

    def symmatch(self, x, xcomp, threshold=1e-8):
        """
        Tells us if x and xcomp are equivalent by a symmetry group

        Parameters
        ----------
        x : 2-tuple
            two indices corresponding to a pair
        xcomp : 2-tuple
            two indices corresponding to a pair to compare
        threshold : double, optional
            threshold to use for "equality"

        Returns
        -------
        True if equivalent by a point group operation, False otherwise
        """
        # first, try the tuple "forward"
        v00 = self.star.pts[x[0]]
        v01 = self.star.pts[x[1]]
        v10 = self.star.pts[xcomp[0]]
        v11 = self.star.pts[xcomp[1]]
        if any([np.all(abs(v00 - np.dot(g, v10)) < threshold) and np.all(abs(v01 - np.dot(g, v11)) < threshold)
                for g in self.groupops]):
            return True
        return any([np.all(abs(v00 - np.dot(g, v11)) < threshold) and np.all(abs(v01 - np.dot(g, v10)) < threshold)
                for g in self.groupops])

class StarVector:
    """
    A class to construct star-vectors, and be able to efficiently index.
    """
    def __init__(self, star=None):
        """
        Initiates a star-vector-generator; is designed to work with a given star.

        Parameters
        ----------
        star : Star, optional
            all of our input parameters will come from this, if non-empty
        """
        self.star = None
        self.Npts = 0
        self.Nstarvects = 0
        self.Nstars = 0
        if star != None:
            self.NNvect = star.NNvect
            self.groupops = star.groupops
            if star.Nshells > 0:
                self.generate(star)

    def generate(self, star, threshold=1e-8):
        """
        Construct the actual star-vectors

        Parameters
        ----------
        star : Star, optional
            all of our input parameters will come from this, if non-empty
        """
        if star.Nshells == 0:
            return
        if star == self.star and star.Npts == self.Npts:
            return
        self.star = star
        self.Npts = star.Npts
        self.NNvect = star.NNvect
        self.groupops = star.groupops
        self.starvecpos = []
        self.starvecvec = []
        for s in self.star.stars:
            # start by generating the parallel star-vector; always trivially present:
            self.starvecpos.append(s)
            scale = 1./np.sqrt(len(s)*np.dot(s[0],s[0])) # normalization factor
            self.starvecvec.append([v*scale for v in s])
            # next, try to generate perpendicular star-vectors, if present:
            v0 = np.cross(s[0], np.array([0, 0, 1]))
            if np.dot(v0, v0) < threshold:
                v0 = np.cross(s[0], np.array([1, 0, 0]))
            v1 = np.cross(s[0], v0)
            # normalization:
            v0 /= np.sqrt(np.dot(v0, v0))
            v1 /= np.sqrt(np.dot(v1, v1))
            Nvect = 2
            # run over the invariant group operations for vector s[0]:
            for g in [g0 for g0 in self.groupops if all(abs(np.dot(g0, s[0]) - s[0]) < threshold)]:
                if Nvect == 0:
                    continue
                gv0 = np.dot(g, v0)
                if Nvect == 1:
                    # we only need to check that we still have an invariant vector
                    if any(abs(gv0 - v0) > threshold):
                        Nvect = 0
                if Nvect == 2:
                    gv1 = np.dot(g, v1)
                    g00 = np.dot(v0, gv0)
                    g11 = np.dot(v1, gv1)
                    g01 = np.dot(v0, gv1)
                    g10 = np.dot(v1, gv0)
                    if abs((abs(g00*g11 - g01*g10) - 1)) > threshold:
                        # we don't have an orthogonal matrix, so kick out
                        Nvect = 0
                        continue
                    if abs(g01-g10) > threshold:
                        # we have a rotation... so the only eigenvalues are complex conjugate pairs
                        Nvect = 0
                        continue
                    if (abs(g00 - 1) > threshold) or (abs(g11 - 1) > threshold):
                        if abs(g00 - 1) > threshold:
                            Nvect = 1
                            continue
                        if abs(g11 - 1) > threshold:
                            v1 = v0
                            Nvect = 1
                            continue
                        v0 = (g01*v0 + (1 - g00)*v1)/np.sqrt(g01*g10 + (1 - g00)**2)
                        Nvect = 1
            # so... do we have any vectors to add?
            if Nvect > 0:
                v0 /= np.sqrt(len(s))
                v1 /= np.sqrt(len(s))
                vlist = [v0]
                if Nvect > 1:
                    vlist.append(v1)
                # add the positions
                for v in vlist:
                    self.starvecpos.append(s)
                    veclist = []
                    for R in s:
                        for g in self.groupops:
                            if all(abs(R - np.dot(g, s[0])) < threshold):
                                veclist += [np.dot(g, v)]
                                continue
                    self.starvecvec.append(veclist)
        self.generateouter()
        self.Nstarvects = len(self.starvecpos)

    def generateouter(self):
        """
        Generate our outer products for our star-vectors
        """
        self.outer = [sum([np.outer(v, v) for v in veclist]) for veclist in self.starvecvec]