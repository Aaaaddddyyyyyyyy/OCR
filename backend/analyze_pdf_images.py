import pymupdf
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

PDF_PATH = Path(r"E:\OCR_Project\test.pdf")

OUTPUT_FILE = Path(
    r"E:\OCR_Project\pdf_image_positions.txt"
)


# ============================================================
# ANALYZE PDF IMAGES
# ============================================================

def analyze_pdf_images():

    if not PDF_PATH.exists():

        print("ERROR: PDF file does not exist:")
        print(PDF_PATH)

        return


    print("=" * 70)
    print("PDF IMAGE POSITION ANALYSIS")
    print("=" * 70)

    print(f"PDF: {PDF_PATH}")

    doc = pymupdf.open(PDF_PATH)

    print(f"Total pages: {len(doc)}")

    print("=" * 70)


    output_lines = []


    for page_index in range(len(doc)):

        page_number = page_index + 1

        page = doc[page_index]

        page_width = page.rect.width
        page_height = page.rect.height

        images = page.get_images(
            full=True
        )

        print()
        print("-" * 70)
        print(
            f"PAGE {page_number} "
            f"({page_width:.2f} x {page_height:.2f})"
        )
        print(
            f"Embedded images: {len(images)}"
        )

        output_lines.append(
            f"PAGE {page_number}"
        )

        output_lines.append(
            f"PAGE_SIZE: "
            f"{page_width:.2f} x {page_height:.2f}"
        )

        output_lines.append(
            f"EMBEDDED_IMAGES: {len(images)}"
        )


        for image_index, image_info in enumerate(
            images,
            start=1
        ):

            xref = image_info[0]

            rects = page.get_image_rects(
                xref
            )

            print()
            print(
                f"Image {image_index}"
            )

            print(
                f"XREF: {xref}"
            )

            print(
                f"Occurrences: {len(rects)}"
            )


            output_lines.append(
                f"IMAGE {image_index}"
            )

            output_lines.append(
                f"XREF: {xref}"
            )

            output_lines.append(
                f"OCCURRENCES: {len(rects)}"
            )


            for occurrence_index, rect in enumerate(
                rects,
                start=1
            ):

                print(
                    f"  Occurrence {occurrence_index}: "
                    f"x0={rect.x0:.2f}, "
                    f"y0={rect.y0:.2f}, "
                    f"x1={rect.x1:.2f}, "
                    f"y1={rect.y1:.2f}, "
                    f"width={rect.width:.2f}, "
                    f"height={rect.height:.2f}"
                )

                output_lines.append(
                    f"  OCCURRENCE {occurrence_index}: "
                    f"x0={rect.x0:.2f}, "
                    f"y0={rect.y0:.2f}, "
                    f"x1={rect.x1:.2f}, "
                    f"y1={rect.y1:.2f}, "
                    f"width={rect.width:.2f}, "
                    f"height={rect.height:.2f}"
                )


        output_lines.append("")


    doc.close()


    # ========================================================
    # SAVE REPORT
    # ========================================================

    OUTPUT_FILE.write_text(
        "\n".join(output_lines),
        encoding="utf-8"
    )


    print()
    print("=" * 70)
    print("ANALYSIS COMPLETED")
    print("=" * 70)

    print(
        f"Report saved to: {OUTPUT_FILE}"
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    analyze_pdf_images()