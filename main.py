from fastapi import FastAPI,UploadFile,Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import HTTPException
from typing import List
from file import FileProcessor,FileBlobWrapper
from json import loads,dumps,dump
import os,boto3,io
from utils import request_open_ai
app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:8000",
    "https://example.com",
    "https://example.net",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"], 
)

@app.get('/')
async def home():
    return 'home'

@app.post('/generator')
async def chat_completion(files:List[UploadFile],project_name:str = Form(),customer_name:str = Form()):
    processed_response = ""
    for index,file in enumerate(files):
        print(file.filename)
        file_uploaded = FileProcessor(file)
        processed_response += f'Content- {index}'+"\n \n"+file_uploaded.process_file_to_txt()+"\n \n"

    response = request_open_ai(processed_response)
    modified_res = response.content
    return {'message':modified_res}
    
@app.get('/upload')
async def chat_completion_v2():
    try:
        root_path = './case_study_generator'
        output_path = './output'
        for folder in os.listdir(root_path):
            print(f"Processing {folder} ....")
            processed_response = ""
            for file in os.listdir(root_path+"/"+folder):
                c=0
                file_path = root_path+"/"+folder+"/"+file
                with open(file_path,mode='rb') as ob_file:
                    file_uploaded = FileBlobWrapper(ob_file,filename=file,content_type=file.rsplit('.')[-1])
                    processed_file = FileProcessor(file_uploaded)
                    processed_response += f'Content- {c}'+"\n \n"+processed_file.process_file_to_txt()+"\n \n"
                    c+=1
            modified_res = {}
            try:
                response = request_open_ai(processed_response)
                
                modified_res = {"project":str(folder),'csg':response.content}
            except Exception as e:
                modified_res = {"project":str(folder),'csg':str(e)}

            with open(output_path+"/"+str(folder)+".json",mode='w') as json_file:
                dump(modified_res, json_file)
            
        return "process executed"
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))

@app.get('/upload/s3')
async def chat_completion_v3(bucket_name:str = Form(),s3_input_path:str = Form(),s3_ouput_path:str=Form()):
    try:
        s3 = boto3.client('s3', aws_access_key_id=os.getenv("S3_ACCESS_KEY"),
                        aws_secret_access_key=os.getenv("S3_SECRET_KEY"))
        
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix=s3_input_path,Delimiter='/')
        for folder in response.get('CommonPrefixes', []):
            folder_prefix = folder.get('Prefix')
            processed_response = ""
            c=0
            print(f"Processing {str(folder_prefix.split('/',1)[-1].replace('/',''))}")
            files_response = s3.list_objects_v2(Bucket=bucket_name, Prefix=folder_prefix)
            if 'Contents' in files_response:
                # Iterate over each object
                for obj in files_response['Contents']:
                    key = obj['Key']
                    file_key = key.split('/')[-1]
                    print(key)
                    # Create a stream to store the file content
                    file_stream = io.BytesIO()

                    # Download the file into the stream
                    s3.download_fileobj(bucket_name, key, file_stream)
                    file_stream.seek(0)
                    file_uploaded = FileBlobWrapper(file_stream,filename=file_key,content_type=file_key.rsplit('.')[-1])
                    processed_file = FileProcessor(file_uploaded)
                    processed_response += f'Content- {c}'+"\n \n"+processed_file.process_file_to_txt()+"\n \n"
                    c+=1
                    # Reset the stream position to the beginning
                modified_res = {}
                try:
                    response = request_open_ai(processed_response)
                    
                    modified_res = {"project":str(folder_prefix.split('/',1)[-1].replace('/','')),'csg':response.content}
                except Exception as e:
                    modified_res = {"project":str(folder_prefix.split('/',1)[-1].replace('/','')),'csg':str(e)}


                


                try:
                    json_data = dumps(modified_res)
                    file_obj = io.BytesIO(json_data.encode('utf-8'))
                    s3.upload_fileobj(file_obj, bucket_name, s3_ouput_path+str(folder_prefix.split('/',1)[-1].replace('/',''))+".json")

                except Exception as e:
                    raise HTTPException(status_code=500,detail=str(e))
            else:
                raise HTTPException(status_code=400,detail=f"No files found with prefix: {s3_input_path}")
        return "process executed"

    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))
