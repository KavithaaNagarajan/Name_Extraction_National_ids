import os
import tempfile
from pdf2image import convert_from_path
import streamlit as st
from PIL import Image
import easyocr
import cv2
import re

# Specify the path to the Poppler 'bin' folder
poppler_path = r"C:\Program Files\poppler-24.08.0\Library\bin"  # Adjust this path for your system

# Define supported image file extensions
image_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff')

def preprocess_image(image_path):
    """
    Preprocess the image for better OCR results.
    """
    # Load the image
    image = cv2.imread(image_path)

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply thresholding to make text clearer
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

    return thresh

def extract_text_with_easyocr(image_path):
    """
    Extract text using EasyOCR from the image.
    """
    # Initialize the EasyOCR Reader (supports multiple languages)
    reader = easyocr.Reader(['en'])

    # Preprocess the image
    image = preprocess_image(image_path)

    # Perform OCR using EasyOCR
    result = reader.readtext(image, detail=0)  # Set detail=0 to return just the text

    # Join the detected text
    extracted_text = "\n".join(result)

    return extracted_text

def parse_mrz_lines_with_criteria(mrz_text):
    """
    Extract lines that start with 'P' and contain one or more '<<' symbols.
    """
    # Split the text into lines
    lines = mrz_text.splitlines()

    # Filter lines that meet the criteria
    filtered_lines = [line for line in lines if line.startswith('P') and '<<' in line]

    return filtered_lines

def process_pdf(file_path, output_folder):
    """
    Convert a PDF to images and save them in the output folder.
    """
    # Convert the PDF to images
    pages = convert_from_path(file_path, dpi=300, poppler_path=poppler_path)

    # Save each page as an image in the output folder
    image_paths = []
    for i, page in enumerate(pages):
        output_image_path = os.path.join(output_folder, f"page_{i+1}.jpg")
        page.save(output_image_path, 'JPEG')
        image_paths.append(output_image_path)

    return image_paths

def split_mrz_line(mrz_line, country_codes):
    """
    This function processes the MRZ line by extracting the document type, country code, given name,
    and the sentence after the country code. It checks if the country code exists in the provided list.
    """
    # Remove any special characters like * and -
    mrz_line = mrz_line.replace("*", "").replace("-", "")

    # Extract the type (first two characters)
    doc_type = mrz_line[:2]

    # Extract the country code (next three characters)
    country_code = mrz_line[2:5]

    # Extract the rest as the given name
    given_name = mrz_line[5:]

    # Find the sentence after the country code
    country_index = mrz_line.find(country_code)
    if country_index != -1:
        sentence_after_country_code = mrz_line[country_index + len(country_code):]
    else:
        sentence_after_country_code = ""

    # Check if the country code exists in the list of valid country codes
    country_exists = country_code in country_codes

    return sentence_after_country_code

def split_surname_given_name(sentence_after_country_code):
    """
    This function splits the sentence after the country code into surname and given name.
    The surname is the part before the first `<` and the given name is everything after it.
    If multiple `<` characters exist, the text between them is considered part of the given name.
    Additionally, any digits (numbers) will be removed from the names.
    """
    # Split the sentence by the first '<'
    parts = sentence_after_country_code.split('<', 1)

    # The part before the first '<' is the surname
    surname = parts[0].strip()

    # Remove any digits from the surname
    surname = re.sub(r'\d', '', surname)

    # The part after the first '<' is the given name (split by '<' and joined with space)
    given_name_part = parts[1].strip() if len(parts) > 1 else ""

    # Remove any digits from the given name part
    given_name_part = re.sub(r'\d', '', given_name_part)

    # Split by '<' to handle individual names separated by '<'
    given_name = ' '.join(given_name_part.split('<')).strip()

    return surname, given_name

