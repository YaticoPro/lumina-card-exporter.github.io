from CardImporter import CardImporter, Card, Cost
from ImageCardTransformer import ImageCardTransformer
from PDFImporter import PDFImporter
import argparse

def main():
    # Args
    parser = argparse.ArgumentParser(
        prog='CardExporter',
        description='Transform the csv list of cards into the visual basic version of cards stored in a PDF file')
    parser.add_argument('-csv-filepath', '--cp', type=str, nargs="+", help="The path of the csv file")
    parser.add_argument('-limit', '--l', type=int, default=None, help="The maximum number of cards to display")
    parser.add_argument('-pdf-filepath', '--pp', type=str, default=None, help="The path of the pdf file to store cards")
    parser.add_argument('-delete-pickle-after-run', '--dp', type=bool, default=True ,help="The path of the csv file")
    parser.add_argument('-delete-images-after-run', '--di', type=bool, default=True ,help="The path of the csv file")

    args = parser.parse_args()

    # Init
    ci = CardImporter()
    ict = ImageCardTransformer()
    pi = PDFImporter()

    # Reset
    ci.delete_pickles()
    ict.delete_images()

    # Apply
    for csv_filepath in args.cp:
        ci.parse(csv_filepath, limit=args.l)
    ict.transform_cards()
    pdf_filepath = args.pp if args.pp is not None else args.cp[0].replace(".csv", ".pdf")
    pi.import_from_images_directory(pdf_filepath=pdf_filepath)

    # After Reset if asked
    if args.dp:
        ci.delete_pickles()

    if args.di:
        ict.delete_images()

    print("Done ♪")

if __name__ == "__main__":
    main()
