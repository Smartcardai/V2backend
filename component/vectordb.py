from langchain_community.vectorstores import Qdrant
import qdrant_client
import os, shutil
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader, TextLoader, PyMuPDFLoader, PyPDFLoader, JSONLoader, Docx2txtLoader
from langchain_community.document_loaders.unstructured import UnstructuredFileLoader
import json
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from qdrant_client.http.models import Filter, FieldCondition, MatchValue, MatchText


import warnings
warnings.filterwarnings("ignore")

# from response import embeddings

load_dotenv()
qdrant_host= os.getenv('QDRANT_HOST')
qdrant_key= os.getenv('QDRANT_KEY')

# size=768
llm_key= os.getenv('LLM_KEY')

embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001",google_api_key=llm_key)

client= qdrant_client.QdrantClient(
    url=qdrant_host,
    api_key=qdrant_key
)

vector_config= qdrant_client.http.models.VectorParams(
    size= 768,
    distance= qdrant_client.http.models.Distance.COSINE
)





def create_vectorstore(collection_name):
    
    if True:
    
        client.recreate_collection(
            collection_name=collection_name,
            vectors_config=vector_config
        )

        
        

    vector_store = Qdrant(
        client=client, 
        collection_name=collection_name, 
        embeddings=embeddings,
    )

    return vector_store

def append_PDFdata_vectorstore(vector_store,data_lst):
   
    
    
    text_splitter= RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=150, length_function= len)
    docs=text_splitter.split_documents(data_lst)

    doc= docs[0]

    print(doc.metadata)

    vector_store.add_documents(docs)

def append_DOCXdata_vectorstore(vector_store,collection_path):
   # loader= DirectoryLoader(collection_path,glob="**/*.txt" ,loader_cls=TextLoader)
    
    loader= DirectoryLoader(collection_path,glob="**/*.docx" ,loader_cls=Docx2txtLoader)
    
    
    documents= loader.load()
    

    text_splitter= RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=150, length_function= len)
    docs=text_splitter.split_documents(documents)

    vector_store.add_documents(docs)

def append_txtdata_vectorstore(vector_store,collection_path):
   # loader= DirectoryLoader(collection_path,glob="**/*.txt" ,loader_cls=TextLoader)
    
    loader= DirectoryLoader(collection_path,glob="**/*.txt" ,loader_cls=TextLoader)
    
    
    documents= loader.load()
    

    text_splitter= RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=150, length_function= len)
    docs=text_splitter.split_documents(documents)


    vector_store.add_documents(docs)

    



def vector_store_to_retriever(collection_name):
    vector_store = Qdrant(
        client=client, 
        collection_name=collection_name, 
        embeddings=embeddings,
    )
    return vector_store.as_retriever()





def metadata_retriever(collection_name, meta_val, query):
    vector_store = Qdrant(
        client=client, 
        collection_name=collection_name, 
        embeddings=embeddings,
    )

    print(f"\nDebug Information:")
    print(f"1. Collection name: {collection_name}")
    print(f"2. Searching for filename: {meta_val}")
    print(f"3. Query: {query}")

    # First, let's check what's in the collection
    try:
        # Get all documents in the collection
        all_docs = client.scroll(
            collection_name=collection_name,
            limit=10,  # Get first 10 documents
            with_payload=True
        )[0]
        
        print("\n4. Sample documents in collection:")
        for doc in all_docs[:3]:  # Show first 3 documents
            print(f"   Metadata: {doc.payload}")
        
        # Try the search with different matching strategies
        strategies = [
            # Exact match
            Filter(
                must=[
                    FieldCondition(
                        key="filename",
                        match=MatchValue(value=meta_val)
                    )
                ]
            ),
            # Partial match
            Filter(
                must=[
                    FieldCondition(
                        key="filename",
                        match=MatchText(text=meta_val)
                    )
                ]
            ),
            {"filename":meta_val}
        ]
        
        for i, filter_condition in enumerate(strategies):
            print(f"\n5. Trying search strategy {i+1}")
            docs = vector_store.similarity_search(
                query=query,
                k=3,
                filter=filter_condition
            )
            

            if docs:
                print(f"   Found {len(docs)} documents!")
                return docs[0].page_content
            else:
                print(f"   Strategy {i+1} found no documents")
        
        # If no documents found with any strategy
        print( {
            "error": "No matching documents found",
            "details": {
                "collection": collection_name,
                "searched_filename": meta_val,
                "available_files": [doc.payload.get("filename") for doc in all_docs]
            }
        })
        return {
            "error": "No matching documents found",
            "details": {
                "collection": collection_name,
                "searched_filename": meta_val,
                "available_files": [doc.payload.get("filename") for doc in all_docs]
            }
        }
        
    except Exception as e:
        error_msg = f"Error in retrieval: {str(e)}"
        print({"exception":"sdsd",
            "error": error_msg,
            "details": {
                "collection": collection_name,
                "searched_filename": meta_val
            }
        })
        return {
            "error": error_msg,
            "details": {
                "collection": collection_name,
                "searched_filename": meta_val
            }
        }


def retrieve_content(retriever,query):
    
    docs=retriever.invoke(query)
    print(len(docs))
    content=docs[0]
    
    chunk= content.page_content
    # print(chunk)
    
    metadata= content.metadata['filename']
    try:
        pnum= content.metadata['page number']
        filename= metadata.split('/')[-1]
        # filename= filename.split('\\')[-1]
        foldername= metadata.split('/')[-2]

        
        
        return chunk, filename, foldername, pnum
    except:
        filename= metadata.split('/')[-1]
        # filename= filename.split('\\')[-1]
        foldername= metadata.split('/')[-2]
        
        
        return chunk, filename, foldername
    



def delete_collection(collection_name):
    client.delete_collection(collection_name=collection_name)
 





