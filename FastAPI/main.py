from fastapi import FastAPI, HTTPException, Depends ,status
from typing import Annotated,List, Optional
from sqlalchemy.orm import Session
from pydantic import BaseModel , Field
#from .database import SessionLocal, engine
#from database import SessionLocal, engine 
#import models

from FastAPI.database import SessionLocal, engine 
from FastAPI import models 
from fastapi.middleware.cors import CORSMiddleware




app = FastAPI(title="Transactions API",openapi_url="/openapi.json")

origins = [
    "http://localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
)

class TransactionBase(BaseModel):
    amount: float = Field(gt=0)
    category: str = Field(max_length=50,default="işlem")
    description: Optional[str] = Field(default="Açıklama")
    is_income: bool
    date: str
        
class TransactionModel(TransactionBase):
    id: int
    
    class Config:     # Bu, ORM ile Pydantic arasında veri aktarımını kolaylaştırır. 
        from_attributes = True

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()  

db_dependecy = Annotated[Session, Depends(get_db)]

# Veritabanı tablolarını oluşturma
models.Base.metadata.create_all(bind=engine)

@app.post("/transactions/", response_model=TransactionModel)
async def create_transaction(transaction: TransactionBase, db: db_dependecy):
    db_transaction = models.Transaction(**transaction.model_dump())
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction




@app.get("/transactions/",response_model=List[TransactionModel])
async def read_transactions(db:db_dependecy,skip:int =0 , limit:int = 100):
    transactions = db.query(models.Transaction).offset(skip).limit(limit).all()
    return transactions



@app.get("/transactions/{transactions_id}",status_code= status.HTTP_202_ACCEPTED)
async def get_byId(transactions_id : int , db:Session = Depends(get_db)):
    result = db.query(models.Transaction).filter(models.Transaction.id == transactions_id).first()
    if result is None:
        raise HTTPException(
            status_code= 404,
            detail= f"ID {transactions_id} : Mevcut değil"
        )
        
    return result



@app.put("/{transactions_id}")
async def update_transactions(transactions_id:int , transaction:TransactionBase , db:Session = Depends(get_db)):
    
    result = db.query(models.Transaction).filter(models.Transaction.id == transactions_id).first()
    if result is None:
        raise HTTPException(
            status_code= 404,
            detail=f"ID {transactions_id} : Mevcut değil"
        )
    
    result.amount = transaction.amount
    result.category = transaction.category
    result.description = transaction.description
    result.is_income = transaction.is_income
    result.date = transaction.date
    
    
    db.commit()
    db.refresh(result)
    
    return transaction


@app.delete("/{transactions_id}",status_code=status.HTTP_200_OK)
async def delete_transactions(transactions_id : int , db:Session = Depends(get_db)):
    result = db.query(models.Transaction).filter(models.Transaction.id ==transactions_id).first()
    
    if result is None:
        raise HTTPException(
            status_code= 404,
            detail= f"ID {transactions_id} : Mevcut değil"
        )
    
    
    db.query(models.Transaction).filter(models.Transaction.id == transactions_id).delete()
    
    db.commit()
    
    return {"detail": "Silme işlemi başarılı."}


