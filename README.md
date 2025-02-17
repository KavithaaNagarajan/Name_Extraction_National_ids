## Name Extractor Uploader

This project is a Streamlit application that allows users to upload PDF or image files for the purpose of extracting and processing text, specifically focusing on extracting names and MRZ (Machine Readable Zone) lines from documents. The application uses OCR (Optical Character Recognition) with EasyOCR to extract text, processes the extracted text for names, and outputs relevant information such as surname and given name. It also filters MRZ lines to provide document-related details.


### Key Features:

PDF and Image Upload Support:

Supports uploading PDF, JPG, JPEG, PNG, BMP, GIF, and TIFF image files.

The uploaded files are processed using OCR to extract relevant text.

## OCR with EasyOCR:

Uses EasyOCR to extract text from both images and PDF pages.

The application processes text for names and MRZ information.

## MRZ Filtering:

Filters lines starting with 'P' and containing '<<' symbols, which are commonly found in Machine Readable Zones (MRZs) of identity documents like passports.

Extracts surname and given name based on MRZ lines.

## Name Extraction:

Utilizes custom keywords like "surname", "given name", "first name", and others to extract relevant names from the OCR results.

The application also filters unwanted words and provides the first two words of the name (first name and surname).

## PDF Conversion:

Converts PDF files into images for easier OCR processing using the pdf2image library.

Displays all pages of the PDF as images with OCR results.

## Streamlit Interface:

A simple and user-friendly web interface powered by Streamlit, which allows users to upload files and view results directly on the browser.

Requirements:

Python 3.x

Streamlit

easyocr

pdf2image

opencv-python

Pillow

re (Regular Expressions)

poppler-utils (for PDF-to-image conversion)

## Installation:

To install the necessary libraries, you can use pip:


pip install streamlit easyocr pdf2image opencv-python Pillow

Make sure that Poppler is installed on your system. You can download Poppler from here.

On Windows, you may need to set the Poppler path explicitly. For example:


poppler_path = r"C:\Program Files\poppler-24.08.0\Library\bin"

## How to Use:

Launch the Streamlit App:

Run the following command in your terminal to start the Streamlit app:

streamlit run app.py

## Upload a File:

The app allows you to upload either a PDF or an image file. Click on the "Choose a file" button to upload your file.

View OCR Results:

Once the file is uploaded, the app will process the file and extract any relevant text.

The extracted MRZ lines (if any) will be displayed.

Names such as the surname and given name will be extracted and shown in the output section.

## Filtered Results:

If MRZ lines are found, they are filtered, and surname and given name are extracted.

If no MRZ lines are found, the app will attempt to extract names based on predefined keywords like "surname" and "given name".

## Functions Breakdown:

preprocess_image(image_path):

Converts the image to grayscale and applies thresholding to enhance text visibility for OCR.

extract_text_with_easyocr(image_path):

Uses EasyOCR to extract text from the image after preprocessing.

parse_mrz_lines_with_criteria(mrz_text):

Filters MRZ lines based on the presence of 'P' and '<<' symbols.

process_pdf(file_path, output_folder):

Converts a PDF file into images and stores them in a specified folder.

split_mrz_line(mrz_line, country_codes):

Processes MRZ lines to extract information such as document type, country code, and names.

split_surname_given_name(sentence_after_country_code):

Splits the sentence after the country code to extract surname and given name.

extract_name(text, keywords, unwanted_words):

Uses regular expressions to extract names from text based on specified keywords and removes unwanted words.

## Sample Output:
For images or PDFs containing MRZ lines, the app will display the filtered MRZ lines and extract the surname and given name.
If no MRZ lines are found, the app will search for names in the extracted text and display the results.
![image](https://github.com/user-attachments/assets/45f8e183-98da-402b-93ee-6f8fc5f916e8)
![image](https://github.com/user-attachments/assets/5545d426-90b0-4924-98b8-9a6a92ce02c0)
![image](https://github.com/user-attachments/assets/75a86337-7bce-445e-a202-9e23301b6def)


