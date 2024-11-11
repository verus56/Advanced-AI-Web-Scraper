import streamlit as st
from selenium.webdriver import Remote, ChromeOptions
from selenium.webdriver.chromium.remote_connection import ChromiumRemoteConnection
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from langchain.prompts import MessagesPlaceholder
from langchain_groq import ChatGroq
from langchain.load import dumps, loads
from langchain_core.prompts import ChatPromptTemplate
import pandas as pd
import time
import re
from concurrent.futures import ThreadPoolExecutor

# Constants
AUTH = ''
SBR_WEBDRIVER = ''
GROQ_API_KEY = ''

# Initialize the LLM model
model = ChatGroq(
    api_key=GROQ_API_KEY,
    model="llama3-8b-8192",
)

def clean_dom_content(html_content):
    """Clean and extract text content from HTML with improved filtering"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove unwanted elements
    unwanted_elements = [
        'script', 'style', 'meta', 'link', 'noscript', 'iframe', 
        'header', 'footer', 'nav', 'aside', 'cookie', 'banner',
        '[class*="cookie"]', '[class*="popup"]', '[class*="modal"]',
        '[class*="overlay"]', '[class*="banner"]', '[class*="notice"]',
        '[id*="cookie"]', '[id*="popup"]', '[id*="modal"]',
        '[class*="advertising"]', '[class*="ad-"]', '[class*="tracker"]',
        '[data-tracking]', '[data-analytics]'
    ]
    
    # Remove elements by tag name and CSS selectors
    for element in unwanted_elements:
        for tag in soup.select(element):
            tag.decompose()
    
    # Additional cleanup of common tracking and cookie elements
    for element in soup.find_all(True):  # Find all elements
        # Remove tracking attributes
        tracking_attrs = ['data-tracking', 'data-analytics', 'data-ga', 
                         'data-gtm', 'data-pixel', 'data-fb']
        for attr in tracking_attrs:
            if element.has_attr(attr):
                del element[attr]
                
        # Remove elements with tracking-related classes
        if element.get('class'):
            classes = ' '.join(element.get('class'))
            if any(term in classes.lower() for term in ['track', 'pixel', 'gtm', 'analytics', 
                                                      'cookie', 'popup', 'modal', 'overlay']):
                element.decompose()
                continue
    
    # Extract useful text content
    text_elements = []
    valid_tags = ['p', 'div', 'span', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 
                  'li', 'td', 'th', 'a', 'article', 'section', 'main']
    
    for element in soup.find_all(valid_tags):
        # Skip if element is hidden
        if element.get('style') and ('display: none' in element['style'] or 
                                   'visibility: hidden' in element['style']):
            continue
            
        # Skip empty elements
        text = element.get_text(strip=True)
        if not text:
            continue
            
        # Skip very short text that might be buttons or labels
        if len(text) < 3:
            continue
            
        # Add structured markers based on element type
        if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            text = f"HEADING: {text}"
        elif element.name == 'a' and element.get('href'):
            # Clean and validate URL
            href = element.get('href')
            if href.startswith('javascript:') or href.startswith('#'):
                continue
            if not href.startswith(('http://', 'https://', '/')):
                continue
            text = f"LINK: {text} (URL: {href})"
        elif element.name in ['td', 'th']:
            text = f"TABLE_CELL: {text}"
            
        # Add the cleaned text
        text_elements.append(text)
    
    # Join elements with proper spacing
    clean_content = '\n'.join(text_elements)
    
    # Clean up whitespace and formatting
    clean_content = re.sub(r'\s+', ' ', clean_content)  # Replace multiple spaces
    clean_content = re.sub(r'\n\s*\n', '\n', clean_content)  # Remove empty lines
    clean_content = re.sub(r'[^\S\n]+', ' ', clean_content)  # Clean up horizontal whitespace
    
    # Split into lines and clean each line
    lines = clean_content.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        if line and len(line) > 3:  # Skip very short lines
            # Remove common noise patterns
            line = re.sub(r'\[.*?\]', '', line)  # Remove square bracket content
            line = re.sub(r'\((?!URL:).*?\)', '', line)  # Remove parentheses except URLs
            line = re.sub(r'^\W+|\W+$', '', line)  # Remove leading/trailing non-word chars
            
            if line:  # Only add non-empty lines
                cleaned_lines.append(line)
    
    # Join cleaned lines
    final_content = '\n'.join(cleaned_lines)
    
    # Remove any remaining noise patterns
    final_content = re.sub(r'(\b\w+\b)\s+\1', r'\1', final_content)  # Remove repeated words
    final_content = re.sub(r'\s*\|\s*', ' | ', final_content)  # Clean up table separators
    
    return final_content

def scrape_website(url):
    """Scrape website content with improved handling and waits"""
    print("Connecting to Scraping Browser...")
    options = ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    # Additional options to block unwanted content
    options.add_argument('--disable-notifications')
    options.add_argument('--disable-geolocation')
    options.add_argument('--disable-plugins')
    options.add_argument('--disable-javascript')  # Optional: disable JS if you don't need it
    
    prefs = {
        'profile.default_content_setting_values': {
            'cookies': 2,  # Block cookies
            'images': 2,   # Block images
            'notifications': 2,  # Block notifications
            'auto_select_certificate': 2,
            'fullscreen': 2,
            'mouselock': 2,
            'mixed_script': 2,
            'media_stream': 2,
            'media_stream_mic': 2,
            'media_stream_camera': 2,
            'protocol_handlers': 2,
            'ppapi_broker': 2,
            'automatic_downloads': 2,
            'midi_sysex': 2,
            'push_messaging': 2,
            'ssl_cert_decisions': 2,
            'metro_switch_to_desktop': 2,
            'protected_media_identifier': 2,
            'app_banner': 2,
            'site_engagement': 2,
            'durable_storage': 2
        }
    }
    options.add_experimental_option('prefs', prefs)

    try:
        sbr_connection = ChromiumRemoteConnection(SBR_WEBDRIVER, "goog", "chrome")
        with Remote(sbr_connection, options=options) as driver:
            try:
                driver.get(url)
                print("Waiting for captcha to solve...")
                solve_res = driver.execute(
                    "executeCdpCommand",
                    {
                        "cmd": "Captcha.waitForSolve",
                        "params": {"detectTimeout": 10000},
                    },
                )
                print("Captcha solve status:", solve_res["value"]["status"])

                # Wait for main content to load
                time.sleep(3)

                # Get the page source
                html = driver.page_source
                
                # Clean and return the content
                return clean_dom_content(html)

            except Exception as e:
                print(f"Error during page load: {str(e)}")
                return None

    except Exception as e:
        print(f"Error connecting to browser: {str(e)}")
        return None

def scrape_website(url):
    """Scrape website content using Selenium with improved error handling"""
    print("Connecting to Scraping Browser...")
    options = ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    try:
        sbr_connection = ChromiumRemoteConnection(SBR_WEBDRIVER, "goog", "chrome")
        with Remote(sbr_connection, options=options) as driver:
            driver.get(url)
            print("Waiting for captcha to solve...")
            solve_res = driver.execute(
                "executeCdpCommand",
                {
                    "cmd": "Captcha.waitForSolve",
                    "params": {"detectTimeout": 10000},
                },
            )
            print("Captcha solve status:", solve_res["value"]["status"])

            # Wait for page to load completely
            time.sleep(3)  # Allow dynamic content to load

            # Get the page source and clean it
            html = driver.page_source
            return clean_dom_content(html)

    except Exception as e:
        print(f"Error during scraping: {str(e)}")
        return None

def parse_with_llm(content, parse_description):
    """Parse content using LLM with improved prompt and response handling"""
    template = """
