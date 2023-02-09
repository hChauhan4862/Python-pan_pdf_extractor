# Python Aadhaar PDF Data Parser
A UnOfficial aadhaar pdf data parsing class in Python

This is just for Example purpose
import this file and use the class as you want to use it in your project.

# Usage Example:

## Example 1:

    from HC_AADHAAR_PDF import HC_AADHAAR_PDF
    test = HC_AADHAAR_PDF("e_aadhaar1234567890.pdf", password="XXXX####")
    JSON_DATA = test.get_json()
    EXTRACTED_TEXT = test.get_text()

## Example 2:

    from HC_AADHAAR_PDF import HC_AADHAAR_PDF
    test = HC_AADHAAR_PDF("e_aadhaar1234567890.pdf", bruteForce=True)
    JSON_DATA = test.get_json()
    EXTRACTED_TEXT = test.get_text()

# BRUTE FORCE:
It is recommended to use the password if you know it because bruteforce option will take a lot of time to crack the password.
So If you don't know the password, and have patience then you can use try brute force method to break it down.

Note: You can improve its response time if you help it recognizing your passowrd by save file with name containing any known part of password like: 

First 4 characters of name and year of birth for new aadhaar card

Pin code for older aadhaar card format

#### examples:
    SURESH.pdf      # Only name is known
    SURESH1990.pdf  # Name and year of birth is known
    1990.pdf        # Only year of birth is known
    123456.pdf      # pin code is known (for older aadhaar card format)