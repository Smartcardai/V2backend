from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse, Response
from typing import List, Optional
import os
import shutil
from pydantic import BaseModel
import time
import requests
import json
import re
import glob
from fastapi.middleware.cors import CORSMiddleware
import io


import warnings
warnings.filterwarnings("ignore")

from component.vectordb import create_vectorstore, append_PDFdata_vectorstore, retrieve_content, vector_store_to_retriever, delete_collection, metadata_retriever
from component.response import doc_agent_response #  analyze_json, process_with_pandas_agent, process_firebase_response, process_firebase_xml, process_firebase_srt

from component.firebase_fileUploads import create_folder_upload_files, retrieve_collection_from_firebase, retrieve_collection_name_from_firebase, retrieve_file_from_firebase
from component.prompt import default_prompt, prompt_latex


from agents.csv import process_with_pandas_agent
from agents.json import analyze_json
from agents.srt import process_firebase_srt
from agents.xls import process_firebase_response
from agents.xml import process_firebase_xml

app = FastAPI()




app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*", "http://localhost:3000", "https://pdf-chat-nu-green.vercel.app","https://pdf-chat-nu-green.vercel.app/backend-testing"],
    allow_methods=["*"],
    allow_headers=["*"],
)



def clean_latex(text):
    return re.sub(r'```html', '```', text)







class UploadRequest(BaseModel):
    name: str
    links: Optional[str] = None
    uuid: str





@app.post("/upload")
async def upload_files(
    
    files: List[UploadFile] = File(None),
    json_data: Optional[str] = Form(...),
):
    data = json.loads(json_data)
    request = UploadRequest(**data)
    
    userID = request.uuid
    name= request.name
    links= request.links
    
    
    if files:
        for file in files:
            
            file_path=f'users/{userID}/folders/{name}/{file.filename}'

            test= create_folder_upload_files(file_path, file)
            
            # with open(file_path, "wb") as buffer:
            #     shutil.copyfileobj(file.file, buffer)
            

    
    
    lst, data_type = retrieve_collection_from_firebase(f'{userID}/{name}/')
    
    vec_name= rf'{userID}-{name}'
    if data_type =='application/pdf':
        vector_store = create_vectorstore(vec_name)
        append_PDFdata_vectorstore(vector_store,lst)

    elif data_type =='application/vnd.openxmlformats-officedocument.wordprocessingml.document':
        vector_store = create_vectorstore(vec_name)
        append_PDFdata_vectorstore(vector_store,lst)

    elif data_type =='text/plain':
        vector_store = create_vectorstore(vec_name)
        append_PDFdata_vectorstore(vector_store,lst)

    return JSONResponse(status_code=200, content={"message": "Files and links uploaded successfully."})

@app.get("/collections/{uuid}")
async def get_collections(uuid:str):
    path=f'{uuid}/folders/'
    test_dir= retrieve_collection_name_from_firebase(path)
    if len(test_dir)==0:
        return []
    
    collections = []
    for folder_name in test_dir:
        collections.append({"name": folder_name})

    return collections



