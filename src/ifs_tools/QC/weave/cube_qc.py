#!/usr/bin/env python3

import argparse
import yaml
import os
import shutil

# Basic
from matplotlib import pyplot as plt
from matplotlib.colors import LogNorm

import numpy as np

from astropy.wcs import WCS

# WEAVE
from ifs_tools.data_readers.weave.weave_cube import WEAVECube

file_dir = os.path.dirname(__file__)

def makedir(path, overwrite=True):
    if os.path.isdir(path):
        if overwrite:
            print(f"Overwriting existing directory {path}")
            shutil.rmtree(path, ignore_errors=True)
            os.mkdir(path)
        else:
            pass
    else:
        os.mkdir(path)

class QC_tests(object):
    """
    Class containing tests.
    """
    def __init__(self, path_to_cube, output=None):
        self.output = output
        self.cube = WEAVECube(path_to_cube, load_hdul=True)

    def load_yml_file(self, file_path):
        with open(file_path, 'r') as file:
            content = yaml.safe_load(file)
        return content

    def check_header(self, key_dict, hdul_idx=0):
        info = self.cube.get_from_header(key_dict.keys(),
                                         hdul_idx=hdul_idx)
        for k, v, in info.items():
            okey = True
            if key_dict[k] != "None":
                okey = key_dict[k][0] < v < key_dict[k][1]
            print(f"{k}: {v} -- Okey: {okey}")

    def check_detector(self):
        detector_kw = self.load_yml_file(os.path.join(file_dir, "qc_params", "check_detector.yml"))
        self.check_header(detector_kw)

    def check_observation(self):
        observation_kw = self.load_yml_file(os.path.join(file_dir, "qc_params", "check_observation.yml"))
        self.check_header(observation_kw)
    
    def check_white_image(self, metadata=["CHIPNAME", "CRVAL1", "CRVAL2"]):
        white_image = self.cube.hdul[6].data
        wcs = WCS(self.cube.hdul[6].header)
        
        t = ""
        for key in metadata:
            t += f"{key}: {self.cube.hdul[6].header[key]}" + "\n"
        fig = plt.figure(figsize=(10, 10))
        ax = fig.add_subplot(111, projection=wcs)
        ax.set_title(t)
        mappable = ax.imshow(white_image, cmap='Spectral', norm=LogNorm())
        plt.colorbar(mappable, ax=ax, label=self.cube.hdul[6].header.get(
            'BUNIT', "Unknown BUNIT"))
        fig.savefig(os.path.join(self.output, "white_image.pdf"))
        plt.close(fig)

    def check_pct_spectra(self, percent=[50, 60, 70, 80, 90, 95]):
        median_cube = np.nanmedian(self.cube.hdul[1].data, axis=0)
        median_cube[~np.isfinite(median_cube)] = 0
        # Get the wavelength array
        wcs = WCS(self.cube.hdul[1].header)
        wavelength = wcs.spectral.array_index_to_world_values(
            np.arange(0, self.cube.hdul[1].header['NAXIS3'])
            ) * 1e10  # to AA
        # Rank spaxels
        rank = np.argsort(median_cube.flatten())

        fig, axs = plt.subplots(nrows=len(percent), ncols=1, sharex=True)
        for pct, ax in zip(percent, axs):
            pos = rank[int(pct * rank.size / 100)]
            cube_pos = np.unravel_index(pos, shape=median_cube.shape)
            spectra = self.cube.hdul[1].data[:, cube_pos[0], cube_pos[1]]
            ivar = self.cube.hdul[2].data[:, cube_pos[0], cube_pos[1]]
            ax.fill_between(wavelength, spectra - 1/ivar**0.5,
                            spectra + 1/ivar**0.5, alpha=0.5, color='r')
            ax.plot(wavelength, spectra, lw=0.7, color="k")
            ax.axhline(np.nanmedian(spectra), c='k', alpha=0.3)
            ax.set_ylabel(f"Flux [{pct}]", fontsize=8)
        fig.savefig(os.path.join(self.output, "pct_spectra.pdf"))
        plt.close(fig)
            
        

if __name__ == '__main__':
    # check_detector("/home/pcorchoc/Research/WEAVE-Apertif/weave_fl/supercube_2963103.fit")
    parser = argparse.ArgumentParser()
    parser.add_argument("datacube_path", metavar="N", type=str, nargs="+",
                        help="Path to datacubes")
    parser.add_argument("--qctest", nargs="+", help="QC test function to be applied to the data",
                        dest="qctest")
    parser.add_argument("--output", nargs=1, help="Output directory to store QC products",
                        dest="output", default=os.path.join(os.getcwd(), "output"))
    parser.add_argument("--overwrite", nargs=1, help="Overwrite output products from previous runs (default is True)",
                        dest="overwrite", default=False)
    args = parser.parse_args()

    print(f"Output directory: {args.output}")
    makedir(args.output, overwrite=False)

    for i, path in enumerate(args.datacube_path):
        print(f"\nChecking datacube {i+1} out of {len(args.datacube_path)}\n")
        outdir = os.path.join(args.output, os.path.basename(path + f"_{i}"))
        makedir(outdir, overwrite=args.overwrite)

        qc_tests = QC_tests(path, output=outdir)
        for test in args.qctest:
            print(f"\nApplying **{test}**\n")
            test_method = getattr(qc_tests, test)
            test_method()
            print("...Check completed...\n")
        qc_tests.cube.close_hdul()

    if len(os.listdir(args.output)) == 0:
        print("No product was made, removing output directory")
        os.rmdir(args.output)