# Function to clean and extract names
def extract_name(text, keywords, unwanted_words):
    # Convert the text to lowercase for case insensitivity
    text = text.lower()
    
    # Regular expression to remove unwanted characters (non-alphabetic)
    clean_text = re.sub(r'[^a-z\s]', '', text)
    
    result = {}
    
    # Iterate through the keywords to find names
    for keyword in keywords:
        # Create a regex pattern to capture the name after the keyword
        pattern = r'{}[\s:]*([a-z\s]+)'.format(re.escape(keyword.lower()))
        match = re.search(pattern, clean_text)
        
        if match:
            # Extract the name after the keyword
            name = match.group(1).strip()
            
            # Remove anything that isn't part of the name (numbers, special characters, etc.)
            name = re.sub(r'[^a-z\s]', '', name)
            
            # Limit name extraction to stop if we encounter unwanted words (like 'date', 'number', etc.)
            stop_words = ['date', 'number', 'place', 'village', 'signature', 'code']
            for word in stop_words:
                if word in name:
                    name = name.split(word)[0].strip()
                    break
            
            # Ensure we capture the first part of the name and stop there
            # Only retain the first two words of the name (for first name and surname)
            name_parts = name.split()
            if len(name_parts) > 2:
                name = ' '.join(name_parts[:2])  # Only capture the first two words
            
            # Store the result with the keyword as the key
            result[keyword] = ' '.join(name.split())
    
    # If no valid names are found, return "name not found"
    if not result:
        return "name not found"
    
    # Filtering unwanted words from the result
    filtered_result = {}
    for key, value in result.items():
        # Split the extracted name to check if it contains any unwanted words
        words = value.split()
        filtered_words = [word for word in words if word not in unwanted_words]
        
        # Join the filtered words back into a name
        filtered_name = ' '.join(filtered_words)
        
        # Store the filtered result if the filtered name is not empty
        if filtered_name:
            filtered_result[key] = filtered_name
    
    return filtered_result

# List of valid country codes
country_codes = [
    "AFG", "ALA", "ALB", "DZA", "AND", "AGO", "ATG", "ARG", "ARM", "AUS", "AUT", "AZE",
    "BHS", "BHR", "BGD", "BRB", "BLR", "BEL", "BLZ", "BEN", "BTN", "BOL", "BIH", "BWA",
    "BRA", "BRN", "BGR", "BFA", "BDI", "KHM", "CMR", "CAN", "CPV", "CAF", "TCD", "CHL",
    "CHN", "COL", "COM", "COG", "COD", "CRI", "CIV", "HRV", "CUB", "CYP", "CZE", "DNK",
    "DJI", "DMA", "DOM", "ECU", "EGY", "SLV", "GNQ", "ERI", "EST", "SWZ", "ETH", "FJI",
    "FIN", "FRA", "GAB", "GMB", "GEO", "DEU", "GHA", "GRC", "GRD", "GTM", "GIN", "GNB",
    "GUY", "HTI", "HND", "HUN", "ISL", "IND", "IDN", "IRN", "IRQ", "IRL", "ISR", "ITA",
    "JAM", "JPN", "JOR", "KAZ", "KEN", "KIR", "KWT", "KGZ", "LAO", "LVA", "LBN", "LSO",
    "LBR", "LBY", "LIE", "LTU", "LUX", "MDG", "MWI", "MYS", "MDV", "MLI", "MLT", "MHL",
    "MRT", "MUS", "MEX", "FSM", "MDA", "MCO", "MNG", "MNE", "MAR", "MOZ", "MMR", "NAM",
    "NRU", "NPL", "NLD", "NZL", "NIC", "NER", "NGA", "PRK", "MKD", "NOR", "OMN", "PAK",
    "PLW", "PAN", "PNG", "PRY", "PER", "PHL", "POL", "PRT", "QAT", "ROU", "RUS", "RWA",
    "KNA", "LCA", "VCT", "WSM", "SMR", "STP", "SAU", "SEN", "SRB", "SYC", "SLE", "SGP",
    "SVK", "SVN", "SLB", "SOM", "ZAF", "KOR", "SSD", "ESP", "LKA", "SDN", "SUR", "SWE",
    "CHE", "SYR", "TWN", "TJK", "TZA", "THA", "TLS", "TGO", "TON", "TTO", "TUN", "TUR",
    "TKM", "TUV", "UGA", "UKR", "ARE", "GBR", "USA", "URY", "UZB", "VUT", "VAT", "VEN",
    "VNM", "YEM", "ZMB", "ZWE"
]

# List of keywords to search for
keywords = ['surname', 'first name', 'first names', 'names', 'given names', 'full names', 'full name']

# List of unwanted words
unwanted_words = ['first', 'names', 'surname', 'name', 'full']

