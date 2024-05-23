from dotenv import load_dotenv
from openai import OpenAI
import os,json
load_dotenv()





def request_open_ai(extracted_text):

    client = OpenAI(api_key=os.getenv('KEY'))

    system_prompt = """You are an extremely skilled AI Model in Extracting key information and question answering.
            I am going to give you a task of locating and extracting information from the following content.
            read it thorougly and keenly.
            skip the preamble go straight into fetching answers for the questions in the below json document. fill the answers in the same json document and
            display it. if there are no answers fill N/A in the json document.
            strictly check for json formatting dont miss any commas,double quotas and curly braces.
            
            {
                    "industry_vertical":null,
                    "customer_overview":
                            {
                                    "customer_name":null,
                                    "location":null,
                                    "business_scope":null,
                                    "company_size":null,
                            },
                            "project_overview":
                                        {
                                            "objective":null,
                                            "techstack":[null],
                                            "benefits":null
                                        },
                            
                                "implementation_approach":null,
                                "challenges":null,
                                "expected_results":null,
                                "impact":null,
                                "project_deliverables":null
        }

"""
    
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo-16k",
        temperature=0.1,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": extracted_text}
        ]
        )
    
    return completion.choices[0].message