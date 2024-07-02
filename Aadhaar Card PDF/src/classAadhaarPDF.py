import os
import fitz  # pip install --upgrade pip; pip install --upgrade pymupdf

import numpy as np
from pyzbar.pyzbar import decode as QRDecode

import gzip
import base64
import re
from datetime import datetime
import json
import io

class AadhaarPDFJson(object):
    def __init__(self):
        self.Photo = None

        self.UID = None
        self.Name = None
        self.Gender = None
        self.Mobile = None
        self.DOB = None
        self.CareOf = None
        # self.CareOfRelation = None
        self.Locality = None
        self.VillageTown = None
        self.PostOffice = None
        self.SubDistrict = None
        self.District = None
        self.State = None
        self.PinCode = None
        self.Address = None
        # self.Photo = None
        self.IssueDate = None
        self.DownloadDate = None


class AadhaarPDF:
    def __init__(self, pdf_file: io.TextIOWrapper, password: str = None, bruteForce: bool = False):
        """
        pdf_path: Path to the PDF file
        password: Password to the PDF file
        bruteForce: If True, brute force the password (default: False)
        """
        self.__data       = AadhaarPDFJson()
        self.__pdf_path   = None
        self.__password   = password
        self.__bruteForce = bruteForce
        self.__doc        = None
        self.__text       = None
        self.__date       = None
        self.__QR         = None
        self.__QRVERSION  = None

        self.__doc = fitz.Document(stream=pdf_file.read())

        assert self.__doc.is_pdf, "Not a valid PDF file"
        self.__pdf_path = pdf_file.name # os.path.abspath(self.__pdf_path)
        # print(self.__doc._getMetadata("CreationDate"))
        
        # Validate the password
        if self.__password is not None or self.__bruteForce:
            self.__authenticate()
        
        assert not self.__doc.is_encrypted, "Password is required to open the PDF file"

        images = self.__doc.get_page_images(0)

        assert len(images) != 0, "Not a valid Aadhaar PDF file :: EX001"

        # Extract the images
        for img in images:
            xref = img[0]
            pix = fitz.Pixmap(self.__doc, xref)
            width, height = pix.width, pix.height
            if width == 160 and height == 200 and self.__data.Photo is None:       # Phtograph of the Aadhaar holder
                self.__data.Photo = base64.b64encode(pix.tobytes()).decode("utf-8")
            elif width == height and self.__QR is None:                  # QR Code Image
                try:
                    self.__QR:str = QRDecode(np.frombuffer(pix.samples, dtype=np.uint8).reshape(height, width, pix.n))[0].data.decode("utf-8")
                except Exception as e:
                    # print(e)
                    pass
            if self.__data.Photo is not None and self.__QR is not None:
                break
        
        self.__text = self.__doc[0].get_text("text")

        assert self.__data.Photo is not None, "Not a valid Aadhaar PDF file :: EX002"
        assert self.__QR is not None, "Not a valid Aadhaar PDF file :: EX003"
        assert self.__QR != "", "Not a valid Aadhaar PDF file :: EX004"
        assert self.__text is not None, "Not a valid Aadhaar PDF file :: EX005"
        # print(self.__text)
        assert re.search(r'(UNIQUE[\s]+IDENTIFICATION[\s]+AUTHORITY[\s]+OF[\s]+INDIA)|(E_Aadhaar_UIDAI)',self.__text), "Not a valid Aadhaar PDF file :: EX006"

        self.__date = datetime.strptime(self.__doc.metadata["creationDate"][2:15], "%Y%m%d%H%M%S")
        self.__doExtract()

    def get_json(self):
        return json.dumps(dict(self.__data.__dict__))
    
    def get(self):
        return self.__data
        
    def get_data(self):
        return dict(self.__data.__dict__)
    
    ####################[:START:] EXTRACT AND PARSE DATA ####################
    def __doExtract(self):
        self.__parseQRCode()
        self.__parseText()

    def __parseText(self):
        TEXT = self.__text
        aadhaar_number  =   re.findall(r'\d{4}[ ]+\d{4}[ ]+\d{4}', TEXT)
        address         =   re.search(r'Addre[\s]*ss([:]?)(.*?)[\d]{6}\n',TEXT, re.DOTALL)
        mobile          =   re.findall(r'\s[6-9]{1}[0-9]{9}\s',TEXT)
        allDates        =   re.findall(r'[\d]{2}/[\d]{2}/[\d]{4}', re.sub(re.compile(r'[\s\.]+'),'', TEXT))

        if aadhaar_number and self.__data.UID is None:
            self.__data.UID = aadhaar_number[0].replace(" ", "")
        if address:
            self.__data.Address = re.sub("Addre[\s]*ss([:]?)([\n]?)", "", address[0])
        if mobile:
            self.__data.Mobile  = mobile[0].strip()

        if allDates:
            DATES = list(set(allDates))
            DATES = sorted(DATES, key=lambda x: datetime.strptime(x, "%d/%m/%Y"))
            DATES = [datetime.strptime(x, "%d/%m/%Y").strftime("%Y-%m-%d") for x in DATES]
            if len(DATES) > 2:
                self.__data.DOB             = DATES[0]
                self.__data.IssueDate       = DATES[1]
                self.__data.DownloadDate    = DATES[2]
            if len(DATES) == 2:
                self.__data.DOB             = DATES[0]
                self.__data.IssueDate       = DATES[1] # Any Download Date is Issue Date
                self.__data.DownloadDate    = DATES[1]
        
        if self.__QRVERSION == "XML2.0":               # for some aadhaar card issued in 2018
            t = self.__data.Address.replace("\n", "").split(",")
            assert len(t) >= 3, "Not a valid Aadhaar PDF file :: EX007"
            self.__data.CareOf      = t[0].strip()
            self.__data.State       = t[-1].split("-")[0].strip()
            self.__data.PinCode     = t[-1].split("-")[1].strip()
            self.__data.District    = t[-2].strip()
            self.__data.Locality    = ", ".join(t[1:-2]).strip()

    def __parseQRCode(self):
        QR_TEXT = self.__QR
        if QR_TEXT.startswith("<?xml"):
            self.__QRVERSION = "XML"
            self.__data.UID         =  self.__searchBetween(QR_TEXT,'uid="','"').strip()
            self.__data.Name        =  self.__searchBetween(QR_TEXT,'name="','"').strip()
            self.__data.DOB         =  self.__searchBetween(QR_TEXT,'dob="','"').strip()
            self.__data.Gender      =  self.__searchBetween(QR_TEXT,'gender="','"').strip()
            self.__data.CareOf      =  self.__searchBetween(QR_TEXT,'co="','"').strip()
            self.__data.Locality    =  self.__searchBetween(QR_TEXT,'loc="','"').strip()
            self.__data.VillageTown =  self.__searchBetween(QR_TEXT,'vtc="','"').strip()
            self.__data.PostOffice  =  self.__searchBetween(QR_TEXT,'po="','"').strip()
            self.__data.SubDistrict =  self.__searchBetween(QR_TEXT,'subdist="','"').strip()
            self.__data.District    =  self.__searchBetween(QR_TEXT,'dist="','"').strip()
            self.__data.State       =  self.__searchBetween(QR_TEXT,'state="','"').strip()
            self.__data.PinCode     =  self.__searchBetween(QR_TEXT,'pc="','"').strip()
            return True
        if QR_TEXT.startswith("<QDA") or QR_TEXT.startswith("<QDB"):  # for 2018 PDFs
            self.__QRVERSION = "XML2.0"
            self.__data.Name        =  self.__searchBetween(QR_TEXT,'n="','"').strip()
            self.__data.Gender      =  self.__searchBetween(QR_TEXT,'g="','"').strip()
            self.__data.DOB         =  self.__searchBetween(QR_TEXT,'d="','"').strip()
            return True
        
        # V2 QR Code
        self.__QRVERSION = "V2"
        try:
            BYTES_ARRAY = int(QR_TEXT).to_bytes((int(QR_TEXT).bit_length() + 7) // 8, 'big')
            DECOMPRESSED_BYTES = gzip.decompress(BYTES_ARRAY)
            temp =  self.__QR_BYTES_ITER(DECOMPRESSED_BYTES)
        except:
            # print(self.__QR)
            raise Exception("Unsupported QR code version :: EX001")

        VERSION = next(temp).replace("b'", "")
        if VERSION not in ["1","2","3","V2"]:
            raise Exception("Unsupported QR code version :: EX002")
        
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

        self.__data.Name        = NAME
        self.__data.DOB         = DOB
        self.__data.Gender      = GENDER
        self.__data.CareOf      = CO
        self.__data.Locality    = ", ".join(x for x in [LANDMARK, HOUSE, LOCATION, STREET] if x!="" and x !='.')
        self.__data.VillageTown = VTC
        self.__data.PostOffice  = PO
        self.__data.District    = DIST
        self.__data.SubDistrict = SUBDIST
        self.__data.State       = STATE
        self.__data.PinCode     = PC
        self.__data.DOB         = DOB
    
    def __QR_BYTES_ITER(self, bytes_array):
        STR, OP = '', ''
        for byte in bytes_array:
            if byte == 255:
                OP, STR = STR, ''
                yield OP
            else:
                STR += chr(byte)

    def __searchBetween(self, text, start, end):
        pattern = f"{start}(.*?){end}"
        match = re.search(pattern, text, re.DOTALL)
        return match.group(1) if match else ""
    
    ####################[:START:] AUTHENTICATE PASSWORD PROTECTED PDF ####################
    def __authenticate(self):
        if self.__password is not None and self.__checkPassword(self.__password):
            return self.__password
        elif self.__bruteForce:
            return self.__bruteForcePassword()
        else:
            assert False, "Invalid password"

    def __checkPassword(self, password):
        try:
            self.__doc.authenticate(password)
            self.__doc.get_page_images(0)   # Just to check if the password is correct
            return True
        except:
            return False

    def __checkPasswordList(self, password_list):
        for password in password_list:
            if self.__checkPassword(password):
                return True
        return False
        
    def __bruteForcePassword(self):
        # check if the brute force dictionary exists
        bruteForceDict = "tmp/names_list.json"
        assert os.path.exists(bruteForceDict), "Brute force dictionary not found"
        assert os.path.isfile(bruteForceDict), "Brute force dictionary not a file"
        assert bruteForceDict.endswith(".json"), "Brute force dictionary not a JSON file"

        # load the brute force dictionary
        with open(bruteForceDict, "r") as f:
            bruteForceDict = json.load(f)
        
        # brute force the password
        PASSWORD_LIST = [] # Blank list to store all the possible passwords to be tried

        MAX_YEAR = datetime.now().year
        MIN_YEAR = MAX_YEAR - 90
        
        # Try: Extracting password from file name and other patterns
        FILE_NAME = re.sub(re.compile(r'[\s]+'),'', ".".join(self.__pdf_path.split("/")[-1].split("."))[:-1]).upper() # remove all whitespaces from the file name
        FILE_NAME2 = ".".join(self.__pdf_path.split("/")[-1].split(".")[:-1]).upper() # 
        SIX_DIGITS = re.findall(r'[\d]{6}', FILE_NAME2)
        FOUR_DIGITS = re.findall(r'[\d]{4}', FILE_NAME2)
        FIRST_FOUR_CHARS = re.findall(r'([A-Z]{2}\.[A-Z])|([A-Z]{4})', FILE_NAME)
        FIRST_THREE_CHARS = re.findall(r'[A-Z]{3}', FILE_NAME)
        FIRST_TWO_CHARS = re.findall(r'[A-Z]{2}', FILE_NAME)
        FIRST_FOUR_CHARS = FIRST_FOUR_CHARS[0] if FIRST_FOUR_CHARS else None
        
        FIRST_FOUR_CHARS = list(filter(None, FIRST_FOUR_CHARS)) if FIRST_FOUR_CHARS else None
        FIRST_CHARS = (FIRST_FOUR_CHARS if FIRST_FOUR_CHARS else FIRST_THREE_CHARS if FIRST_THREE_CHARS else FIRST_TWO_CHARS if FIRST_TWO_CHARS else [""])[0]

        if SIX_DIGITS:
            PASSWORD_LIST.append(SIX_DIGITS[0])
        
        if FIRST_CHARS!="":
            if FOUR_DIGITS:
                PASSWORD_LIST.append(FIRST_CHARS + FOUR_DIGITS[0])
                for Y in range(MAX_YEAR,MIN_YEAR,-1):
                    if FOUR_DIGITS and FOUR_DIGITS[0] == str(Y): continue
                    PASSWORD_LIST.append(FIRST_CHARS+str(Y))
        elif FOUR_DIGITS:
            for v in bruteForceDict:
                PASSWORD_LIST.append(v+FOUR_DIGITS[0])
        
        if self.__checkPasswordList(PASSWORD_LIST):
            return True
        
        # assert False, "Could not brute force the password"

        # Try: Brute force the password based on the brute force dictionary and Years
        PASSWORD_LIST = []
        # check if self.__date is less than 04/10/2017
        # if self.__date < datetime(2017,10,4):
        
        for v in bruteForceDict:
            if FIRST_CHARS and v == FIRST_CHARS: continue
            for Y in range(MAX_YEAR,MIN_YEAR,-1):
                if FOUR_DIGITS and FOUR_DIGITS[0] == str(Y): continue
                PASSWORD_LIST.append(v+str(Y))
        
        if self.__checkPasswordList(PASSWORD_LIST):
            return True

        # assert False, "Could not brute force the password"

        # Try: Brute force the password based on the pincodes
        PASSWORD_LIST = []
        for pc in range(100000,999999):
            PASSWORD_LIST.append(str(pc))
        
        if self.__checkPasswordList(PASSWORD_LIST):
            return True

        assert False, "Could not brute force the password"
    ####################[:END:] AUTHENTICATE PASSWORD PROTECTED PDF ####################


if __name__ == "__main__":
    """
        This is just for Example purpose
        Create a new file and import this file and use the class as you want to use it in your project.

        Example:
            from HC_AADHAAR_PDF import HC_AADHAAR_PDF
            test = HC_AADHAAR_PDF(fileObject, password="XXXX####")
            JSON_DATA = test.get_json()
            EXTRACTED_TEXT = test.get_text()
        
        Example 2:
            from HC_AADHAAR_PDF import HC_AADHAAR_PDF
            test = HC_AADHAAR_PDF(fileObject, bruteForce=True)
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
    
    with open("e_aadhaar1234567890.pdf", "rb") as f:
        OBJ = AadhaarPDF(f, password="XXXX####", bruteForce=True)

    print("Time taken: ", time.time()-start_time, "seconds")

    print(OBJ.get_json())