def main():
    # Streamlit user interface for uploading files
    st.title("Name Extractor Uploader")
    uploaded_file = st.file_uploader("Choose a file (PDF or Image)", type=['pdf', 'jpg', 'jpeg', 'png', 'bmp', 'gif', 'tiff'])

    if uploaded_file is not None:
        # Get file extension
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()

        # If the uploaded file is an image, apply similar layout as PDF processing
        if file_extension in image_extensions:
            # Create a temporary file for image storage
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
                temp_file.write(uploaded_file.getbuffer())
                temp_file_path = temp_file.name

            # Open the image
            image = Image.open(temp_file_path)
            st.write("Image file uploaded successfully.")

            # Resize the image to a smaller size (similar to PDF page size)
            image_resized = image.resize((300, 300))  # Adjust the size as needed

            # Use columns for better layout of image
            cols = st.columns(1)  # Single column for image
            with cols[0]:
                st.image(image_resized, caption="Uploaded Image", use_container_width=True)

            # Perform OCR and extract MRZ lines
            extracted_text = extract_text_with_easyocr(temp_file_path)
            filtered_lines = parse_mrz_lines_with_criteria(extracted_text)

            # Display the results for the uploaded image
            with st.expander("OCR Results for Uploaded Image"):
                if filtered_lines:
                    st.write("Filtered MRZ Lines:")
                    for line in filtered_lines:
                        st.write(line)

                    # Process the MRZ line and extract surname and given name
                    for line in filtered_lines:
                        sentence_after_country_code = split_mrz_line(line, country_codes)
                        surname, given_name = split_surname_given_name(sentence_after_country_code)
                        st.write(f"Surname: {surname}")
                        st.write(f"Given Name: {given_name}")
                else:
                    st.write("No matching MRZ lines found. Attempting to extract names from text...")
                    # Extract names using keywords and unwanted words
                    name = extract_name(extracted_text, keywords, unwanted_words)
                    if isinstance(name, dict):
                        for key, value in name.items():
                            st.write(f"{key}: {value}")
                    else:
                        st.write(name)

        # If the uploaded file is a PDF, convert it to images and save them
        elif file_extension == '.pdf':
            st.write("Processing PDF... Please wait.")
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_pdf_file:
                temp_pdf_file.write(uploaded_file.getbuffer())
                temp_pdf_file_path = temp_pdf_file.name

            with tempfile.TemporaryDirectory() as temp_output_dir:
                # Convert PDF to images
                image_paths = process_pdf(temp_pdf_file_path, temp_output_dir)
                st.write(f"PDF processed. {len(image_paths)} pages converted to images.")

                # Use columns for better layout of images
                num_columns = 3  # Set the number of columns you want
                cols = st.columns(num_columns)
                
                for i, image_path in enumerate(image_paths):
                    # Open image for displaying in Streamlit
                    page_image = Image.open(image_path)
                    col_idx = i % num_columns
                    with cols[col_idx]:
                        st.image(page_image, caption=f"Page {i+1} of the PDF", use_container_width=True)
                    
                    # Perform OCR and extract MRZ lines
                    extracted_text = extract_text_with_easyocr(image_path)
                    filtered_lines = parse_mrz_lines_with_criteria(extracted_text)

                    # Display the results for each page
                    with st.expander(f"Page {i+1} OCR Results"):
                        if filtered_lines:
                            st.write(f"Filtered MRZ Lines from Page {i+1}:")
                            for line in filtered_lines:
                                st.write(line)

                            # Process the MRZ line and extract surname and given name
                            for line in filtered_lines:
                                sentence_after_country_code = split_mrz_line(line, country_codes)
                                surname, given_name = split_surname_given_name(sentence_after_country_code)
                                st.write(f"Surname: {surname}")
                                st.write(f"Given Name: {given_name}")
                        else:
                            st.write(f"No matching MRZ lines found on Page {i+1}. Attempting to extract names from text...")
                            # Extract names using keywords and unwanted words
                            name = extract_name(extracted_text, keywords, unwanted_words)
                            if isinstance(name, dict):
                                for key, value in name.items():
                                    st.write(f"{key}: {value}")
                            else:
                                st.write(name)

if __name__ == "__main__":
    main()
