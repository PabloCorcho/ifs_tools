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
from ifs_tools.QC.QCtestBase import QCtestBase
from ifs_tools.data_readers.weave.weave_cube import WEAVECube

file_dir = os.path.dirname(__file__)

class QC_tests(QCtestBase):
    """
    Class containing tests.
    """
    def __init__(self, path_to_cube, output=None, **kwargs):
        self.data_container = WEAVECube(path_to_cube, load_hdul=True)
        super().__init__(data_level="cube",
                         name=self.data_container.hdul.filename(),
                         survey="weave",
                         **kwargs)
        self.output = output
        

    def load_yml_file(self, file_path):
        with open(file_path, 'r') as file:
            content = yaml.safe_load(file)
        return content

    def check_detector(self):
        detector_kw = self.load_yml_file(os.path.join(file_dir, "qc_params", "check_detector.yml"))
        checks = self.check_header(detector_kw)
        if self.html:
            self.html_page.add_table_section(title="Detector checks",
                                             data=checks)

    def check_observation(self):
        observation_kw = self.load_yml_file(os.path.join(file_dir, "qc_params", "check_observation.yml"))
        checks = self.check_header(observation_kw)
        if self.html:
            self.html_page.add_table_section(title="Observation checks",
                                             data=checks)
    
    def check_white_image(self, metadata=["CHIPNAME", "CRVAL1", "CRVAL2"]):
        white_image = self.data_container.hdul[6].data
        wcs = WCS(self.data_container.hdul[6].header)
        
        t = ""
        for key in metadata:
            t += f"{key}: {self.data_container.hdul[6].header[key]}" + "\n"
        fig = plt.figure(figsize=(10, 10))
        ax = fig.add_subplot(111, projection=wcs.celestial)
        ax.set_title(t)
        mappable = ax.imshow(white_image, cmap='Spectral', norm=LogNorm())
        plt.colorbar(mappable, ax=ax, label=self.data_container.hdul[6].header.get(
            'BUNIT', "Unknown BUNIT"))
        output = os.path.join(self.output, "white_image.png")
        fig.savefig(output)
        plt.close(fig)
        if self.html:
            self.html_page.add_plot_section("White image", output)
        return output


    def check_pct_spectra(self, percent=[50, 60, 70, 80, 90, 95]):
        median_cube = np.nanmedian(self.data_container.hdul[1].data, axis=0)
        median_cube[~np.isfinite(median_cube)] = 0
        # Get the wavelength array
        wcs = WCS(self.data_container.hdul[1].header)
        wavelength = wcs.spectral.array_index_to_world_values(
            np.arange(0, self.data_container.hdul[1].header['NAXIS3'])
            ) * 1e10  # to AA
        # Rank spaxels
        rank = np.argsort(median_cube.flatten())

        fig, axs = plt.subplots(nrows=len(percent), ncols=1, sharex=True,
                                figsize=(12, 3 * len(percent)))
        for pct, ax in zip(percent, axs):
            pos = rank[int(pct * rank.size / 100)]
            cube_pos = np.unravel_index(pos, shape=median_cube.shape)
            spectra = self.data_container.hdul[1].data[:, cube_pos[0], cube_pos[1]]
            ivar = self.data_container.hdul[2].data[:, cube_pos[0], cube_pos[1]]
            ax.fill_between(wavelength, spectra - 1/ivar**0.5,
                            spectra + 1/ivar**0.5, alpha=0.5, color='r')
            ax.plot(wavelength, spectra, lw=0.7, color="k")
            ax.axhline(np.nanmedian(spectra), c='k', alpha=0.3)
            ax.set_ylabel(f"Flux [{pct}]", fontsize=8)
            ax.annotate(f"Rank: {pct}", xy=(0.05, 0.95), xycoords='axes fraction',
                        va='top', ha='left')
        output = os.path.join(self.output, "pct_spectra.png")
        fig.savefig(output)
        plt.close(fig)
        if self.html:
            self.html_page.add_plot_section("Ranked spectra", output)
        return output

