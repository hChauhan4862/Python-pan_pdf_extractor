import fitz  # pip install --upgrade pip; pip install --upgrade pymupdf
from pyzbar.pyzbar import decode # pip install pyzbar

from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage

from io import StringIO
import base64
import re

class HC_PAN_PDF:
    def __init__(self, pdf_path, password = None, bruteForce = False):
        self.__pdf_path = pdf_path
        self.__password = password
        self.__PAN_NO = None
        self.__NAME = None
        self.__FATHER = None
        self.__DOB = None
        self.__GENDER = None
        self.__PHOTO = None
        self.__SIGN = None
        self.__VERSION = None
        self.__pdf_text = None
        self.__METADATA = None
        self.bruteForceResult = -1
        self.bruteForceTime = -1

        if not pdf_path.endswith(".pdf"):
            raise Exception("Invalid pdf file")
        
        try:
            doc = fitz.Document(pdf_path)
        except:
            raise Exception(FileNotFoundError)
        
        if not self.__password and bruteForce:
            import time
            start = time.time()
            self.__bruteforce()
            end = time.time()
            self.bruteForceTime = end - start
            if self.__password is None:
                self.bruteForceResult = 0
            else:
                self.bruteForceResult = 1
            
            print("Brute Force Result: ", self.__password)
        
        if self.__password is not None:
            doc.authenticate(self.__password)
        
        try:
            PAGE_IMAGE = doc.get_page_images(0)
        except:
            if self.__password is None:
                raise Exception("Password Required")
            raise Exception("Password Incorrect")
        
        self.__METADATA = doc.metadata
        
        if not len(PAGE_IMAGE):
            raise Exception(FileNotFoundError)

        i = 0
        IMAGES_LIST = []
        for img in PAGE_IMAGE:
            i += 1
            xref = img[0]
            pix = fitz.Pixmap(doc, xref)
            width, height = pix.width, pix.height
            IMAGES_LIST.append("{}x{}".format(width, height))

            pix.save("op/{}.png".format(i))

            if width == height == 213:
                self.__PHOTO = base64.b64encode(pix.tobytes()).decode("utf-8")
                self.__VERSION = "UTIITSL"
            elif width == height == 204:
                self.__PHOTO = base64.b64encode(pix.tobytes()).decode("utf-8")
                self.__VERSION = "NSDL"
            elif width == 160 and height == 200:
                self.__PHOTO = base64.b64encode(pix.tobytes()).decode("utf-8")
                self.__VERSION = "INSTANT_PAN"
            elif width == 333 and height == 137:
                # NSDL SIGN
                self.__SIGN = base64.b64encode(pix.tobytes()).decode("utf-8")

            elif (
                    width == 207 and height == 150 # Standard size for uti thumb immpression
                        ) or (
                    width != height and  # because any other image which is shown 2 time assumed as sign but QR code also shown 2 time with same height width
                    IMAGES_LIST.count("{}x{}".format(width, height)) == 2   
                    ):
                # UTIITSL SIGN
                self.__SIGN = base64.b64encode(pix.tobytes()).decode("utf-8")

    def get_meta(self):
        import json
        return json.dumps(self.__METADATA, indent=4)

    def get_text(self):
        if self.__pdf_text is None:
            self.__extract_text()
        
        return self.__pdf_text
    
    def get_json(self, pretty = False):        
        if self.__pdf_text is None and self.__extract_text() == None:
            return None

        DATA = {
            "PAN_NO": self.__PAN_NO,
            "NAME": self.__NAME,
            "FATHER": self.__FATHER,
            "GENDER": self.__GENDER,
            "DOB": self.__DOB,
            "VERSION": self.__VERSION,
            "PHOTO": self.__PHOTO,
            "SIGN": self.__SIGN,
        }

        if pretty:
            import json
            return json.dumps(DATA, indent=4)

        return DATA
        
    def __extract_text(self):
        rsrcmgr = PDFResourceManager()
        retstr = StringIO()
        codec = 'utf-8'
        laparams = LAParams()
        device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
        fp = open(self.__pdf_path, 'rb')
        interpreter = PDFPageInterpreter(rsrcmgr, device)

        for page in PDFPage.get_pages(fp, pagenos = set(), maxpages=0, password=self.__password,caching=False, check_extractable=False):
            interpreter.process_page(page)

        self.__pdf_text = retstr.getvalue()

        fp.close()
        device.close()
        retstr.close()
        
        PAN_NO = re.findall(r"[A-Z]{5}[0-9]{4}[A-Z]{1}", self.__pdf_text)
        DOB    = re.findall(r"[0-9]{2}\/[0-9]{2}\/[0-9]{4}", self.__pdf_text)
        AADHAAR= re.findall(r"[X]{8}\d{4}", self.__pdf_text)
        if len(PAN_NO):
            self.__PAN_NO = PAN_NO[0]
        if len(DOB):
            self.__DOB = DOB[0]
        
        TEMP = self.__pdf_text.split("\n\n")
        for e in TEMP:
            if re.match(r"^[A-Z\s]{3,}$", e):
                if self.__NAME is None:
                    self.__NAME = e
                elif self.__FATHER is None:
                    self.__FATHER = e
            elif e in ["Male","Female"] and self.__GENDER is None:
                if e=="Female":
                    self.__GENDER = "F"
                elif e == "Male":
                    self.__GENDER = "M"

        if len(AADHAAR):
            temp = self.__pdf_text.split(self.__PAN_NO)
            if len(temp) > 0:
                temp = temp[1].split(self.__DOB)
                self.__NAME = temp[0]
                if len(temp):
                    temp = temp[1].split(AADHAAR[0])[0].strip()
                    if temp=="Female":
                        self.__GENDER = "F"
                    elif temp=="Male":
                        self.__GENDER = "M"
            # Instant Pan Service



        return True

    def __bruteforce(self):
        import datetime
        doc = fitz.Document(self.__pdf_path)
        PASSWORD_LIST = []
        # new date on 1950-01-01
        tmp_date = datetime.datetime(1900, 1, 1)
        while tmp_date < datetime.datetime.now():
            PASSWORD_LIST.append(tmp_date.strftime("%d%m%Y"))
            tmp_date += datetime.timedelta(days=1)

        for pwd in PASSWORD_LIST:
            try:
                doc.authenticate(pwd)
                doc.get_page_images(0)
                self.__password = pwd
                return True
            except:
                continue

if __name__ == "__main__":
    # test = HC_PAN_PDF("E2.pdf", password="01011969")
    # test = HC_PAN_PDF("E1.pdf", password="15011928")
    test = HC_PAN_PDF("E3.pdf", password="01012000")
    # test = HC_PAN_PDF("EP.pdf")
    print(test.bruteForceTime, "seconds")
    print(test.get_json())
    with open("output.json", "w") as f:
        f.write(test.get_json(pretty=True))
    with open("output.txt", "w") as f:
        f.write(test.get_meta())