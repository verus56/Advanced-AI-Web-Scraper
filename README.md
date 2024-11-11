# 🕷️ Advanced AI Web Scraper

An intelligent web scraping application built with Streamlit that combines automated web scraping with AI-powered data extraction. The application uses Selenium for web scraping, Groq LLM for intelligent data parsing, and presents a user-friendly interface for extracting structured data from websites.
You can test it here: [Demo Link](https://web-scraper1924.streamlit.app/)

## 🌟 Features

- **Intelligent Scraping**: Automatically handles CAPTCHAs and dynamic content
- **AI-Powered Extraction**: Uses Groq LLM to intelligently parse and structure data
- **Clean Interface**: Modern, responsive UI with dark theme optimization
- **Parallel Processing**: Handles large content through parallel chunk processing
- **Smart Content Cleaning**: Removes tracking elements, ads, and unwanted content
- **Structured Output**: Presents data in clean, organized tables

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- A Groq API key
- A Bright Data Scraping Browser account

### Environment Variables

Create a `.env` file in your project root and add:

```env
AUTH=your-bright-data-auth
GROQ_API_KEY=your-groq-api-key
```

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/advanced-web-scraper.git
cd advanced-web-scraper
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

### Required Packages

```txt
streamlit
selenium
beautifulsoup4
langchain
langchain-groq
pandas
concurrent.futures
```

## 💻 Usage

1. Start the application:
```bash
streamlit run app.py
```

2. Enter a website URL in the input field
3. Click "Scrape" to fetch the website content
4. Describe what data you want to extract
5. Click "Extract" to get structured data

## ⚙️ Configuration

The application provides several configurable parameters:

- **Content Chunk Size**: Adjust the size of content chunks for processing (2000-8000 characters)
- **Parallel Processing**: Controls the number of concurrent extraction processes
- **Browser Options**: Configurable through Selenium options

## 🔒 Security Features

- Automatic CAPTCHA handling
- Cookie and tracking prevention
- JavaScript blocking options
- Secure API key handling

## 🎨 UI Features

- Dark theme optimization
- Responsive design
- Progress indicators
- Expandable content sections
- Error handling with visual feedback
- Interactive data tables
![AIweb](https://github.com/verus56/Advanced-AI-Web-Scraper/blob/main/web11.png)
![AIweb2](https://github.com/verus56/Advanced-AI-Web-Scraper/blob/main/web2.png)

## 🛠️ Advanced Features

### Content Cleaning
- Removes tracking elements
- Filters unwanted content
- Preserves semantic structure
- Handles dynamic content

### Data Processing
- Parallel chunk processing
- Intelligent merging
- Duplicate removal
- Table structure preservation

## 📝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Acknowledgments

- [Streamlit](https://streamlit.io/) for the web framework
- [Groq](https://groq.com/) for LLM capabilities
- [Bright Data](https://brightdata.com/) for scraping infrastructure
- [Selenium](https://www.selenium.dev/) for web automation
- [LangChain](https://langchain.org/) for LLM integration

## ⚠️ Disclaimer

This tool is intended for legal web scraping activities. Always check and comply with the target website's robots.txt and terms of service before scraping.