You are a web scraping assistant. Based on the text content provided and the user's extraction request,
please extract and organize the information in a clean table format.

Content to analyze: {dom_content}

Extraction request: {parse_description}

Rules:
1. Format the output as a SINGLE clean markdown table
2. Use clear, concise column headers
3. Each row must contain related information
4. Remove duplicates and irrelevant information
5. Ensure consistent column alignment
6. Follow this exact format:
   | Header1 | Header2 | Header3 |
   |---------|---------|---------|
   | Data1   | Data2   | Data3   |

Important: 
- Output ONLY the markdown table
- Do not include any explanatory text
- Do not create multiple separate tables
- Ensure all table rows have the same number of columns
- Use proper markdown table syntax with aligned separators
"""

    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | model

    try:
        response = chain.invoke({
            "dom_content": content,
            "parse_description": parse_description
        })

        # Extract just the table content
        result = str(response).strip()
        
        # Clean up the response
        if "content=" in result:
            start = result.find("content=") + len("content=")
            end = result.find("additional_kwargs", start)
            if start != -1 and end != -1:
                table_content = result[start:end].strip().strip('"').replace("\\n", "\n")
                
                # Clean up any remaining quotes or escape characters
                table_content = re.sub(r'[\'"]', '', table_content)
                table_content = re.sub(r'\\+', '', table_content)
                
                # Ensure proper table formatting
                lines = table_content.split('\n')
                cleaned_lines = []
                for line in lines:
                    if '|' in line:
                        # Ensure proper spacing in table cells
                        cells = [cell.strip() for cell in line.split('|')]
                        cleaned_line = '| ' + ' | '.join(cells[1:-1]) + ' |'
                        cleaned_lines.append(cleaned_line)
                
                return '\n'.join(cleaned_lines)
        
        return None
    except Exception as e:
        print(f"Error in LLM parsing: {str(e)}")
        return None

def merge_tables(tables):
    """Merge multiple tables while removing duplicates"""
    if not tables:
        return None
        
    # Split each table into lines
    table_lines = [table.split('\n') for table in tables if table]
    
    # Get headers from first table
    headers = table_lines[0][0]
    separator = table_lines[0][1]
    
    # Collect all unique data rows
    seen_rows = set()
    merged_rows = []
    
    for table in table_lines:
        # Skip headers and separator, process only data rows
        for row in table[2:]:
            if row not in seen_rows and row.strip():
                seen_rows.add(row)
                merged_rows.append(row)
    
    # Combine everything back together
    return '\n'.join([headers, separator] + merged_rows)

def markdown_table_to_df(markdown_table):
    """Convert markdown table to pandas DataFrame with improved error handling"""
    try:
        if not markdown_table or '|' not in markdown_table:
            return None

        # Split the table into lines
        lines = markdown_table.strip().split('\n')
        lines = [line for line in lines if line.strip()]

        if len(lines) < 2:
            return None

        # Extract headers
        headers = [col.strip() for col in lines[0].split('|')[1:-1]]

        # Skip the separator line
        data_lines = lines[2:]

        # Parse data rows
        data = []
        for line in data_lines:
            row = [cell.strip() for cell in line.split('|')[1:-1]]
            if len(row) == len(headers):  # Only include rows that match header count
                data.append(row)

        return pd.DataFrame(data, columns=headers)
    except Exception as e:
        print(f"Error converting to DataFrame: {str(e)}")
        return None

def split_content(content, max_chunk_size=4000):
    """Split content into smaller chunks with improved chunking logic"""
    words = content.split()
    chunks = []
    current_chunk = []
    current_length = 0

    for word in words:
        word_length = len(word)
        if current_length + word_length + 1 > max_chunk_size:
            chunks.append(' '.join(current_chunk))
            current_chunk = [word]
            current_length = word_length
        else:
            current_chunk.append(word)
            current_length += word_length + 1

    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks

def process_chunk(chunk, parse_description):
    """Process a single chunk with the LLM"""
    return parse_with_llm(chunk, parse_description)




# Set page configuration
st.set_page_config(
    page_title="Advanced Web Scraper",
    page_icon="🕷️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS with dark theme optimization
st.markdown("""
    <style>
        /* Main container spacing */
        .main {
            padding: 2rem;
        }
        
        /* Title styling with darker gradient */
        .title-container {
            background: linear-gradient(90deg, #FF4B4B 0%, #8B0000 100%);
            padding: 2rem;
            border-radius: 12px;
            margin-bottom: 2rem;
            text-align: center;
            color: white;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }
        
        /* Input container styling - darker background */
        .input-container {
            background-color: rgba(255, 255, 255, 0.05);
            padding: 2rem;
            border-radius: 12px;
            margin-bottom: 2rem;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        /* Results container styling - darker background */
        .results-container {
            background-color: rgba(255, 255, 255, 0.05);
            padding: 2rem;
            border-radius: 12px;
            margin-top: 2rem;
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }
        
        /* Button styling */
        .stButton > button {
            background: linear-gradient(90deg, #FF4B4B 0%, #FF6B6B 100%);
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 8px;
            font-weight: bold;
            transition: all 0.3s ease;
            width: 100%;
            margin-top: 1.5rem;
        }
        
        .stButton > button:hover {
            background: linear-gradient(90deg, #FF3333 0%, #FF4B4B 100%);
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
            transform: translateY(-2px);
        }
        
        /* Status messages for dark theme */
        .status-message {
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
            font-weight: 500;
        }
        
        .success {
            background-color: rgba(46, 125, 50, 0.2);
            color: #81c784;
            border: 1px solid rgba(129, 199, 132, 0.3);
        }
        
        .error {
            background-color: rgba(198, 40, 40, 0.2);
            color: #ef5350;
            border: 1px solid rgba(239, 83, 80, 0.3);
        }
        
        /* Table styling for dark theme */
        .dataframe {
            width: 100%;
            margin-top: 1rem;
            border-collapse: separate;
            border-spacing: 0;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            overflow: hidden;
        }
        
        .dataframe th {
            background-color: rgba(255, 255, 255, 0.1);
            padding: 1rem;
            font-weight: 600;
            text-align: left;
            border-bottom: 2px solid rgba(255, 255, 255, 0.1);
            color: #FF4B4B;
        }
        
        .dataframe td {
            padding: 0.75rem 1rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            color: rgba(255, 255, 255, 0.9);
        }
        
        .dataframe tr:hover {
            background-color: rgba(255, 255, 255, 0.05);
        }
        
        /* Code block styling */
        .highlight {
            background-color: rgba(255, 255, 255, 0.05) !important;
            border-radius: 8px;
            padding: 1rem;
        }
        
        /* Expander styling */
        .streamlit-expanderHeader {
            background-color: rgba(255, 255, 255, 0.05);
            border-radius: 8px;
        }
        
        /* Metrics styling */
        [data-testid="stMetricValue"] {
            color: #FF4B4B;
        }
        
        /* Headers */
        h1, h2, h3 {
            color: rgba(255, 255, 255, 0.9);
        }
        
        /* Input fields */
        .stTextInput input, .stTextArea textarea {
            background-color: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            color: white;
            border-radius: 8px;
        }
        
        .stTextInput input:focus, .stTextArea textarea:focus {
            border-color: #FF4B4B;
            box-shadow: 0 0 0 1px #FF4B4B;
        }
        
        /* Spinner */
        .stSpinner {
            text-align: center;
            margin: 1rem 0;
        }
        
        /* Loading animation */
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.6; }
            100% { opacity: 1; }
        }
        
        .loading {
            animation: pulse 1.5s infinite;
        }
    </style>
""", unsafe_allow_html=True)

def main():
    # Page title
    st.markdown("""
        <div class="title-container">
            <h1 style='margin-bottom: 0.5rem;'>🕷️ Advanced Web Scraper</h1>
            <p style='font-size: 1.2rem; opacity: 0.9;'>Extract and organize data effortlessly</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Sidebar configuration
    with st.sidebar:
        st.markdown("### ⚙️ Configuration")
        st.markdown("---")
        chunk_size = st.slider(
            "Content Chunk Size",
            min_value=2000,
            max_value=8000,
            value=4000,
            step=500,
            help="Adjust the content chunk size for processing"
        )
        
        st.markdown("### 📊 Statistics")
        stats_col1, stats_col2 = st.columns(2)
        with stats_col1:
            st.metric(label="Processed Pages", value="0")
        with stats_col2:
            st.metric(label="Success Rate", value="100%", delta="↑")
    
    # Main content area
    st.markdown("<div class='input-container'>", unsafe_allow_html=True)
    
    # URL Input and Scrape button
    url_col, button_col = st.columns([3, 1])
    with url_col:
        url = st.text_input(
            "Website URL",
            placeholder="https://example.com",
            help="Enter the URL of the website you want to scrape"
        )
    with button_col:
        scrape_button = st.button('🚀 Scrape', use_container_width=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Handle scraping
    if scrape_button:
        if not url:
            st.markdown("""
                <div class="status-message error">
                    ⚠️ Please enter a valid URL
                </div>
            """, unsafe_allow_html=True)
        else:
            with st.spinner("🔄 Scraping website..."):
                clean_content = scrape_website(url)
                if clean_content:
                    st.session_state.dom_content = clean_content
                    st.markdown("""
                        <div class="status-message success">
                            ✅ Website scraped successfully!
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Results container
                    st.markdown("<div class='results-container'>", unsafe_allow_html=True)
                    st.markdown("### 📄 Scraped Content")
                    with st.expander("View raw content", expanded=False):
                        st.code(clean_content, language="html")
                    st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.markdown("""
                        <div class="status-message error">
                            ❌ Failed to scrape website. Please try again.
                        </div>
                    """, unsafe_allow_html=True)
    
    # Extraction section
    if 'dom_content' in st.session_state:
        st.markdown("<div class='input-container'>", unsafe_allow_html=True)
        st.markdown("### 🎯 Extract Information")
        
        extract_col, extract_button_col = st.columns([3, 1])
        
        with extract_col:
            parse_description = st.text_area(
                "What would you like to extract?",
                placeholder="Example: Extract all product names and prices",
                help="Describe the specific information you want to extract from the website"
            )
        
        with extract_button_col:
            extract_button = st.button('📥 Extract', use_container_width=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        if extract_button:
            if parse_description:
                with st.spinner("🔄 Extracting information..."):
                    content_chunks = split_content(st.session_state.dom_content, chunk_size)
                    
                    with ThreadPoolExecutor(max_workers=3) as executor:
                        futures = [executor.submit(process_chunk, chunk, parse_description) 
                                 for chunk in content_chunks]
                        all_tables = [f.result() for f in futures if f.result()]
                    
                    if all_tables:
                        final_table = merge_tables(all_tables)
                        st.markdown("<div class='results-container'>", unsafe_allow_html=True)
                        st.markdown("### 📋 Extracted Data")
                        st.write(markdown_table_to_df(final_table))
                        st.markdown("</div>", unsafe_allow_html=True)
                    else:
                        st.markdown("""
                            <div class="status-message error">
                                ❌ Extraction failed. Please adjust your description or try again.
                            </div>
                        """, unsafe_allow_html=True)
            else:
                st.markdown("""
                    <div class="status-message error">
                        ⚠️ Please provide an extraction description.
                    </div>
                """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
