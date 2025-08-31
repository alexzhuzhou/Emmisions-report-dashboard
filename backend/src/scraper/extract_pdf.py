import fitz  # PyMuPDF
import os
from .utils.strings import normalize_text

def extract_pdf_content(pdf_path: str, output_dir: str) -> str:
    """
    Extracts text (with page breaks) and images from a PDF file.
    Saves text as a .txt file and images in a subfolder.
    Returns the path to the text file.
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        pdf_basename = os.path.basename(pdf_path)
        text_filename = os.path.splitext(pdf_basename)[0] + ".txt"
        text_output_path = os.path.join(output_dir, text_filename)
        images_output_dir = os.path.join(output_dir, "images")
        os.makedirs(images_output_dir, exist_ok=True)

        full_text = ""
        image_count = 0

        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            # --- Text Extraction ---
            page_text = page.get_text("text")
            page_text = normalize_text(page_text)
            full_text += page_text
            full_text += f"\n--- Page {page_num + 1} End ---\n"
            # --- Image Extraction (optional) ---
            for img_index, img_info in enumerate(page.get_images(full=True)):
                xref = img_info[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                image_filename = f"page{page_num + 1}_img{img_index + 1}.{image_ext}"
                image_output_path = os.path.join(images_output_dir, image_filename)
                with open(image_output_path, "wb") as img_file:
                    img_file.write(image_bytes)
                image_count += 1

        with open(text_output_path, "w", encoding="utf-8") as text_file:
            text_file.write(full_text.strip())

        doc.close()
        print(f"Extracted text saved to: {text_output_path}")
        print(f"Extracted {image_count} images saved to: {images_output_dir}")
        return text_output_path
    except Exception as e:
        return os.path.join(output_dir, "EXTRACTION_FAILED.txt")
    
# Example usage:
if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python extract_pdf_content.py <path_to_pdf>")
        sys.exit(1)
    pdf_path = sys.argv[1]
    output_dir = os.path.splitext(pdf_path)[0] + "_extracted"
    extract_pdf_content(pdf_path, output_dir)