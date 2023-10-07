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
from ifs_tools.data_readers.weave.weave_raw import WEAVERaw
from ifs_tools.html_tools.utils import HTMLPage

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

class QC_tests(QCtestBase):
    """
    Class containing tests.
    """
    def __init__(self, path_to_raw, output=None):
        self.data_container = WEAVERaw(path_to_raw, load_hdul=True)
        super().__init__(data_level="raw",
                         name=self.data_container.hdul.filename(),
                         survey="weave")
        self.output = output

    def check_primary(self):
        detector_kw = self.load_yml_file(os.path.join(file_dir, "qc_params", "check_raw.yml"))
        checks = self.check_header(detector_kw)
        if self.html:
            self.html_page.add_table_section(title="Primary Header checks",
                                             data=checks)
    
    def check_raw(self):
        fig, axs = plt.subplots(nrows=2, ncols=1,
                                figsize=(10, 20),
                                gridspec_kw=dict(wspace=0.35))
        fig.suptitle(f'{self.data_container.hdul.filename()}',
                     fontsize=14, fontweight='bold')
        for ax, hdul_index in zip(axs, [1, 2]):
            data = self.data_container.hdul[hdul_index].data
            mappable = ax.imshow(data, cmap='Spectral', norm=LogNorm(),
                                 origin='lower')

            column_index = data.shape[1] // 2
            random_column = np.random.randint(data.shape[1])

            row_index = data.shape[0] // 2
            random_raw = np.random.randint(data.shape[0])

            ax.axhline(row_index, color='k', ls='--', lw=2)
            ax.axvline(column_index, color='k', ls='--', lw=2)

            ax.axhline(random_raw, color='b', ls='--', lw=2)
            ax.axvline(random_column, color='b', ls='--', lw=2)

            inax = ax.inset_axes((1.05, 0, 0.15, 1))
            inax.plot(data[:, column_index], np.arange(data[:, column_index].size),
                      c='k', lw=0.7)
            inax.set_ylim(ax.get_ylim())
            inax.set_yticklabels([])  

            inax = ax.inset_axes((1.25, 0, 0.15, 1))
            inax.plot(data[:, random_column],
                       np.arange(data[:, column_index].size),
                       c='b', lw=0.7)
            inax.set_ylim(ax.get_ylim())
            inax.set_yticklabels([])  

            inax = ax.inset_axes((0, 1.05, 1, 0.15))
            inax.plot(data[row_index, :], c='k', lw=0.7)
            inax.set_xlim(ax.get_ylim())
            inax.set_xticklabels([])

            inax = ax.inset_axes((0, 1.25, 1, 0.15))
            inax.plot(data[random_raw, :], c='b', lw=0.7)
            inax.set_xlim(ax.get_ylim())
            inax.set_xticklabels([])

            plt.colorbar(mappable, ax=ax, label=self.data_container.hdul[1].header.get(
            'BUNIT', "Unknown BUNIT"), location='left')
        output = os.path.join(self.output, "raw_image.png")
        fig.savefig(output,
                    bbox_inches='tight')
        plt.close(fig)
        if self.html:
            self.html_page.add_plot_section("Raw display", output)
        return output

    def check_histogram(self):
        nsigma = 3
        fig, axs = plt.subplots(nrows=2, ncols=2,
                                figsize=(15, 10))
        for ax_pair, hdul_index in zip(axs, [1, 2]):
            data = self.data_container.hdul[hdul_index].data
            ax = ax_pair[0]
            h, xedges, _ = ax.hist(
                data.flatten(), bins='auto',
                range=[-1000, 70000], log=True)
            ax.set_xlabel("Counts/ADU")
            
            xbins = (xedges[:-1] + xedges[1:]) / 2
            norm = np.sum(h)
            mean = np.sum(h * xbins) / norm
            sigma = np.sqrt(np.sum(h * (xbins - mean)**2) / norm)

            inax = ax_pair[1]
            inax.set_title(f"mean={mean:.1f} +- {nsigma}*{sigma:.1f}")
            inax.step(xbins, h)
            inax.set_xlim(mean - 5 * sigma, mean + 5 * sigma)
            inax.set_xlabel("Counts/ADU")
            inax.set_yscale('log')
        output = os.path.join(self.output, "raw_hist.png")
        fig.savefig(output, bbox_inches='tight')
        plt.close(fig)
        if self.html:
            self.html_page.add_plot_section("Raw histogram", output)
        return output
        
            
        

if __name__ == '__main__':
    # check_detector("/home/pcorchoc/Research/WEAVE-Apertif/weave_fl/supercube_2963103.fit")
    parser = argparse.ArgumentParser()
    parser.add_argument("raw_path", metavar="N", type=str, nargs="+",
                        help="Path to raws")
    parser.add_argument("--qctest", nargs="+", help="QC test function to be applied to the data",
                        dest="qctest")
    parser.add_argument("--output", nargs=1, help="Output directory to store QC products",
                        dest="output", default=os.path.join(os.getcwd(), "output"))
    parser.add_argument("--overwrite", nargs=1, help="Overwrite output products from previous runs (default is True)",
                        dest="overwrite", default=False)
    parser.add_argument("--html", action=argparse.BooleanOptionalAction,
                        help="Creates an HTML file to visualize the results",
                        dest="html", default=False)
    args = parser.parse_args()

    print(f"Output directory: {args.output}")
    makedir(args.output, overwrite=False)
    if args.html:
        master_page = HTMLPage(title='QC WEAVE RAW')

    for i, path in enumerate(args.raw_path):
        print(f"\nChecking raw {i+1} out of {len(args.raw_path)}\n")
        outdir = os.path.join(args.output, os.path.basename(path + f"_{i}"))
        makedir(outdir, overwrite=args.overwrite)

        qc_tests = QC_tests(path, output=outdir)
        if args.html:
            qc_page = HTMLPage(os.path.basename(outdir))
        for test in args.qctest:
            print(f"\nApplying **{test}**\n")
            test_method = getattr(qc_tests, test)
            output = test_method()
            if args.html:
                qc_page.add_plot_section(test, output)
            print("...Check completed...\n")
        qc_tests.raw.close_hdul()
        if args.html:
            qc_page.save_page(os.path.join(outdir, "index.html"))
            master_page.add_reference(os.path.join(outdir, "index.html"),
                                      qc_page.title)
    if args.html:
        master_page.save_page(os.path.join(args.output, "index.html"))

    if len(os.listdir(args.output)) == 0:
        print("No product was made, removing output directory")
        os.rmdir(args.output)