@app.post("/folderandquery/{uuid}/{foldername}")
async def query_the_agent(uuid:str, foldername:str, request:dict):
    chat_history= request.get("chat_history")
    user_prompt= request.get("prompt")

    print(user_prompt)

    print(type(user_prompt))

    data_lst, data_type = retrieve_collection_from_firebase(f'{uuid}/{foldername}/')
    query = request.get("query")
    
    
    
    if user_prompt!= "None":
        prompt= user_prompt
    else:
        prompt= default_prompt
        

    

    if data_type in ['application/pdf','application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
        vec_name= f'{uuid}-{foldername}'
        retriever= vector_store_to_retriever(vec_name)
        content, filenameTest, foldernameTest, pnum=retrieve_content(retriever,query)
        agent_response= doc_agent_response(prompt,content,chat_history, query)
        response= f'{agent_response} \n filename:{filenameTest} \n foldername:{foldernameTest} \n page num:{pnum}'



    elif data_type== 'text/plain':
        vec_name= f'{uuid}-{foldername}'
        retriever= vector_store_to_retriever(vec_name)
        content, filenameTest, foldernameTest =retrieve_content(retriever,query)
        agent_response= doc_agent_response(prompt,content,chat_history, query)
        response= f'{agent_response} \n filename:{filenameTest} \n foldername:{foldernameTest}'

    elif data_type== 'application/json':

        query= f"chat_history: {chat_history}\nquery: {query}"
        
        response= analyze_json(data_lst, query)

    elif data_type in ['application/octet-stream', 'application/x-subrip', 'text/srt']:
        query= f"chat_history: {chat_history}\nquery: {query}"
        response= process_firebase_srt(data_lst, query)

    elif data_type== 'text/xml':
        query= f"chat_history: {chat_history}\nquery: {query}"
        response= process_firebase_xml(data_lst, query)

    elif data_type== 'text/csv':
        query= f"chat_history: {chat_history}\nquery: {query}"
        response= process_with_pandas_agent(data_lst, query)

    elif data_type in['application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']:
        query= f"chat_history: {chat_history}\nquery: {query}"
        response= process_firebase_response(data_lst, query)
    
    
    
   
    inter_response= doc_agent_response(prompt_latex,response,'NONE', prompt_latex)
    
    clean_response= clean_latex(inter_response)
    print(response)
    return {"response":response, "response_latex": clean_response}


@app.post("/fileandquery/{uuid}/{foldername}/{filename}")
async def queryfile_the_agent(uuid:str, foldername:str, filename, request:dict):
    user_prompt= request.get("prompt")

    data_lst, data_type = retrieve_file_from_firebase(f'{uuid}/{foldername}/{filename}')
    query = request.get("query")

    chat_history= request.get("chat_history")

    if user_prompt!= "None":
        prompt= user_prompt
    else:
        prompt= default_prompt
        

    if data_type in ['application/pdf','application/vnd.openxmlformats-officedocument.wordprocessingml.document','text/plain']:
        vec_name= f'{uuid}-{foldername}'
        metadata_val= rf"{data_lst}"

        
        doc= metadata_retriever(vec_name, metadata_val, query)
        response= doc_agent_response(prompt,doc,chat_history, query)


    elif data_type== 'application/json':

        query= f"chat_history: {chat_history}\nquery: {query}"
        
        response= analyze_json(data_lst, query)

    elif data_type in ['application/octet-stream', 'application/x-subrip', 'text/srt']:
        query= f"chat_history: {chat_history}\nquery: {query}"
        response= process_firebase_srt(data_lst, query)

    elif data_type== 'text/xml':
        query= f"chat_history: {chat_history}\nquery: {query}"
        response= process_firebase_xml(data_lst, query)

    elif data_type== 'text/csv':
        query= f"chat_history: {chat_history}\nquery: {query}"
        response= process_with_pandas_agent(data_lst, query)

    elif data_type in['application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']:
        query= f"chat_history: {chat_history}\nquery: {query}"
        response= process_firebase_response(data_lst, query)
    
    
    
   
    inter_response= doc_agent_response(prompt_latex,response,'NONE', prompt_latex)
    
    clean_response= clean_latex(inter_response)
    print(response)
    return {"response":response, "response_latex": clean_response}


@app.delete("/collections/delete/{uuid}")
async def delete_data_collection(collection_name:dict, uuid:str):
    try:
        name= collection_name.get('name')
        vec_name= f'{uuid}-{name}'
        # test_path= os.path.join(uuid,name)
        delete_collection(vec_name)
        return JSONResponse(status_code=200, content={"message": f"The collection {name} is deleted."})
    except Exception as e:
        return JSONResponse(status_code=400, content={'error':str(e)})





@app.post('/report')
async def generate_report(request: dict):
    prompt= 'You are provided with chat history'
    query= 'write a through report summary of the chat'
    content= request.get('chat')
    response= doc_agent_response(prompt,content,'NONE', query)
    return {"response": response}

@app.post('/podcast')
async def generate_podcast(request: dict):

    prompt= 'You are provided with chat history '
    


    query= '''
    Please create a podcast transcript with alternating dialogue between a male and a female speaker. Include interjections such as 'Oh!', 'Hmm', 'Well', 'Wow!', etc., to make the conversation feel more natural. The output must be formatted as a JSON array of objects. Each object should contain two key-value pairs: one for the male's dialogue and one for the female's dialogue. Use the following format:

    The keys must be "male" and "female".
    The values must be raw strings representing the conversation.
    No additional text, explanations, or guest names should be included.
    Ensure that the conversation flows naturally with interjections to simulate a real conversation.

    Here's an example of the expected response structure:
    [
        {
            "male": r"Hello, how are you?",
            "female": r"Oh! I'm doing well, thank you. How about you?"
        },
        {
            "male": r"Hmm, what are you doing?",
            "female": r"I'm studying at the moment."
        }
    ]

    Only provide the JSON response as described, and nothing else.
    Response Format should be JSON object only as shown in the example
    Follow the example expected response structure only nothing else
    Do not include any text like json or anything other than following the response structure
    '''

    # content= request.get('chat')
    response= doc_agent_response(prompt,request.get('chat'),'NONE', query)
    
    
    def clean_and_extract_json( text):
    # First pattern to match and remove ```json or ```JSON and their closing ```
        code_block_pattern = r'```(?:json|JSON)\n(.*?)```'

        # Pattern to match "user_res: " prefix if it exists
        prefix_pattern = r'^user_res:\s*'

        def process_text(input_text):
            # Remove prefix if it exists
            text_without_prefix = re.sub(prefix_pattern, '', input_text.strip())

            # Check if we have a code block
            code_block_match = re.search(code_block_pattern, text_without_prefix, re.DOTALL)
            if code_block_match:
                # If we found a code block, return its contents
                return code_block_match.group(1).strip()
            else:
                # If no code block markers, return the cleaned text
                return text_without_prefix.strip()

        return process_text(text)
    
    response= clean_and_extract_json(response)
    print(response)
    
    return {"response": response}




@app.post('/trigger/{uuid}/{old_folder_name}/{new_folder_name}')
async def trigger_firebase(uuid: str, old_folder_name: str, new_folder_name: str):
    # global vector_store
    try:
        data_lst, data_type = retrieve_collection_from_firebase(f'{uuid}/{new_folder_name}/')
        print(len(data_lst))
        print(data_type)
        if data_type in ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain']:
                old_vec_name = f'{uuid}-{old_folder_name}'
                new_vec_name = f'{uuid}-{new_folder_name}'
                
                try:
                    
                    delete_collection(old_vec_name)
                    time.sleep(2)
                    
                    
                except Exception as e:
                    print(f"Error deleting old collection: {e}")
                
                try:
                    
                    
                    retries = 10
                    for attempt in range(retries):
                        vector_store = create_vectorstore(new_vec_name)
                        
                        collections = vector_store.client.get_collections()
                        collection_names = [c.name for c in collections.collections]
                        
                        if new_vec_name in collection_names:
                            break
                        else:
                            if attempt < retries - 1:
                                print(f"Retrying collection creation check (Attempt {attempt + 1}/{retries})...")
                                time.sleep(2)  # Wait for 2 seconds before retrying
                            else:
                                raise Exception(f"Collection {new_vec_name} was not created successfully")
                    
                    # Add a small delay to ensure the collection is fully created
                    time.sleep(1)
                    append_PDFdata_vectorstore(vector_store, data_lst)
                    
                    return {"status": "success", "message": "Vector store updated successfully"}
                except Exception as e:
                    print(f"Error in vector store operations: {e}")
                    return {"status": "error", "message": str(e)}
        else:
            pass

    except:
        pass




def fetch_with_retry(url, max_retries=20, delay=1):
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'User-Agent': 'ApiConnector/1.0'
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            if response.status_code == 429 and attempt < max_retries - 1:
                time.sleep(delay * (2 ** attempt))  # Exponential backoff
            else:
                raise e
    
    raise requests.RequestException("Max retries reached")

@app.post("/ApiConnector/{uuid}")
async def api_connector(link: dict, uuid:str):
    url = link.get('link')
    if not url:
        raise HTTPException(status_code=400, detail="No link provided")
    
    try:
        response = fetch_with_retry(url)
        
        # Try to parse as JSON first
        try:
            return {'response': response.json(), 'content_type': 'json'}
        except json.JSONDecodeError:
            # If it's not JSON, return as text
            return {'response': response.text, 'content_type': 'text'}
    
    except requests.RequestException as e:
        error_detail = str(e)
        if hasattr(e, 'response') and e.response is not None:
            error_detail += f"\nResponse content: {e.response.text}"
        if "Too Many Attempts" in error_detail:
            raise HTTPException(status_code=429, detail="Rate limit exceeded. Please try again later.")
        raise HTTPException(status_code=500, detail=f"Error fetching URL: {error_detail}")



    

@app.post("/imgchat/{query}/{uuid}")
async def ChatWithImg(query: str, file: UploadFile = File(...)):
    from PIL import Image
    import base64
    from langchain_google_genai import ChatGoogleGenerativeAI
    from dotenv import load_dotenv
    from langchain_core.messages import HumanMessage

    load_dotenv()


    llm_key= os.getenv('LLM_KEY')
    contents = await file.read()
    image = Image.open(io.BytesIO(contents))
    model = ChatGoogleGenerativeAI(model="gemini-1.5-flash", api_key=llm_key)

    def get_image_base64(image_raw):
        buffered = io.BytesIO()
        image_raw.save(buffered, format=image_raw.format)
        img_byte = buffered.getvalue()

        return base64.b64encode(img_byte).decode('utf-8')
    def file_to_base64(file_bytes):
        return base64.b64encode(file_bytes).decode('utf-8')

    image_base64 = get_image_base64(image)
    response = model.invoke(
        [
            HumanMessage(
                content=[
                    {"type": "text", "text": query},
                    {"type": "image_url", "image_url": f"data:image/jpeg;base64,{image_base64}"}
                ]
            )
        ]
    )
    
    return {"analysis": response.content}




if __name__ == "__main__":
    import uvicorn
    # uvicorn.run(app, host="0.0.0.0", port=8000)
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("server:app", host="0.0.0.0", port=port)

