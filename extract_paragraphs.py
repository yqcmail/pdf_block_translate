import fitz  # PyMuPDF
import os

def extract_paragraphs_from_pdf(pdf_path):
    """
    Extracts paragraphs from a PDF file, merging single-line paragraphs
    based on width and proximity to the next paragraph.

    Args:
        pdf_path (str): The path to the PDF file.

    Returns:
        list: A list of dictionaries, where each dictionary contains:
              'original_text' (str): The original paragraph text.
              'translated_text' (str): The simulated translated text.
              'position' (tuple): The (x0, y0, x1, y1) bounding box of the paragraph.
              'page_num' (int): The page number (0-indexed) where the paragraph is located.
    """
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file '{pdf_path}' not found.")
        return []

    paragraphs_data = []
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"Error opening PDF '{pdf_path}': {e}")
        return []

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        
        # Approximate page content area width (can be refined)
        # For now, using full page width. A margin could be subtracted.
        page_content_width = page.rect.width
        width_threshold = page_content_width * 0.70

        blocks = page.get_text("blocks")
        # Sort blocks by vertical position, then horizontal.
        # This helps in correctly identifying consecutive blocks.
        blocks.sort(key=lambda b: (b[1], b[0])) 

        i = 0
        while i < len(blocks):
            current_block = blocks[i]
            x0, y0, x1, y1, text_content, _, _ = current_block
            block_width = x1 - x0
            
            # Normalize text: replace multiple spaces/newlines with single space, strip leading/trailing whitespace
            cleaned_text = ' '.join(text_content.strip().split()) 
            
            # Check if it's a single-line paragraph
            # A simple check: count newlines. More robust might be to check block height vs font size.
            is_single_line = cleaned_text.count('\n') == 0

            merged = False
            if is_single_line and block_width < width_threshold and (i + 1) < len(blocks):
                next_block = blocks[i+1]
                nx0, ny0, nx1, ny1, ntext_content, _, _ = next_block
                
                # Merge condition: next block starts on the same or very close next line
                # and is reasonably aligned horizontally (e.g. not too far indented or outdented)
                # This vertical threshold might need adjustment based on typical line spacing.
                vertical_threshold = 15 # Points, assuming typical line spacing
                
                if abs(ny0 - y0) < vertical_threshold or (ny0 > y1 and ny0 - y1 < vertical_threshold) : # Same line or close next line
                    # Further check: ensure next block isn't a completely different style/indentation
                    # For now, we'll merge if it's close vertically.
                    cleaned_ntext = ' '.join(ntext_content.strip().split())
                    cleaned_text += " " + cleaned_ntext
                    
                    # Update bounding box to encompass both merged blocks
                    x0 = min(x0, nx0)
                    y0 = min(y0, ny0) # Though for top-left, current y0 is usually fine
                    x1 = max(x1, nx1)
                    y1 = max(y1, ny1) # Update bottom y for the merged block
                    
                    i += 1 # Skip the next block as it's merged
                    merged = True
            
            if cleaned_text: # Ensure there's text to add
                paragraphs_data.append({
                    'original_text': cleaned_text, # Renamed from 'text'
                    'position': (x0, y0, x1, y1),
                    'page_num': page_num  # Store page number
                })
            i += 1
            
    # --- Placeholder for Translation Step ---
    # This part now also carries forward the page_num
    processed_paragraphs = []
    for p_data in paragraphs_data:
        original_text = p_data['original_text']
        
        # Simulate translation - Placeholder for Google AI Studio API call
        # Actual API call would look something like:
        # translated_text = google_ai_studio_translate(
        #     text_to_translate=original_text,
        #     source_language="en",
        #     target_language="zh-CN"
        # )
        # For now, we simulate by appending a suffix.
        simulated_translated_text = original_text + "_[zh-CN translated]"
        
        processed_paragraphs.append({
            'original_text': original_text,
            'translated_text': simulated_translated_text,
            'position': p_data['position'],
            'page_num': p_data['page_num'] # Carry page_num through
        })
            
    return processed_paragraphs

def add_annotations_to_pdf_in_memory(doc, processed_paragraphs_data):
    """
    Adds text annotations to a PDF document in memory based on processed paragraph data.

    Args:
        doc (fitz.Document): The PyMuPDF document object (opened PDF).
        processed_paragraphs_data (list): A list of dictionaries, each containing
                                          'translated_text', 'position', and 'page_num'.
    """
    print("\nAdding annotations to PDF in memory...")
    for i, p_data in enumerate(processed_paragraphs_data):
        page_num = p_data['page_num']
        position = p_data['position']
        translated_text = p_data['translated_text']

        try:
            page = doc.load_page(page_num) # doc[page_num] is equivalent
            annot_point = fitz.Point(position[0], position[1]) # Top-left corner
            
            # Add a "sticky note" style text annotation
            page.add_text_annot(annot_point, translated_text)
            
            if i < 3: # Print confirmation for the first 3 annotations
                print(f"  Added annotation on page {page_num + 1} at ({position[0]:.2f}, {position[1]:.2f}) for: \"{translated_text[:50]}...\"")
        except Exception as e:
            print(f"Error adding annotation for paragraph on page {page_num + 1}: {e}")
    
    print("Finished adding annotations to the document in memory.")


if __name__ == "__main__":
    pdf_file = "test_pdf.pdf"
    
    # Step 1: Extract and process paragraphs (now includes page_num)
    processed_paragraphs_data = extract_paragraphs_from_pdf(pdf_file)

    print(f"Total paragraphs processed (with simulated translation): {len(processed_paragraphs_data)}\n")

    print("Sample of processed paragraphs (first 3):")
    for i, p_data in enumerate(processed_paragraphs_data[:3]):
        print(f"Paragraph {i+1}:")
        print(f"  Page: {p_data['page_num'] + 1}") # Display 1-indexed page number
        print(f"  Position: {p_data['position']}")
        print(f"  Original Text: \"{p_data['original_text']}\"")
        print(f"  Translated Text (Simulated): \"{p_data['translated_text']}\"\n")

    # Step 2: Add annotations to the PDF in memory
    if processed_paragraphs_data:
        try:
            # Re-open the PDF document for annotation. 
            # The 'doc' from extract_paragraphs_from_pdf is closed within that function.
            doc_for_annotation = fitz.open(pdf_file)
            add_annotations_to_pdf_in_memory(doc_for_annotation, processed_paragraphs_data)
            
            # Step 3: Save the document with annotations to a new file
            output_pdf_path = "test_pdf_translated.pdf"
            doc_for_annotation.save(output_pdf_path, garbage=4, deflate=True)
            print(f"\nTranslated PDF with annotations saved to {output_pdf_path}")
            
            doc_for_annotation.close() # Close the document after saving

        except Exception as e:
            print(f"Error during PDF annotation or saving process: {e}")

    # Example of how to access a specific paragraph's data (including page_num)
    # if processed_paragraphs_data:
    #     first_paragraph_original = processed_paragraphs_data[0]['original_text']
    #     first_paragraph_translated = processed_paragraphs_data[0]['translated_text']
    #     first_paragraph_position = processed_paragraphs_data[0]['position']
    #     first_paragraph_page_num = processed_paragraphs_data[0]['page_num']
    #     print(f"\nAccessing first paragraph directly:")
    #     print(f"Original Text: {first_paragraph_original}")
    #     print(f"Translated Text: {first_paragraph_translated}")
    #     print(f"Position: {first_paragraph_position}")
    #     print(f"Page Number: {first_paragraph_page_num + 1}") # 1-indexed for display

