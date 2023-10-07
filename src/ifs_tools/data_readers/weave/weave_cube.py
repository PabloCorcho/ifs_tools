#! python3

"""
This module provides the basic utilities to manipulate WEAVE LIFU datacubes.
"""

from astropy.io import fits

class WEAVECube(object):
    def __init__(self, path_to_cube, load_hdul=True):
        self.path = path_to_cube
        self.verbose(f"Cube path: {self.path}")
        if load_hdul:
            self.load_hdul()

    def verbose(self, mssg, lvl='INFO'):
        print(f"[{lvl}] {mssg}")

    def load_hdul(self):
        self.verbose("Loading HDUL")
        self.hdul = fits.open(self.path)

    def get_from_header(self, list_of_kw, hdul_idx=0):
        results = {}
        for kw in list_of_kw:
            results[kw] = self.hdul[hdul_idx].header.get(kw, None)
        return results

    def close_hdul(self):
        self.verbose("Closing HDUL")
        self.hdul.close()

if __name__ == "__main__":
    cube = WEAVECube("/home/pcorchoc/Research/WEAVE-Apertif/weave_fl/supercube_2963103.fit")

    print(cube.get_from_header(['DETECTOR', 'CCDTEMP']))