#!/usr/bin/env python3

import argparse
import os
import shutil

from ifs_tools.html_tools.utils import HTMLPage
import ifs_tools.QC as qc

def makedir(path, overwrite=True):
    if os.path.isdir(path):
        if overwrite:
            print(f"Overwriting existing directory {path}")
            shutil.rmtree(path, ignore_errors=True)
            os.mkdir(path)
            return True
        else:
            print(f"{path} already exists")
            return False
    else:
        os.mkdir(path)
        return True

def is_html_page(path):
    page = os.path.join(path, "index.html")
    ispage = os.path.isfile(page)
    if ispage:
        return page
    else:
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file_path", metavar="N", type=str, nargs="+",
                        help="Path to file(s)")
    parser.add_argument("--search_in", type=str, help="If selected, will search for all fits file within the given directory",
                        dest="search_in", action=argparse.BooleanOptionalAction,
                        default=False)
    parser.add_argument("--survey", type=str, help="Survey/instrument to be used (default=weave)",
                        dest="survey", required=True)
    parser.add_argument("--qctest", nargs="+", help="QC test function to be applied to the data",
                    dest="qctest", required=True)
    parser.add_argument("--qcmode", type=str, help="QC test level of every qc test: raw, cube, or prod",
                    dest="qcmode", required=True)
    parser.add_argument("--output", nargs=1, help="Output directory to store QC products of all files.",
                    dest="output", default=os.path.join(os.getcwd(), "output"))
    parser.add_argument("--overwrite", action=argparse.BooleanOptionalAction,
                        help="Overwrite output products from previous runs (default is False)",
                        dest="overwrite", default=False)
    parser.add_argument("--html", action=argparse.BooleanOptionalAction,
                    help="Create an HTML file to visualize the results (default=True)",
                    dest="html", default=True)
    print("\n\n\nParsing input arguments")
    args = parser.parse_args()

    if args.search_in:
        if len(args.file_path) != 1:
            raise NotImplementedError("Provide only one directory")
        from glob import glob
        print(f"Searching for files within input directory:\n  {args.file_path[0]}")
        files_found = sorted(
            glob(os.path.join(args.file_path[0], "*.fit*")))
        print(f"Number of files found: {len(files_found)}",
              "\n", '\n '.join(files_found))
        args.file_path = files_found
    n_files = len(args.file_path)
    n_qc_test = len(args.qctest)

    print(f"Number of input files: {n_files}",
          f"\nSurvey: {args.survey}",
          f"\nNumber of QC tests: {n_qc_test}",
          f"\nOutput directory: {args.output}")
    makedir(args.output, overwrite=args.overwrite)

    print(f"Checking survey module: {args.survey}")
    survey_in = hasattr(qc, args.survey)
    if not survey_in:
        raise ImportError("Input survey module not found")
    else:
        survey_module = getattr(qc, args.survey)
        print("Survey module found")
    
    print(f"Checking QC data level: {args.qcmode}")
    data_lvl_module = hasattr(survey_module, f"{args.qcmode}_qc")
    if not data_lvl_module:
        raise ImportError(f"Input QC {args.qcmode} module not found")
    else:
        module = getattr(survey_module, f"{args.qcmode}_qc")
        print(f"QC {args.qcmode} module found")

    # Prepare HTML master page
    if args.html:
        page_path = is_html_page(args.output)
        if page_path is None or args.overwrite:
            print("Initialising master HTML page")
            master_page = HTMLPage(title=f"QC reports")
        else:
            print("Using existing HTML report")
            master_page = HTMLPage(path=page_path)

    # Run the tests
    for i, path in enumerate(args.file_path):
        print(f"\nChecking {args.qcmode} {i+1} out of {len(args.file_path)}\n")
        outdir = os.path.join(args.output, os.path.basename(path + f"_{i}"))
        makedir(outdir, overwrite=args.overwrite)

        qc_tests = module.QC_tests(path, output=outdir,
                                   html=args.html)
        for test in args.qctest:
            print(f"\nApplying **{test}**\n")
            test_method = getattr(qc_tests, test)
            output = test_method()
            print("...Check completed...\n")
        qc_tests.data_container.close_hdul()
        if args.html:
            qc_tests.html_page.save_page(
                os.path.join(outdir, f"index_{args.qcmode}.html"))
            master_page.add_reference(
                os.path.join(os.path.basename(outdir), f"index_{args.qcmode}.html"),
                            qc_tests.html_page.title)
    if args.html:
        master_page.save_page(os.path.join(args.output, "index.html"))

    if len(os.listdir(args.output)) == 0:
        print("No product was made, removing output directory")
        os.rmdir(args.output)

    
