from abc import ABC, abstractmethod

class ATSParserGUIInterface(ABC):

    @abstractmethod
    def select_file(self):
        pass

    @abstractmethod
    def extract_contact(self,text):
        pass

    @abstractmethod
    def parse_ats_cv_english(self, pdf_path):
        pass

    @abstractmethod
    def generate_cv_html(self, cv_data, output_path="cv.html"):
        pass
