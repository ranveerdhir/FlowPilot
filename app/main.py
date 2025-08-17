from fastapi import FastAPI

#create an instance of FastAPI application

app = FastAPI()

#deffine path operation decorator for the rout operation url 
@app.get("/")
def read_root():
    """
    Handles Get requests to the root URL.
    Return a simple Dictionary.
    """
    return {"message":"OK"}
    
