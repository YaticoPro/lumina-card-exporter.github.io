from CardImporter import CardImporter, Card, Cost
from ImageCardTransformer import ImageCardTransformer
from PDFImporter import PDFImporter
import argparse

def main():
    parser = argparse.ArgumentParser(
        prog='CardExporter',
        description='Transform the csv list of cards into the visual basic version of cards stored in a PDF file')
    parser.add_argument('-csv-filepath', '--cp', type=str, help="The path of the csv file")
    parser.add_argument('-limit', '--l', type=int, default=None, help="The maximum number of cards to display")
    parser.add_argument('-pdf-filepath', '--pp', type=str, default=None, help="The path of the pdf file to store cards")
    parser.add_argument('-delete-pickle-after-run', '--dp', type=bool, default=True ,help="The path of the csv file")
    parser.add_argument('-delete-images-after-run', '--di', type=bool, default=True ,help="The path of the csv file")

    args = parser.parse_args()

    ci = CardImporter()
    ict = ImageCardTransformer()
    pi = PDFImporter()

    ci.parse(args.cp, limit=args.l)
    ict.transform_cards()

    pdf_filepath = args.pp if args.pp is not None else args.cp.replace(".csv", ".pdf")
    pi.import_from_images_directory(pdf_filepath=pdf_filepath)

    if args.dp:
        ci.delete_pickles()

    if args.di:
        ict.delete_images()

    print("Done ♪")

if __name__ == "__main__":
    main()
