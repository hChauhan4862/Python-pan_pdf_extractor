import os
import fitz  # pip install --upgrade pip; pip install --upgrade pymupdf

from PIL import Image
from pyzbar.pyzbar import decode # pip install pyzbar

from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage

from io import StringIO
import gzip
import base64
import re

class HC_AADHAAR_PDF:
    def __init__(self, pdf_path, password = None, bruteForce = False):
        self.__pdf_path = pdf_path
        self.__password = password
        self.__uid = None
        self.__photo = None
        self.__address = None
        self.__mobile = None
        self.__pdf_text = None
        self.__QR_TEXT = None
        self.__QR_DATA = None
        self.__LOCAL_DATA = None

        if not pdf_path.endswith(".pdf"):
            raise Exception("Invalid pdf file")
        
        try:
            doc = fitz.Document(pdf_path)
        except:
            raise Exception(FileNotFoundError)
        
        if not self.__password and bruteForce:
            self.__bruteforce()
        
        if self.__password is not None:
            doc.authenticate(self.__password)
        
        try:
            PAGE_IMAGE = doc.get_page_images(0)
        except:
            if self.__password is None:
                raise Exception("Password Required")
            raise Exception("Password Incorrect")
        
        if not len(PAGE_IMAGE):
            raise Exception(FileNotFoundError)

        for img in PAGE_IMAGE:
            xref = img[0]
            pix = fitz.Pixmap(doc, xref)
            width, height = pix.width, pix.height
            if width == 160 and height == 200:
                self.__photo = base64.b64encode(pix.tobytes()).decode("utf-8")
            elif width == height:
                try:
                    # decode QR code from pixel map samples
                    pix.save("temp.png")
                    decoded = decode(Image.open("temp.png"))
                    if decoded:
                        self.__QR_TEXT = decoded[0].data.decode("utf-8")
                except:
                    raise Exception("Invalid pdf file")
                os.remove("temp.png")
        
    def get_text(self):
        if self.__pdf_text is None:
            self.__extract_text()
        
        return self.__pdf_text
    
    def get_json(self, pretty = False, pdf_text = False, photo = True, address = True, local = False):
        # docstring for local
        
        if self.__pdf_text is None:
            self.__extract_text()
        if self.__QR_DATA is None:
            self.__extract_qr_data()

        if self.__QR_DATA is None or self.__pdf_text is None:
            return None
        
        if local and self.__LOCAL_DATA is None:
            try:
                from google.transliteration import transliterate_word

                LOCAL = {}  
                LOCAL["name"] = transliterate_word(self.__QR_DATA["name"], lang_code="hi", max_suggestions=1)[0] if self.__QR_DATA["name"] and self.__QR_DATA["name"]!="" else None

                CO_TYPE = self.__QR_DATA["co"].split(" ") if self.__QR_DATA["co"] and self.__QR_DATA["co"]!="" else []
                if len(CO_TYPE) == 2:
                    LOCAL["co"] = CO_TYPE[0] + " " +transliterate_word(CO_TYPE[1], lang_code="hi", max_suggestions=1)[0] if CO_TYPE[1] and CO_TYPE[1]!="" else ""
                else:
                    LOCAL["co"] = transliterate_word(self.__QR_DATA["co"], lang_code="hi", max_suggestions=1)[0] if self.__QR_DATA["co"] and self.__QR_DATA["co"]!="" else None
                LOCAL["loc"] = transliterate_word(self.__QR_DATA["loc"], lang_code="hi", max_suggestions=1)[0] if self.__QR_DATA["loc"] and self.__QR_DATA["loc"]!="" else None
                LOCAL["vtc"] = transliterate_word(self.__QR_DATA["vtc"], lang_code="hi", max_suggestions=1)[0] if self.__QR_DATA["vtc"] and self.__QR_DATA["vtc"]!="" else None
                LOCAL["po"] = transliterate_word(self.__QR_DATA["po"], lang_code="hi", max_suggestions=1)[0] if self.__QR_DATA["po"] and self.__QR_DATA["po"]!="" else None
                LOCAL["dist"] = transliterate_word(self.__QR_DATA["dist"], lang_code="hi", max_suggestions=1)[0] if self.__QR_DATA["dist"] and self.__QR_DATA["dist"]!="" else None
                LOCAL["subdist"] = transliterate_word(self.__QR_DATA["subdist"], lang_code="hi", max_suggestions=1)[0] if self.__QR_DATA["subdist"] and self.__QR_DATA["subdist"]!="" else None
                LOCAL["state"] = transliterate_word(self.__QR_DATA["state"], lang_code="hi", max_suggestions=1)[0] if self.__QR_DATA["state"] and self.__QR_DATA["state"]!="" else None
                if self.__address:
                    LOCAL["address"] = self.__address.split(" ")[0] + ",".join([
                        transliterate_word(x, lang_code="hi", max_suggestions=1)[0] for x in  self.__address[len(self.__address.split(" ")[0]):].split(",") if x and x!=""
                    ])

                self.__LOCAL_DATA = LOCAL
            except Exception as e:
                print(e)
                pass

        
        
        DATA = {
            "uid": self.__uid,
            "pdf_text": self.__pdf_text if pdf_text else None,
            **self.__QR_DATA,
            "mobile": self.__mobile if self.__mobile and self.__mobile !="" else None,
            "address": self.__address if address else None,
            "local": self.__LOCAL_DATA if local else None,
            "photo": self.__photo if photo else None,
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
        
        aadhaar_number = re.findall(r'\d{4}\s+\d{4}\s+\d{4}', self.__pdf_text)
        if aadhaar_number:
            self.__uid = aadhaar_number[0].replace(" ", "")
        
        # Search text between "Address:" and "\n\n" using regex
        TXT = re.findall(r'A([\s]*)d([\s]*)d([\s]*)r([\s]*)e([\s]*)s([\s]*)s([\s]*):([\s]*)(.*?)\n\n', self.__pdf_text, re.DOTALL)
        if TXT:
            self.__address = TXT[0][8]
            self.__address = re.sub(r'A([\s]*)d([\s]*)d([\s]*)r([\s]*)e([\s]*)s([\s]*)s([\s]*):([\s]*)', '', self.__address).strip()
            self.__address = re.sub(r'\s+', ' ', self.__address).strip()
            self.__address = self.__address.replace("\n", " ")

        # search mobile number
        MOB = re.findall(r'[\d]{10}', self.__pdf_text)
        if MOB:
            self.__mobile = MOB[0]

        # if "Address:" in self.__pdf_text:
        #     self.__address = self.__pdf_text.split("Address:")[1].split("\n\n")[0].strip().replace("\n", " ")

    def __extract_qr_data(self):
        if self.__QR_TEXT is None or self.__QR_DATA is not None:
            return None
        DATA = {}
        if self.__QR_TEXT.startswith("<?xml"):
            import xml.etree.ElementTree as ET
            root = ET.fromstring(self.__QR_TEXT)
            # print(root.attrib)
            DATA["version"] = "XML"
            DATA["ref_no"] = root.attrib["uid"] if "uid" in root.attrib else None
            DATA["name"] = root.attrib["name"] if "name" in root.attrib else None
            DATA["dob"] = root.attrib["dob"].replace("/", "-") if "dob" in root.attrib else None
            DATA["gender"] = root.attrib["gender"] if "gender" in root.attrib else None
            DATA["co"] = root.attrib["co"] if "co" in root.attrib else None
            DATA["loc"] = root.attrib["loc"] if "loc" in root.attrib else None
            DATA["vtc"] = root.attrib["vtc"] if "vtc" in root.attrib else None
            DATA["po"] = root.attrib["po"] if "po" in root.attrib else None
            DATA["dist"] = root.attrib["dist"] if "dist" in root.attrib else None
            DATA["subdist"] = root.attrib["subdist"] if "subdist" in root.attrib else None
            DATA["state"] = root.attrib["state"] if "state" in root.attrib else None
            DATA["pc"] = root.attrib["pc"] if "pc" in root.attrib else None
        else:
            try:
                BYTES_ARRAY = int(self.__QR_TEXT).to_bytes((int(self.__QR_TEXT).bit_length() + 7) // 8, 'big')
                DECOMPRESSED_BYTES = gzip.decompress(BYTES_ARRAY)
                temp =  self.__QR_BYTES_ITER(DECOMPRESSED_BYTES)
            except:
                return None
            
            VERSION = next(temp).replace("b'", "")
            if VERSION not in ["1","2","3","V2"]:
                raise Exception("Unsupported QR code version")
            
            MOBILE_EMAIL = VERSION
            if VERSION == "V2":
                MOBILE_EMAIL = next(temp)
            
            REF_NO = next(temp)
            NAME = next(temp)
            DOB = next(temp)
            GENDER = next(temp)
            CO = next(temp)
            DIST = next(temp)
            LANDMARK = next(temp)
            HOUSE = next(temp)
            LOCATION = next(temp)
            PC = next(temp)
            PO = next(temp)
            STATE = next(temp)
            STREET = next(temp)
            SUBDIST = next(temp)
            VTC = next(temp)

            DATA["version"] = VERSION
            DATA["ref_no"] = REF_NO
            DATA["name"] = NAME
            DATA["dob"] = DOB
            DATA["gender"] = GENDER
            DATA["co"] = CO
            DATA["loc"] = ", ".join(x for x in [LANDMARK, HOUSE, LOCATION, STREET] if x!="")
            DATA["vtc"] = VTC
            DATA["po"] = PO
            DATA["dist"] = DIST
            DATA["subdist"] = SUBDIST
            DATA["state"] = STATE
            DATA["pc"] = PC
            DATA["dob"] = DOB

        self.__QR_DATA = DATA
        return True

    def __QR_BYTES_ITER(self, bytes_array):
        STR, OP = '', ''
        for byte in bytes_array:
            if byte == 255:
                OP, STR = STR, ''
                yield OP
            else:
                STR += chr(byte)
    
    def __checkPasswordList(self, password_list):
        doc = fitz.Document(self.__pdf_path)
        for pwd in password_list:
            try:
                doc.authenticate(pwd)
                doc.get_page_images(0)
                self.__password = pwd
                print("Password found: ",pwd)
                return pwd
            except:
                continue
        return False
    
    def __bruteforce(self):
        import datetime
        doc = fitz.Document(self.__pdf_path)
        with open("names_list.json", "r") as f:
            import json
            NAMES_LIST = json.load(f)
        

        PASSWORD_LIST = []
        MAX_YEAR = datetime.datetime.now().year
        MIN_YEAR = MAX_YEAR - 90

        # Extracting password from file name and other patterns
        FILE_NAME = self.__pdf_path.split("/")[-1].split(".")[0]
        SIX_DIGITS = re.findall(r'[\d]{6}', FILE_NAME)
        FOUR_DIGITS = re.findall(r'[\d]{4}', FILE_NAME)
        FIRST_FOUR_CHARS = re.findall(r'[a-zA-Z]{4}', FILE_NAME)
        FIRST_THREE_CHARS = re.findall(r'[a-zA-Z]{3}', FILE_NAME)
        FIRST_TWO_CHARS = re.findall(r'[a-zA-Z]{2}', FILE_NAME)

        if SIX_DIGITS:
            PASSWORD_LIST.append(SIX_DIGITS[0])
        
        pwd = self.__checkPasswordList(PASSWORD_LIST)
        if pwd: return pwd
        PASSWORD_LIST = []
        
        TEMP_NAME = False
        if FIRST_FOUR_CHARS or FIRST_THREE_CHARS or FIRST_TWO_CHARS:
            TEMP_NAME = (FIRST_FOUR_CHARS if FIRST_FOUR_CHARS else FIRST_THREE_CHARS if FIRST_THREE_CHARS else FIRST_TWO_CHARS)[0].upper()
            if FOUR_DIGITS:
                PASSWORD_LIST.append(TEMP_NAME+FOUR_DIGITS[0])
            for Y in range(MAX_YEAR,MIN_YEAR,-1):
                if FOUR_DIGITS and FOUR_DIGITS[0] == str(Y): continue
                PASSWORD_LIST.append(TEMP_NAME+str(Y))
        elif FOUR_DIGITS:
            for name in NAMES_LIST:
                PASSWORD_LIST.append(name+FOUR_DIGITS[0])
        
        pwd = self.__checkPasswordList(PASSWORD_LIST)
        if pwd: return pwd
        PASSWORD_LIST = []
        # End Extracting password from file name and other patterns
        
        # Brute force using names and years
        for name in NAMES_LIST:
            if TEMP_NAME and name == TEMP_NAME: continue
            for Y in range(MAX_YEAR,MIN_YEAR,-1):
                if FOUR_DIGITS and FOUR_DIGITS[0] == str(Y): continue
                PASSWORD_LIST.append(name+str(Y))
        
        pwd = self.__checkPasswordList(PASSWORD_LIST)
        if pwd: return pwd
        PASSWORD_LIST = []
        
        # Brute force using pin codes
        for pc in range(100000,999999):
            PASSWORD_LIST.append(str(pc))

        pwd = self.__checkPasswordList(PASSWORD_LIST)
        if pwd: return pwd
        PASSWORD_LIST = []
        
        # MAX = len(PASSWORD_LIST)
        

if __name__ == "__main__":
    """
        This is just for Example purpose
        Create a new file and import this file and use the class as you want to use it in your project.

        Example:
            from HC_AADHAAR_PDF import HC_AADHAAR_PDF
            test = HC_AADHAAR_PDF("e_aadhaar1234567890.pdf", password="XXXX####")
            JSON_DATA = test.get_json()
            EXTRACTED_TEXT = test.get_text()
        
        Example 2:
            from HC_AADHAAR_PDF import HC_AADHAAR_PDF
            test = HC_AADHAAR_PDF("e_aadhaar1234567890.pdf", bruteForce=True)
            JSON_DATA = test.get_json()
            EXTRACTED_TEXT = test.get_text()
        
        FOR BRUTE FORCE:
            It will take a lot of time to brute force the password.
            So, it is recommended to use the password if you know it.
            If you don't know the password, then you can use brute force.
            but save file with name containing any known part of password like: 
                first 4 characters of name and year of birth for new aadhaar card
                pin code for older aadhaar card format
            examples:
                SURESH.pdf      # Only name is known
                SURESH1990.pdf  # Name and year of birth is known
                1990.pdf        # Only year of birth is known
                123456.pdf      # pin code is known (for older aadhaar card format)
                
    """
    import time
    start_time = time.time()
    
    OBJ = HC_AADHAAR_PDF("e_aadhaar1234567890.pdf", password="XXXX####")

    print("Time taken: ", time.time()-start_time, "seconds")

    print(OBJ.get_json())
