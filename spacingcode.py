import fitz  # PyMuPDF

def get_line_heights_and_spaces(file_path):
    doc = fitz.open(file_path)
    line_info = []

    for page_num in range(doc.page_count):
        page = doc[page_num]
        prev_line_y = 0

        for block in page.get_text("blocks"):
            for line in block[4]:
                text = line[4]
                line_y0, line_y1 = line[1], line[3]
                line_height = line_y1 - line_y0

                # Calculate space between lines based on Y coordinates
                space = line_y0 - prev_line_y if prev_line_y != 0 else 0
                line_info.append((text, line_height, space))

                prev_line_y = line_y1

    return line_info

if __name__ == "__main__":
    # Replace 'your_document.pdf' with the actual path to your PDF document
    document_path = 'Computer_and_Health_docx.pdf'

    # Get line heights and spaces
    line_info = get_line_heights_and_spaces(document_path)

    # Print the line heights and spaces
    for text, height, space in line_info:
        print(f"Line: '{text}', Height: {height} pt, Space: {space} pt")
