default_prompt=''' 
Follow these principles in your interactions:

1. **Consultative Approach:**
2. **Tailored Recommendations:** 
3. **Detailed Information:** 
4. **Comparison:** If applicable
5. **Value-Added Services:** 
6. **Proactive Assistance:** 
7. **Gratitude and Follow-Up:**  

Always give a relevant response  for the query
'''

prompt2 ='''
You will be given text extracted from an image of a card in the Reference Data, which could be a business card, credit card, driver's license, or any other type of identification card. 

Your task is to analyze the text and extract relevant information, structuring it into a Python dictionary.

The dictionary should have the following keys, if applicable based on the type of card:

* `name` 
* `company` (for business cards)
* `designation` (for business cards)
* `card_number` (for credit cards, driver's licenses, etc.)
* `expiry_date` (for credit cards)
* `issue_date` (for driver's licenses)
* `phone_number`
* `website`
* `email`
* `address` 

The values for these keys should be the corresponding information extracted from the text. 

**Please note:**

* If any of the information is missing from the text, the corresponding value in the dictionary should not exist`.
* Ensure the extracted information is accurate and free of any extra characters or symbols.
* Prioritize extracting key information that is relevant to the type of card detected.

Now, process the following text and provide the structured dictionary:

'''
prompt_img='''
**Task:** 
Extract structured data from text extracted from an image of a card (business card, credit card, driver's license, etc.).

**Output Format:**
Python dictionary with the following keys (if applicable): 

* `name` 
* `company` 
* `designation` 
* `card_number` 
* `expiry_date`
* `issue_date` 
* `phone_number`
* `website`
* `email`
* `address` 


* If information is missing, set the corresponding value to `None`.
* Ensure extracted information is accurate and clean.
* Prioritize key information relevant to the detected card type.
* Also provide the output in pretty print
'''

prompt3='''
**Task:** 
You'll be provided with text extracted from an image of various card types (business card, credit card, debit card, driver's license, PAN card, etc.). 

**Objective:** 
Analyze the text, identify the card type, and extract relevant information. Structure the extracted data into a Python dictionary as Json Pretty Print.

**Output Format:**

* A string that represents the extracted data in a visually formatted way, resembling the output of Python's `pprint` function.
* Keys: Relevant designations based on the card type (e.g., `name`, `address`, `card_number`, etc.)
* Values: Corresponding information extracted from the text
* If information is missing, set the value to `None`.
* Ensure extracted information is accurate and free of extra characters/symbols

'''

prompt4= '''
You are provided with information using that you have to write detailed research description in points that explains everything
'''
prompt_latex= '''
convert the provided content into latex and use this in html

<head>

<title>Boundary Work Formulas</title>

<script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>

<script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>

</head>

and convert all into html and only give the html code

'''