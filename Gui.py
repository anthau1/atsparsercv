
import tkinter as tk
from tkinter import filedialog

import re
import phonenumbers
import pdfplumber
import os
import webbrowser
from ATSParserGUIInterface import ATSParserGUIInterface


SECTION_HEADERS = {
    "contact": ["contact", "contact information", "personal info", "personal information"],
    "profile": ["profile", "summary", "professional summary", "about me","profiili"],
    "work_experience": ["experience", "work experience", "employment history", "professional experience","työkokemus"],
    "education": ["education", "academic background", "qualifications","koulutus"],
    "skills": ["skills", "technical skills", "competencies", "expertise","taidot"]
}

HEADER_MAP = {h: sec for sec, hs in SECTION_HEADERS.items() for h in hs}
EMAIL_RE = re.compile(r'[\w\.-]+@[\w\.-]+\.\w+')
LINKEDIN_RE = re.compile(r'(https?://)?(www\.)?linkedin\.com/[A-Za-z0-9_\-/]+', re.IGNORECASE)


class ATSParserGUI(ATSParserGUIInterface):
    radio3 = None
    listbox = None

    def __init__(self, root):
        self.root = root
        self.root.title("ATS Resume Parser")
        self.root.geometry("900x300")
        self.select_button = tk.Button(root, text="Select PDF", command=self.select_file)
        self.select_button.pack()
        self.select_button.pack()
        self.listbox = tk.Listbox(root)

    def select_file(self):

        self.file_path = filedialog.askopenfilename(
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )

        if self.file_path:
            self.selected_file = self.file_path

            data = self.parse_ats_cv_english(self.selected_file)

            #generate cv
            #TODO Tarkista, onko Java mukana
            self.generate_cv_html(data)
            html_path = os.path.abspath("cv.html")

            webbrowser.open(f"file://{html_path}")

    def extract_contact(self,text):
        emails = list(set(EMAIL_RE.findall(text)));
        # Phones
        phones = []
        phone_candidates = re.findall(r'(\+?\d[\d\-\s\(\)]{6,}\d)', text)
        for pc in phone_candidates:
            try:
                parsed = phonenumbers.parse(pc, None)
                if phonenumbers.is_possible_number(parsed):
                    phones.append(phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164))
            except:
                pass

        # LinkedIn
        linkedin = None
        m = LINKEDIN_RE.search(text)
        if m:
            linkedin = m.group(0)
            if not linkedin.startswith("http"):
                linkedin = "https://" + linkedin
        return {"emails": emails, "phones": phones, "linkedin": linkedin}


    def parse_ats_cv_english(self,pdf_path):

        #chatgpt generated code !
        all_lines = []
        all_text = ""

         # 1. Read PDF
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                txt = page.extract_text()
                if txt:
                    all_lines.extend(txt.split("\n"))
                    all_text += txt + "\n"

        # 2. Extract contact info
        contact_info = self.extract_contact(all_text)

        # 3. Extract sections
        sections = {sec: [] for sec in SECTION_HEADERS}
        current = None
        for line in all_lines:
            clean = line.strip().lower()

            if clean in HEADER_MAP:
                current = HEADER_MAP[clean]
                continue

            if current:
                sections[current].append(line.strip())

        # 4. Remove empty lines
        for sec in sections:
            sections[sec] = [l for l in sections[sec] if l]

         # 5. Combine contact info
        sections["contact"] = contact_info
        #skannaa tiedosto m'iden varalta

        patternjava = r'\bjava\b(?!script)'
        patternmysql = r'\bjava\b(?!script)'
        patternjava = r'\bjava\b(?!script)'
        patternpython = r'\bpython\b(?!script)'

        sections["found1"] = {
            "Java": bool(re.search(patternjava, all_text, re.IGNORECASE))
            , "Python": bool(re.search(patternpython, all_text, re.IGNORECASE)),
            "mysql": bool(re.search(patternmysql, all_text, re.IGNORECASE))
        }
        return sections


    def generate_cv_html(self ,cv_data, output_path="cv.html"):
        points = 0
        score = cv_data["found1"]

        for key in score.keys():

            if score.get(key):
                points = points + 25


            """
        Luo HTML-tiedosto ATS-CV JSON-datan pohjalta.

        cv_data esimerkki:
        {
        "contact": {"emails": [...], "phones": [...], "linkedin": "..."},
        "profile": [...],
        "work_experience": [...],
        "education": [...],
        "skills": [...]
        }
        """
        # --- Yhteystiedot HTML ---

        color = "red"

        if points > 25:
            color = "green"

        contact_html = "<p class=\"" + color + "\"\>score " + str(points) + "</p>"
        contact = cv_data.get("contact", {})

        if emails := contact.get("emails"):
            contact_html += "<p><strong>Email:</strong> " + ", ".join(emails) + "</p>\n"
        if phones := contact.get("phones"):
            contact_html += "<p><strong>Phone:</strong> " + ", ".join(phones) + "</p>\n"
        if linkedin := contact.get("linkedin"):
            contact_html += f'<p><strong>LinkedIn:</strong> <a href="{linkedin}">{linkedin}</a></p>\n'

         # --- Profiili ---
        profile_html = ""
        if profile := cv_data.get("profile"):
            profile_html += "<p>" + "<br>".join(profile) + "</p>"

        # --- Työkokemus ---
        work_html = ""
        first=True

        if work := cv_data.get("work_experience" ):
            work_html = ""
            if work := cv_data.get("work_experience"):
                work_html += "<div class=\"work\"><ul>\n"

                for item in work:
                    #first line

                    if re.search(r" \| ", item, re.IGNORECASE):
                        if first:
                            work_html +="<div class=\"workplace\">"
                            first=False
                        else:
                            work_html += "</div><div class=\"workplace\""
                        work_html += f"<li><b>{item}</b></li>\n"
                    elif re.search(r"\b(?:19|20)\d{2}\b", item, re.IGNORECASE):

                        work_html += f"<li><em>{item}</em></li>\n"
                    else:
                         work_html += f"<li>{item}</li>\n"
                work_html += "</ul></div>"
                work_html += "</div>"


        # --- Koulutus ---
        edu_html = ""
        if edu := cv_data.get("education"):
            edu_html += "<ul>\n"
            for item in edu:
                edu_html += f"<li>{item}</li>\n"
            edu_html += "</ul>"

        # --- Taidot ---
        skills_html = ""
        if skills := cv_data.get("skills"):
            skills_html += "<ul>\n"
            for s in skills:
                skills_html += f"<li>{s}</li>\n"
            skills_html += "</ul>"

     # --- Kokonais-HTML ---

        html_content = \
        f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
    <meta charset="UTF-8">
    <title>CV</title>

    <style>

    body {{ font-family: Arial, sans-serif; margin: 40px; }}
    h1 {{ color: #333; }}
    h2 {{ color: #555; margin-top: 20px; }}
    ul {{ list-style-type: disc; margin-left: 20px; }}
    a {{ color: #1a0dab; text-decoration: none; }}
    </style>
    <link rel="stylesheet" href="cv.css">
    </style>
    </head>
    <body>

    <h1 id="test">Curriculum Vitae</h1>
    <div>
    <h2> Metadetails </h2>
    <p  class="{ "green"}"> Score {score}</p>
    </div>

    <div>
    <h2>Contact</h2>
{contact_html}
</div>
<div>
<h2>Profile</h2>
{profile_html}
</div>
<div>
<h2>Work Experience</h2>
{work_html}
</div>

<div>
<h2>Education</h2>
{edu_html}
</div>
<div>
<h2>Skills</h2>
{skills_html}
</div>
</body>
</html>
"""

    # --- Kirjoita tiedostoon ---
        with open(output_path, "w", encoding="utf-8") as f:
         f.write(html_content)
