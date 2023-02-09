# Python-aadhaar_pdf_extractor
A UnOfficial aadhaar pdf data parsing class in Python

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