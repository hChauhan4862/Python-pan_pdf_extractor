# Python-pan_pdf_extractor
A UnOfficial pan card pdf data parsing class in Python

This is just for Example purpose
import this file and use the class as you want to use it in your project.

# Features Supported:
* Extract PAN Card Data from PDF by cracking the password
* Extract PAN Card Data from PDF by providing the password
* NSDL PAN Card PDF
* UTI PAN Card PDF
* Instant PAN Card PDF

# Usage Example:

## Example 1:

    from HC_PAN_PDF import HC_PAN_PDF
    MyObj = HC_PAN_PDF("MyPanCard.pdf", password="01011990")
    JSON_DATA = MyObj.get_json()        # retrun DICT
    EXTRACTED_TEXT = MyObj.get_text()   # return STRING
    META_INFO = MyObj.get_meta()        # return DICT

## Example 2:

    from HC_PAN_PDF import HC_PAN_PDF
    MyObj = HC_PAN_PDF("MyPanCard.pdf", bruteForce=True)
    JSON_DATA = MyObj.get_json()        # retrun DICT
    EXTRACTED_TEXT = MyObj.get_text()   # return STRING
    META_INFO = MyObj.get_meta()        # return DICT

# BRUTE FORCE:
It is recommended to use the password if you know because bruteforce option will take around 1 Minute to crack the password.
So If you don't know the password, and have patience then you can use try brute force method to break it down.