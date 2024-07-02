import os
import fitz  # pip install --upgrade pip; pip install --upgrade pymupdf

import numpy as np
from pyzbar.pyzbar import decode as QRDecode # pip install pyzbar

import gzip
import base64
import re
from datetime import datetime
import json
import io

class PanPDFJson(object):
    def __init__(self):
        self.Photo = None
        self.Sign = None

        self.PAN = None
        self.Name = None
        self.Father = None
        self.DOB = None
        self.Gender = None
        self.Source = None


class PanPDF:
    def __init__(self, pdf_file: io.TextIOWrapper, password: str = None, bruteForce: bool = False):
        """
        pdf_path: Path to the PDF file
        password: Password to the PDF file
        bruteForce: If True, brute force the password (default: False)
        """
        self.__data       = PanPDFJson()
        self.__password   = password
        self.__bruteForce = bruteForce
        self.__doc        = None
        self.__text       = None

        self.__doc = fitz.Document(stream=pdf_file.read())

        assert self.__doc.is_pdf, "Not a valid PDF file"
        # print(self.__doc._getMetadata("CreationDate"))
        
        # Validate the password
        if self.__password is not None or self.__bruteForce:
            self.__authenticate()
        
        assert not self.__doc.is_encrypted, "Password is required to open the PDF file"

        images = self.__doc.get_page_images(0)

        assert len(images) != 0, "Not a valid PAN PDF file :: EX001"

        # Extract the images
        IMAGES_LIST = []
        for img in images:
            xref = img[0]
            pix = fitz.Pixmap(self.__doc, xref)
            width, height = pix.width, pix.height
            IMAGES_LIST.append("{}x{}".format(width, height))

            if width == height == 213:       # Phtograph of the Aadhaar holder
                self.__data.Photo = base64.b64encode(pix.tobytes()).decode("utf-8")
                self.__data.Source = "UTIITSL"
            elif width == height == 204:
                self.__data.Photo = base64.b64encode(pix.tobytes()).decode("utf-8")
                self.__data.Source = "NSDL"
            elif width == 160 and height == 200:
                self.__data.Photo = base64.b64encode(pix.tobytes()).decode("utf-8")
                self.__data.Source = "INSTANT_PAN"
            elif width == 333 and height == 137:
                # NSDL SIGN
                self.__data.Sign = base64.b64encode(pix.tobytes()).decode("utf-8")

            elif (
                    width == 207 and height == 150 # Standard size for uti thumb immpression
                        ) or (
                    width != height and  # because any other image which is shown 2 time assumed as sign but QR code also shown 2 time with same height width
                    IMAGES_LIST.count("{}x{}".format(width, height)) == 2   
                  ):
                # UTIITSL SIGN
                self.__data.Sign = base64.b64encode(pix.tobytes()).decode("utf-8")

        
        self.__text = self.__doc[0].get_text("text")

        assert self.__data.Photo is not None, "Not a valid PAN PDF file :: EX002"
        # print(self.__text)
        assert re.search(r'(INCOME[\s]+TAX)',self.__text.upper()), "Not a valid PAN PDF file :: EX006"
        self.__doExtract()

    def get_json(self):
        return json.dumps(dict(self.__data.__dict__))
    
    def get(self):
        return self.__data
        
    def get_data(self):
        return dict(self.__data.__dict__)
    
    ####################[:START:] EXTRACT AND PARSE DATA ####################
    def __doExtract(self):
        self.__parseText()

    def __parseText(self):
        PDF_TEXT = self.__text

        PAN_NO = re.findall(r"[A-Z]{5}[0-9]{4}[A-Z]{1}", PDF_TEXT)
        DOB    = re.findall(r"[0-9]{2}\/[0-9]{2}\/[0-9]{4}", PDF_TEXT)
        AADHAAR= re.findall(r"[X]{8}\d{4}", PDF_TEXT)

        if len(PAN_NO):
            self.__data.PAN = PAN_NO[0]
        if len(DOB):
            self.__data.DOB = DOB[0]
        
        TEMP = PDF_TEXT.split("\n")
        for e in TEMP:
            e = e.strip()
            if re.match(r"^[A-Z\s]{3,}$", e):
                if self.__data.Name is None:
                    self.__data.Name = e
                elif self.__data.Father is None:
                    self.__data.Father = e
            elif e in ["Male","Female"] and self.__data.Gender is None:
                if e=="Female":
                    self.__data.Gender = "F"
                elif e == "Male":
                    self.__data.Gender = "M"

        if len(AADHAAR):
            # Instant Pan Service
            temp = PDF_TEXT.split(self.__data.PAN)
            if len(temp) > 0:
                temp = temp[1].split(self.__data.DOB)
                self.__data.Name = temp[0].replace("\n", "").strip()
                if len(temp):
                    temp = temp[1].split(AADHAAR[0])[0].strip()
                    if temp=="Female":
                        self.__data.Gender = "F"
                    elif temp=="Male":
                        self.__data.Gender = "M"
        return True

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

    def __bruteForcePassword(self):
        import datetime
        tmp_date = datetime.datetime(1900, 1, 1)
        while tmp_date < datetime.datetime.now():
            tmp_date += datetime.timedelta(days=1)
            if self.__checkPassword(tmp_date.strftime("%d%m%Y")):
                return tmp_date.strftime("%d%m%Y")
        assert False, "Could not brute force the password"
    ####################[:END:] AUTHENTICATE PASSWORD PROTECTED PDF ####################



if __name__ == "__main__":

    # with open("E1.pdf", "rb") as f: test = PanPDF(f,password="15011928", bruteForce=True)
    # with open("E2.pdf", "rb") as f: test = PanPDF(f,password="01011969", bruteForce=True)
    # with open("E3.pdf", "rb") as f: test = PanPDF(f,password="01011969", bruteForce=True)
    # with open("E4.pdf", "rb") as f: test = PanPDF(f,password="01011969", bruteForce=True)
    # with open("E5.pdf", "rb") as f: test = PanPDF(f,password="01011969", bruteForce=True)
    with open("EP.pdf", "rb") as f: test = PanPDF(f,password="01011969", bruteForce=True)

    data = test.get_data()
    print(data)