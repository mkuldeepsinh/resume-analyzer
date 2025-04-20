import os
import io
import spacy
import re
from pdfminer.converter import TextConverter
from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
from pdfminer.pdfpage import PDFPage
from pdfminer.layout import LAParams
import nltk
from nltk.corpus import stopwords

# Download necessary NLTK data
nltk.download('stopwords', quiet=True)

class CustomResumeParser:
    def __init__(self, resume_file):
        self.resume_file = resume_file
        try:
            self.nlp = spacy.load('en_core_web_sm')
        except:
            # If model not found, provide instruction to install
            raise Exception("Please install spaCy model with: python -m spacy download en_core_web_sm")
        
        self.text_raw = self.extract_text_from_pdf()
        self.text = ' '.join(self.text_raw.split())
        self.email = self.extract_email()
        self.phone = self.extract_phone()
        self.skills = self.extract_skills()
        self.name = self.extract_name()
        self.education = self.extract_education()

    def extract_text_from_pdf(self):
        """Extract text from PDF file"""
        resource_manager = PDFResourceManager()
        fake_file_handle = io.StringIO()
        converter = TextConverter(resource_manager, fake_file_handle, laparams=LAParams())
        page_interpreter = PDFPageInterpreter(resource_manager, converter)
        
        with open(self.resume_file, 'rb') as fh:
            for page in PDFPage.get_pages(fh, caching=True, check_extractable=True):
                page_interpreter.process_page(page)
                
            text = fake_file_handle.getvalue()
            
        # Close open handles
        converter.close()
        fake_file_handle.close()
        
        return text
    
    def extract_email(self):
        """Extract email from text using regex"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, self.text)
        return emails[0] if emails else ''
    
    def extract_phone(self):
        """Extract phone numbers from text using regex"""
        # Pattern to match various phone number formats
        phone_pattern = r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        phones = re.findall(phone_pattern, self.text)
        return phones[0] if phones else ''
    
    def extract_skills(self):
        """Extract skills from text using NLP and a predefined skills list"""
        skills = []
        # Common programming languages, tools, and frameworks
        skill_keywords = [
            "python", "java", "javascript", "html", "css", "sql", "nosql", "mongodb",
            "react", "angular", "vue", "node", "express", "django", "flask", "spring",
            "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy", "data science",
            "machine learning", "deep learning", "ai", "nlp", "data analysis",
            "aws", "azure", "gcp", "docker", "kubernetes", "git", "ci/cd",
            "agile", "scrum", "leadership", "project management", "teamwork"
        ]
        
        # Process the text
        doc = self.nlp(self.text.lower())
        
        # Extract skills by matching keywords in text
        for token in doc:
            token_text = token.text.lower()
            if token_text in skill_keywords:
                skills.append(token_text)
                
        # Also check for multi-word skills
        for skill in skill_keywords:
            if len(skill.split()) > 1:  # Check only multi-word skills
                if skill.lower() in self.text.lower():
                    skills.append(skill)
                    
        # Remove duplicates and sort
        skills = sorted(list(set(skills)))
        return skills
    
    def extract_name(self):
        """Extract name from the beginning of the resume"""
        # Use the first line or the largest text at the beginning as name
        lines = self.text_raw.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line and len(line.split()) <= 5:  # Assuming name is not more than 5 words
                # Check if line doesn't contain email or phone
                if '@' not in line and not re.search(r'\d{3}', line):
                    return line
        return ""
    
    def extract_education(self):
        """Extract education information"""
        education_keywords = ["degree", "bachelor", "master", "phd", "doctorate", "bsc", "msc", "b.tech", "m.tech", "college", "university"]
        doc = self.nlp(self.text.lower())
        
        # Simple approach: find sentences containing education keywords
        education_info = []
        sentences = re.split(r'[.!?]\s+', self.text)
        for sentence in sentences:
            for keyword in education_keywords:
                if keyword in sentence.lower():
                    education_info.append(sentence.strip())
                    break
                    
        return education_info
        
    def get_extracted_data(self):
        """Return the extracted data as a dictionary"""
        return {
            'name': self.name,
            'email': self.email,
            'mobile_number': self.phone,
            'skills': self.skills,
            'education': self.education,
            'no_of_pages': self.count_pages(),
            'degree': self.get_degree()
        }
        
    def count_pages(self):
        """Count the number of pages in the PDF"""
        with open(self.resume_file, 'rb') as f:
            return sum(1 for _ in PDFPage.get_pages(f))
            
    def get_degree(self):
        """Extract degree information from education"""
        degree_keywords = ["bachelor", "master", "phd", "doctorate", "bsc", "msc", "b.tech", "m.tech"]
        
        for edu in self.education:
            for keyword in degree_keywords:
                if keyword in edu.lower():
                    return keyword.title()
        
        return ""