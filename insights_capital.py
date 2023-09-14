import requests
from bs4 import BeautifulSoup
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from transformers import pipeline
import re
import pandas as pd
import fitz  # This is PyMuPDF
import requests
from flask import current_app

def load_model():
    tokenizer = AutoTokenizer.from_pretrained("nbroad/ESG-BERT")
    model = AutoModelForSequenceClassification.from_pretrained("nbroad/ESG-BERT")
    classifier = pipeline('text-classification', model=model, tokenizer=tokenizer)
    return classifier

def get_data(name):
    name = name.lower()
    name = name.split()
    name = "-".join(name)
    url = "https://www.responsibilityreports.com/Company/"+str(name)
    r = requests.get(url)
    soup = BeautifulSoup(r.content, 'html.parser')
    data = {}
    for d in soup.find_all('div', attrs={'class': 'archived_report_content_block'}):
        if d is not None: 
            for inn_d in d.find_all('div', attrs={'class': 'text_block'}):
                if inn_d is not None:
                    l = []
                    for s in inn_d.find('span', attrs={'class': 'heading'}):
                        if s is not None:
                            l.append(s)
                        else:
                            l.append('None')
                    for a in inn_d.find_all('a', attrs={'target': '_blank'}):
                        if a is not None: 
                            l.append(str("https://www.annualreports.com/") + a['href'])
                        else:
                            l.append('None')
                    data[l[0]] = l[1]
    return data

class PDFParser:
    def __init__(self, pdf_url):
        self.pdf_url = pdf_url
        self.pdf_content = self.fetch_pdf_content()
        self.text = self.get_text_clean()

    def fetch_pdf_content(self):
        response = requests.get(self.pdf_url)
        response.raise_for_status()  # Raise an exception for unsuccessful responses
        return response.content

    def get_text_clean(self):
        text = ""
        with fitz.open("pdf", self.pdf_content) as doc:
            for page_num in range(doc.page_count):
                page = doc.load_page(page_num)
                text += page.get_text()
        text = re.sub(r'\n', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text

    def get_text_clean_list(self):
        text = self.get_text_clean()
        text_list = text.split('.')
        return text_list
    
def run_classifier(url):
    classifier=load_model()
    pp = PDFParser(url)
    sentences = pp.get_text_clean_list()
    print(f"The CSR report has {len(sentences):,d} sentences")
    result = classifier(sentences)
    df = pd.DataFrame(result)
    return(df)

def calculate_msci_esg_score(ratings):
    e_labels = ["Water_And_Wastewater_Management", "Ecological_Impacts", "Energy_Management",
                "Physical_Impacts_Of_Climate_Change", "GHG_Emissions", "Air_Quality"]

    s_labels = ["Employee_Health_And_Safety", "Critical_Incident_Risk_Management",
                "Human_Rights_And_Community_Relations", "Labor_Practices",
                "Employee_Engagement_Inclusion_And_Diversity", "Access_And_Affordability",
                "Customer_Privacy", "Data_Security", "Customer_Welfare"]

    g_labels = ["Waste_And_Hazardous_Materials_Management", "Director_Removal",
                "Supply_Chain_Management", "Product_Design_And_Lifecycle_Management",
                "Business_Ethics", "Selling_Practices_And_Product_Labeling",
                "Systemic_Risk_Management", "Management_Of_Legal_And_Regulatory_Framework",
                "Business_Model_Resilience", "Competitive_Behavior"]

    e_ratings = [ratings[label] for label in e_labels]
    s_ratings = [ratings[label] for label in s_labels]
    g_ratings = [ratings[label] for label in g_labels]

    e_rating = sum(e_ratings) / len(e_ratings)
    s_rating = sum(s_ratings) / len(s_ratings)
    g_rating = sum(g_ratings) / len(g_ratings)

    total_esg_rating = (e_rating + s_rating + g_rating) / 3

    # Map the ratings to MSCI ESG scores (0.0 to 10.0)
    msci_esg_score = {
        "E_Rating": e_rating * 10,
        "S_Rating": s_rating * 10,
        "G_Rating": g_rating * 10,
        "Total_ESG_Rating": total_esg_rating * 10
    }

    return msci_esg_score

def classify_esg_rating(score):
    if 8.571 <= score <= 10.000:
        return "AAA"
    elif 7.143 <= score < 8.571:
        return "AA"
    elif 5.714 <= score < 7.143:
        return "A"
    elif 4.286 <= score < 5.714:
        return "BBB"
    elif 2.857 <= score < 4.286:
        return "BB"
    elif 1.429 <= score < 2.857:
        return "B"
    else:
        return "CCC"

def calculate_esg_ratings(ratings):
    e_rating = ratings['E_Rating']
    s_rating = ratings['S_Rating']
    g_rating = ratings['G_Rating']
    total_esg_rating = ratings['Total_ESG_Rating']

    e_letter_score = classify_esg_rating(e_rating)
    s_letter_score = classify_esg_rating(s_rating)
    g_letter_score = classify_esg_rating(g_rating)
    total_esg_letter_score = classify_esg_rating(total_esg_rating)

    return {
        "E_Letter_Score": e_letter_score,
        "S_Letter_Score": s_letter_score,
        "G_Letter_Score": g_letter_score,
        "Total_ESG_Letter_Score": total_esg_letter_score
    }