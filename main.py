import os

from CardImporter import CardImporter
from GoogleSheetsCSVImporter import GoogleSheetsCSVImporter
from ImageCardTransformer import ImageCardTransformer
from PDFImporter import PDFImporter
import argparse

def main():
    # Args
    parser = argparse.ArgumentParser(
        prog='CardExporter',
        description='Transform the csv list of cards into the visual basic version of cards stored in a PDF file')

    parser.add_argument('-test', '--test', action='store_true', help="To just use for a test csv file, requires a test.csv in the files directory")

    parser.add_argument('-link', '--link', default=None, type=str, help="The link of the csv file")
    parser.add_argument('-csv-filepath', '--cp', type=str, nargs="+", help="The path of the csv file")
    parser.add_argument('-limit', '--l', type=int, default=None, help="The maximum number of cards to display")
    parser.add_argument('-pdf-filepath', '--pp', type=str, default=None, help="The path of the pdf file to store cards")
    parser.add_argument('-delete-pickle-after-run', '--dp', type=bool, default=False ,help="The path of the csv file", action=argparse.BooleanOptionalAction)
    parser.add_argument('-delete-images-after-run', '--di', type=bool, default=False ,help="The path of the csv file", action=argparse.BooleanOptionalAction)
    parser.add_argument('-refresh', '--refresh', type=bool, default=False ,help="Refresh exported csv file")

    args = parser.parse_args()

    # Init
    ci = CardImporter()
    ict = ImageCardTransformer()
    pi = PDFImporter()

    # Reset
    ci.delete_pickles()
    ict.delete_images()

    if args.test:
        defaut_file = "./files/test"
    else:
        defaut_file = "./files/to_export"

    # Apply
    if args.link is not None:
        default_csv_filepath = defaut_file+".csv"
        if not os.path.exists(default_csv_filepath) or args.refresh:
            gsci = GoogleSheetsCSVImporter(args.link)
            default_csv_filepath = gsci.import_csv()
        ci.parse(default_csv_filepath, limit=args.l)
    if args.cp is not None:
        for csv_filepath in args.cp:
            ci.parse(csv_filepath, limit=args.l)
    ict.transform_cards()
    pdf_filepath = args.pp if args.pp is not None else defaut_file+".pdf"
    pi.import_from_images_directory(pdf_filepath=pdf_filepath, example=args.test)

    # After Reset if asked
    if args.dp:
        ci.delete_pickles()

    if args.di:
        ict.delete_images()

    print("Done ♪")

if __name__ == "__main__":
    main()
