from typing import Annotated
from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as star_http_exp
from schemas import UserCreate, UserResponse, PostCreate, PostResponse

from sqlalchemy import select 
from sqlalchemy.orm import Session

import models
from database import get_db, engine, Base

Base.metadata.create_all(bind=engine)

app=FastAPI()
app.mount("/static",StaticFiles(directory=r"C:\Users\krishna\Desktop\Pyhton\fastapi\static"),name="static")
app.mount("/media",StaticFiles(directory=r"C:\Users\krishna\Desktop\Pyhton\fastapi\media"),name="media")
templates= Jinja2Templates(directory=r"C:\Users\krishna\Desktop\Pyhton\fastapi\templates")

@app.get("/", name="home")
@app.get("/posts", include_in_schema=False, name="post")
def home(request: Request, db: Annotated[Session, Depends(get_db)]):

    result=db.execute(select(models.Post))
    posts=result.scalars().all()
    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "posts": posts
        }
    )


@app.get("/redirect")
def redirect():
    return RedirectResponse(url="/posts")

'''@app.get("/html_test",response_class=HTMLResponse)
def html_test():
    return f"<b>{posts[0]['name']}</b>"'''


@app.get("/post/{post_id}", include_in_schema=False,) 
def post_spec(request: Request, post_id: int, db: Annotated[Session, Depends(get_db)]):

    result=db.execute(select(models.Post).where(models.Post.id==post_id))
    posts=result.scalars().first()

    if posts:
        title=posts.title[:50]
        return templates.TemplateResponse(request,"post.html", {"post":posts, "title":title})
    
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

@app.get("/users/{user_id}/post",name="user_posts", include_in_schema=False)
def user_post_pg(request: Request, user_id:int, db: Annotated[Session, Depends(get_db)]):

    result=db.execute(select(models.User).where(models.User.id==user_id))
    user=result.scalars().first()

    if not user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Oops!.. User Id not found")
    
    result=db.execute(select(models.Post).where(models.Post.user_id==user_id))
    posts=result.scalars().all()

    return templates.TemplateResponse(request,"user_post.html", {"posts":posts, "title":f"{user.user_name}'s posts"})


@app.post("/api/users/create",response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Annotated[Session, Depends(get_db)]):

    result= db.execute(select(models.User).where(models.User.user_name==user.user_name))
    existing_user=result.scalars().first()

    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")
    
    result= db.execute(select(models.User).where(models.User.email==user.email))
    existing_email=result.scalars().first()

    if existing_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    new_user=models.User(user_name=user.user_name, email=user.email)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

@app.get("/api/users/{user_id}") 
def get_user(user_id: int, db: Annotated[Session, Depends(get_db)]):

    result= db.execute(select(models.User).where(models.User.id==user_id))
    user=result.scalars().first()

    if user:
        return user
    
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

@app.get("/api/posts/{user_id}", response_model=PostResponse) #{post_id} it is a parameter fo rdynamic routing to get specific user result
def get_user_post(user_id: int, db: Annotated[Session, Depends(get_db)]):

    result= db.execute(select(models.User).where(models.User.id==user_id))
    user=result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    post=db.execute(select(models.Post).where(models.Post.user_id==user_id))
    posts=post.scalars().first()
    
    return posts

@app.post("/api/post/create",response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def create_post(post: PostCreate, db: Annotated[Session, Depends(get_db)]):
   
   result= db.execute(select(models.User).where(models.User.id==post.user_id))
   user=result.scalars().first()
   
   if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
   
   new_post=models.Post(title=post.title, content=post.content, user_id=post.user_id)

   db.add(new_post)
   db.commit()
   db.refresh(new_post)
   return new_post

@app.get("/api/post", response_model=list[PostResponse])
def get_posts(db: Annotated[Session, Depends(get_db)]):
    
    result=db.execute(select(models.Post))
    posts=result.scalars().all()
    return posts


@app.exception_handler(star_http_exp)# exception for general request
def general_http_exception(request: Request, exception: star_http_exp):
    message=(
        exception.detail
        if exception.detail
        else "An error occured"
    )

    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=exception.status_code,
            content={"Error": message}
        )
    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code":exception.status_code,
            "title":exception.status_code,
            "message":message
        },
        status_code=exception.status_code
    )

@app.exception_handler(RequestValidationError) # exception for invalid request
def req_validation_error(request: Request, exception: RequestValidationError):
    if request.url.path.startswith("/api"):
         return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"Details": exception.errors()}
        )
    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code":status.HTTP_422_UNPROCESSABLE_CONTENT,
            "title":status.HTTP_422_UNPROCESSABLE_CONTENT,
            "message":"Invalid request"
        },
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT
    )