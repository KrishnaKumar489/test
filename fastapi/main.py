from fastapi import FastAPI, Request, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

app=FastAPI()
app.mount("/static",StaticFiles(directory=r"C:\Users\krishna\Desktop\Pyhton\fastapi\static"),name="static")
templates= Jinja2Templates(directory=r"C:\Users\krishna\Desktop\Pyhton\fastapi\templates")


posts: list[dict] = [
    {"id": 1, "name": "asdf", "role": "admin"},
    {"id": 2, "name": "qwer", "role": "user"},
    {"id": 3, "name": "zxcv", "role": "moderator"},
]

@app.get("/")
def home():
    return { "MSG":"Hello asdfcv"}

@app.get("/redirect")
def redirect():
    return RedirectResponse(url="/post")

@app.get("/html_test",response_class=HTMLResponse)
def html_test():
    return f"<b>{posts[0]['name']}</b>"

@app.get("/post", include_in_schema=False)
def jinja_test(request: Request):
    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "posts": posts
        }
    )

@app.get("/post/{post_id}", include_in_schema=False) 
def post_spec(request: Request, post_id: int):
    for post in posts:
        if post_id == post["id"]:
            return templates.TemplateResponse(
                "post.html",
                {
                    "request": request,
                    "post": post
                }
            )
        
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

@app.get("/api/post")
def get_posts():
    return posts

@app.get("/api/post/{post_id}") #{post_id} it is a parameter fo rdynamic routing to get specific user result
def get_spec(post_id: int):
    for i in posts:
        if post_id == i["id"]:
            return i
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")