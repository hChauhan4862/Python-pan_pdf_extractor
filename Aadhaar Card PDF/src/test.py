import json
import os
from classAadhaarPDF import AadhaarPDF

if __name__ == '__main__':
    # each pdf file in AADHAAR_FILES is processed
    DATA = []

    i = 0
    n = len(os.listdir('AADHAAR_FILES'))
    for file in os.listdir('AADHAAR_FILES'):
        print("Processing: " , file, "  :: ",i ,"of",n, end='\r')
        i += 1
        with open('AADHAAR_FILES/' + file, 'rb') as f:
            aadhaar = AadhaarPDF(f,password="202132", bruteForce=True)

        DATA.append(aadhaar.get_data())

        
    with open('data.json', 'w') as f:
        json.dump(DATA, f)