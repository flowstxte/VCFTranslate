import re
import requests
import json
import time
from typing import Optional

class VCFTranslator:
    def __init__(self):
        # Cache to avoid translating the same name multiple times
        self.translation_cache = {}
        self.request_delay = 1  # Delay between API requests to avoid rate limiting
        
    def is_bengali_text(self, text):
        """Check if text contains Bengali characters"""
        bengali_pattern = re.compile(r'[\u0980-\u09FF]')
        return bool(bengali_pattern.search(text))
    
    def is_english_text(self, text):
        """Check if text is primarily English"""
        # Remove emojis and special characters for checking
        clean_text = re.sub(r'[^\w\s]', '', text)
        if not clean_text.strip():
            return False
        
        # Check if it's mostly ASCII letters
        ascii_letters = sum(1 for c in clean_text if c.isascii() and c.isalpha())
        total_letters = sum(1 for c in clean_text if c.isalpha())
        
        if total_letters == 0:
            return False
        
        return (ascii_letters / total_letters) > 0.8
    
    def extract_emojis(self, text):
        """Extract emojis from text"""
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]+",
            flags=re.UNICODE
        )
        return emoji_pattern.findall(text)
    
    def remove_emojis(self, text):
        """Remove emojis from text"""
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]+",
            flags=re.UNICODE
        )
        return emoji_pattern.sub('', text)
    
    def translate_with_mymemory(self, text: str) -> Optional[str]:
        """Translate text using MyMemory API (free service)"""
        try:
            url = "https://api.mymemory.translated.net/get"
            params = {
                'q': text,
                'langpair': 'en|bn'  # English to Bengali
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data['responseStatus'] == 200:
                    return data['responseData']['translatedText']
            return None
        except Exception as e:
            print(f"MyMemory translation error: {e}")
            return None
    
    def translate_with_libretranslate(self, text: str) -> Optional[str]:
        """Translate text using LibreTranslate API (free service)"""
        try:
            # Using a public LibreTranslate instance
            url = "https://libretranslate.de/translate"
            data = {
                'q': text,
                'source': 'en',
                'target': 'bn',
                'format': 'text'
            }
            
            response = requests.post(url, data=data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                return result['translatedText']
            return None
        except Exception as e:
            print(f"LibreTranslate translation error: {e}")
            return None
    
    def translate_with_google_translate_web(self, text: str) -> Optional[str]:
        """Translate using Google Translate web interface (unofficial)"""
        try:
            # This is a simplified approach - for production use, consider official APIs
            from urllib.parse import quote
            
            # Google Translate web interface URL
            url = f"https://translate.googleapis.com/translate_a/single"
            params = {
                'client': 'gtx',
                'sl': 'en',  # source language
                'tl': 'bn',  # target language
                'dt': 't',   # translation
                'q': text
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result and len(result) > 0 and len(result[0]) > 0:
                    return result[0][0][0]
            return None
        except Exception as e:
            print(f"Google Translate error: {e}")
            return None
    
    def is_likely_name(self, text: str) -> bool:
        """Check if text is likely a person's name"""
        # Remove common titles and check if remaining text looks like a name
        titles = ['mr', 'mrs', 'miss', 'ms', 'dr', 'prof', 'sir', 'madam']
        words = text.lower().split()
        
        # Remove titles
        filtered_words = [word for word in words if word not in titles]
        
        if not filtered_words:
            return False
        
        # Check if it's likely a name (1-4 words, mostly alphabetic)
        if len(filtered_words) > 4:
            return False
        
        for word in filtered_words:
            if not re.match(r'^[a-zA-Z]+$', word):
                return False
        
        # Check if it's a common service term (less likely to be a name)
        service_terms = ['customer', 'care', 'service', 'support', 'office', 'home', 'work', 'mobile', 'phone']
        if any(term in text.lower() for term in service_terms):
            return len(filtered_words) > 1  # Only translate if it's part of a longer phrase
        
        return True
    
    def translate_text_online(self, text: str) -> str:
        """Translate text using multiple online services with fallback"""
        if not text or not text.strip():
            return text
        
        # Check cache first
        cache_key = text.lower().strip()
        if cache_key in self.translation_cache:
            return self.translation_cache[cache_key]
        
        # If already contains Bengali, don't translate
        if self.is_bengali_text(text):
            self.translation_cache[cache_key] = text
            return text
        
        # If not English text, don't translate
        if not self.is_english_text(text):
            self.translation_cache[cache_key] = text
            return text
        
        # Extract emojis first
        emojis = self.extract_emojis(text)
        text_without_emojis = self.remove_emojis(text).strip()
        
        # Check if it's likely a name
        if not self.is_likely_name(text_without_emojis):
            self.translation_cache[cache_key] = text
            return text
        
        print(f"Translating: {text_without_emojis}")
        
        # Try different translation services
        translation_services = [
            self.translate_with_google_translate_web,
            self.translate_with_mymemory,
            self.translate_with_libretranslate
        ]
        
        translated_text = None
        for service in translation_services:
            try:
                translated_text = service(text_without_emojis)
                if translated_text and translated_text.strip():
                    # Basic validation - check if translation looks reasonable
                    if len(translated_text.strip()) > 0 and translated_text != text_without_emojis:
                        break
                    else:
                        translated_text = None
            except Exception as e:
                print(f"Translation service failed: {e}")
                continue
            
            # Add delay between requests to avoid rate limiting
            time.sleep(self.request_delay)
        
        # If no translation worked, keep original
        if not translated_text:
            print(f"Could not translate: {text_without_emojis}")
            translated_text = text_without_emojis
        else:
            print(f"Translated to: {translated_text}")
        
        # Add emojis back
        final_text = translated_text
        for emoji in emojis:
            final_text += emoji
        
        # Cache the result
        self.translation_cache[cache_key] = final_text
        
        return final_text
    
    def translate_name(self, name):
        """Translate name using online services"""
        return self.translate_text_online(name)
    
    def process_vcf_line(self, line):
        """Process a single VCF line and translate names if needed"""
        line = line.strip()
        
        if line.startswith('N:') or line.startswith('N;'):
            # Handle N field (Name field)
            if ';CHARSET=UTF-8:' in line:
                prefix = line.split(';CHARSET=UTF-8:')[0] + ';CHARSET=UTF-8:'
                name_part = line.split(';CHARSET=UTF-8:')[1]
            else:
                prefix = line.split(':')[0] + ':'
                name_part = line.split(':', 1)[1]
            
            # Split name components (Last;First;Middle;Prefix;Suffix)
            name_components = name_part.split(';')
            translated_components = []
            
            for component in name_components:
                if component:
                    translated_components.append(self.translate_name(component))
                else:
                    translated_components.append('')
            
            # Check if translation occurred
            if any(orig != trans for orig, trans in zip(name_components, translated_components)):
                # Add charset if translation happened and not already present
                if 'CHARSET=UTF-8' not in prefix:
                    prefix = prefix.replace(':', ';CHARSET=UTF-8:')
            
            return prefix + ';'.join(translated_components)
        
        elif line.startswith('FN:') or line.startswith('FN;'):
            # Handle FN field (Full Name field)
            if ';CHARSET=UTF-8:' in line:
                prefix = line.split(';CHARSET=UTF-8:')[0] + ';CHARSET=UTF-8:'
                name_part = line.split(';CHARSET=UTF-8:')[1]
            else:
                prefix = line.split(':')[0] + ':'
                name_part = line.split(':', 1)[1]
            
            translated_name = self.translate_name(name_part)
            
            # Check if translation occurred
            if name_part != translated_name:
                # Add charset if translation happened and not already present
                if 'CHARSET=UTF-8' not in prefix:
                    prefix = prefix.replace(':', ';CHARSET=UTF-8:')
            
            return prefix + translated_name
        
        return line
    
    def translate_vcf_file(self, input_file, output_file):
        """Translate VCF file from English to Bengali"""
        try:
            with open(input_file, 'r', encoding='utf-8') as infile:
                lines = infile.readlines()
            
            print(f"Processing {len(lines)} lines...")
            translated_lines = []
            
            for i, line in enumerate(lines, 1):
                if i % 100 == 0:  # Progress indicator
                    print(f"Processed {i}/{len(lines)} lines...")
                
                translated_line = self.process_vcf_line(line)
                translated_lines.append(translated_line + '\n')
            
            with open(output_file, 'w', encoding='utf-8') as outfile:
                outfile.writelines(translated_lines)
            
            print(f"\nTranslation completed! Output saved to: {output_file}")
            print(f"Translated {len(self.translation_cache)} unique names/terms")
            
        except FileNotFoundError:
            print(f"Error: Input file '{input_file}' not found.")
        except Exception as e:
            print(f"Error processing file: {str(e)}")
    
    def save_translation_cache(self, cache_file="translation_cache.json"):
        """Save translation cache to file for future use"""
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.translation_cache, f, ensure_ascii=False, indent=2)
            print(f"Translation cache saved to: {cache_file}")
        except Exception as e:
            print(f"Error saving cache: {e}")
    
    def load_translation_cache(self, cache_file="translation_cache.json"):
        """Load translation cache from file"""
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                self.translation_cache = json.load(f)
            print(f"Loaded {len(self.translation_cache)} cached translations")
        except FileNotFoundError:
            print("No translation cache found, starting fresh")
        except Exception as e:
            print(f"Error loading cache: {e}")

def main():
    translator = VCFTranslator()
    
    # Load existing translation cache if available
    translator.load_translation_cache()
    
    # Get input and output file paths
    input_file = input("Enter the path to your VCF file: ").strip()
    if not input_file:
        input_file = "contacts.vcf"  # default filename
    
    output_file = input("Enter the output file path (press Enter for 'translated_contacts.vcf'): ").strip()
    if not output_file:
        output_file = "translated_contacts.vcf"
    
    print("\nStarting translation process...")
    print("This may take a while for large contact lists due to API rate limits.")
    print("The program will automatically handle rate limiting and retries.\n")
    
    # Translate the file
    translator.translate_vcf_file(input_file, output_file)
    
    # Save translation cache for future use
    translator.save_translation_cache()

if __name__ == "__main__":
    main()