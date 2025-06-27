# VCF Contact Translator

A Python script to translate contact names in VCF files from English to Bengali. It uses multiple translation APIs for reliability and caches translations to avoid redundant API calls.

## Features

- Translates contact names in VCF files from English to Bengali.
- Uses multiple free translation APIs (Google Translate, MyMemory, LibreTranslate) with fallbacks.
- Caches translations to speed up subsequent runs and reduce API calls.
- Handles VCF files with different formatting for name fields (`N:` and `FN:`).
- Preserves emojis in contact names.

## Files

- `main.py`: The main Python script for translating VCF files.
- `contacts.vcf`: An example input VCF file.
- `translated_contacts.vcf`: The default output file for translated contacts.

## Requirements

- Python 3.7+
- `requests` library

## Installation

1.  **Clone the repository or download the `main.py` file.**

2.  **Install the required packages:**

    ```bash
    pip install requests
    ```

## Usage

1.  **Place your VCF file** (e.g., `contacts.vcf`) in the same directory as the script.

2.  **Run the script:**

    ```bash
    python main.py
    ```

3.  **Follow the prompts:**
    -   Enter the path to your VCF file (or press Enter to use the default `contacts.vcf`).
    -   Enter the desired output file path (or press Enter to use the default `translated_contacts.vcf`).

4.  The script will process the file and save the translated version to the specified output file.

## How It Works

1.  The script reads the input VCF file line by line.
2.  For each line containing a contact name (`N:` or `FN:`), it extracts the name.
3.  It checks if the name is in English and likely to be a person's name.
4.  If so, it translates the name to Bengali using a series of translation APIs.
5.  The translated name is then written to the output VCF file, with proper UTF-8 encoding.
6.  A `translation_cache.json` file is created to store translations, so that the same name is not translated multiple times.
